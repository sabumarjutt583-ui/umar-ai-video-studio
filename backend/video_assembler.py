"""
Video Assembly Module — FFmpeg se asli video banata hai.

Workflow:
1. Har segment ki media (image ya video) ko download/copy karke local file banana
2. Image ho to zoom/pan effect ke sath ek clip banana (uski assigned duration ki)
3. Video clip ho to trim/loop karke duration match karna
4. Sab clips ko order mein jodkar (concatenate) ek video banana
5. Us video ko voice audio ke sath combine karna
"""

import subprocess
import os
import shutil
import threading
import time
import uuid
import math
import requests


class RenderCancelled(Exception):
    """User ne render beech mein cancel kar diya."""
    pass


# Har render thread ka apna cancel-event — isse chalti hui FFmpeg process
# turant kill ho jati hai (pehle cancel ka koi tareeka hi nahi tha)
_thread_cancel = {}


def set_cancel_event(event):
    _thread_cancel[threading.get_ident()] = event


def clear_cancel_event():
    _thread_cancel.pop(threading.get_ident(), None)


def _cancelled() -> bool:
    event = _thread_cancel.get(threading.get_ident())
    return bool(event is not None and event.is_set())


def check_cancel():
    if _cancelled():
        raise RenderCancelled("Render cancel kar diya gaya.")

# Standard vertical video resolution (YouTube Shorts / Reels ke liye) — DEFAULT
WIDTH = 1080
HEIGHT = 1920
FPS = 30

# Aspect Ratio + Resolution Tier -> (width, height)
# Har platform ka apna standard ratio, aur har ratio ke 3 quality tiers
RESOLUTION_TABLE = {
    "9:16": {"4k": (2160, 3840), "1080p": (1080, 1920), "720p": (720, 1280)},
    "16:9": {"4k": (3840, 2160), "1080p": (1920, 1080), "720p": (1280, 720)},
    "1:1":  {"4k": (2160, 2160), "1080p": (1080, 1080), "720p": (720, 720)},
}


def get_dimensions(aspect_ratio: str = "9:16", resolution: str = "1080p"):
    """Aspect ratio + resolution tier se (width, height) deta hai. Fallback: 1080x1920."""
    tier = RESOLUTION_TABLE.get(aspect_ratio, RESOLUTION_TABLE["9:16"])
    return tier.get(resolution, tier["1080p"])

# Agar video zaroorat se bohot chhoti hai, itni slow nahi karenge ke ajeeb
# lage (jaise 10x slow-motion) — is limit ke baad repeat se cover karenge
MAX_SLOWDOWN = 2.5

# Slow karne ke baad bhi kam pade to video ko max itni baar DOBARA chalate hain
# (yani total MAX_VIDEO_REPEATS+1 plays). Is se aage ki duration video ke
# aakhiri frame ki image (zoom ke sath) se poori hoti hai — freeze nahi.
MAX_VIDEO_REPEATS = 2

# Preset -> FFmpeg zoompan filter parameters
ZOOM_PRESETS = {
    "zoom_in_slow": {"start_zoom": 1.0, "end_zoom": 1.15},
    "zoom_in_fast": {"start_zoom": 1.0, "end_zoom": 1.3},
    "zoom_out_slow": {"start_zoom": 1.15, "end_zoom": 1.0},
    "zoom_out_fast": {"start_zoom": 1.3, "end_zoom": 1.0},
    "static": {"start_zoom": 1.0, "end_zoom": 1.0},
}
PAN_PRESETS = {"pan_left_right", "pan_right_left"}

# Auto mode mein IMAGES ke liye inhi effects mein se rotate karke variety milegi
AUTO_ROTATE_EFFECTS = [
    "zoom_in_slow", "pan_left_right", "zoom_out_slow",
    "pan_right_left", "zoom_in_fast", "static"
]


def run_ffmpeg(cmd: list, cwd: str = None):
    """
    FFmpeg command chalata hai. Popen use karte hain (subprocess.run nahi) taake
    beech mein cancel hone par chalti hui process ko turant kill kar saken.

    cwd: agar diya ho, process isi folder se chalti hai (taake 'cmd' mein
    relative/chhote filenames use ho sakein — lambi paths se command-line
    length limit (Windows WinError 206) na tootay).
    """
    check_cancel()
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
        cwd=cwd,
    )
    while True:
        try:
            _out, err = process.communicate(timeout=0.5)
            break
        except subprocess.TimeoutExpired:
            if _cancelled():
                process.kill()
                try:
                    process.communicate(timeout=5)
                except Exception:
                    pass
                raise RenderCancelled("Render cancel kar diya gaya.")

    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {(err or '')[-2000:]}")
    return err or ""


def probe_duration(path: str, fallback: float = 0.0) -> float:
    """Kisi media file ki duration (seconds). Fail ho to fallback."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float((result.stdout or "").strip())
    except (ValueError, AttributeError):
        return fallback


def norm_suffix(fps: int = None) -> str:
    """
    Har clip ka frame-rate aur pixel-aspect-ratio EK JAISA karna zaroori hai,
    warna concat/xfade par timing bigadti hai ya stream copy fail hota hai.
    (Pehle sirf kuch branches mein fps set hota tha — ye bug tha.)
    """
    return f"fps={fps or FPS},setsar=1"


def download_media(url: str, dest_path: str):
    """Stock media (Pexels/Pixabay/Unsplash) ka URL se file download karta hai."""
    res = requests.get(url, timeout=30, stream=True)
    res.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)


def create_image_clip(image_path: str, duration: float, effect: str, output_path: str, add_silent_audio: bool = False,
                       width: int = WIDTH, height: int = HEIGHT):
    """
    Ek image se zoom/pan effect wala video clip banata hai (given duration ka).
    add_silent_audio: agar video_audio_mode 'keep' hai to images ko bhi ek
    KHAMOSH audio-track deni zaroori hai — taake concat karte waqt saari
    clips (video + image) ka audio-stream structure consistent rahe.
    """
    total_frames = max(int(duration * FPS), 1)

    if effect in PAN_PRESETS:
        # Pan effect: image ko thoda bada rakh kar left-right ya right-left move karte hain
        if effect == "pan_left_right":
            x_expr = f"(iw-iw/1.2)*(on/{total_frames})"
        else:
            x_expr = f"(iw-iw/1.2)*(1-on/{total_frames})"
        vf = (
            f"scale=-2:{int(height*1.2)},"
            f"zoompan=z='1.2':x='{x_expr}':y='(ih-ih/1.2)/2':d={total_frames}:s={width}x{height}:fps={FPS},"
            f"{norm_suffix()}"
        )
    else:
        preset = ZOOM_PRESETS.get(effect, ZOOM_PRESETS["static"])
        start_z, end_z = preset["start_zoom"], preset["end_zoom"]
        zoom_expr = f"{start_z}+({end_z}-{start_z})*(on/{total_frames})"
        vf = (
            f"scale=8000:-1,"
            f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={width}x{height}:fps={FPS},{norm_suffix()}"
        )

    if add_silent_audio:
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path,
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-vf", vf, "-t", str(duration),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "44100", "-ac", "2",
            "-shortest", "-preset", "fast",
            output_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path,
            "-vf", vf, "-t", str(duration),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
            output_path
        ]
    run_ffmpeg(cmd)


def _build_atempo_chain(factor: float) -> str:
    """
    FFmpeg ka 'atempo' filter sirf 0.5x-2.0x range accept karta hai ek baar mein.
    Agar zyada slow/fast karna ho, to chain (jodna) padta hai.
    """
    filters = []
    remaining = factor
    # Bohot slow karna hai (0.5 se kam)
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    # Bohot fast karna hai (2.0 se zyada)
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    filters.append(f"atempo={remaining:.4f}")
    return ",".join(filters)


def _extract_frame(video_path: str, out_image: str, from_end_offset: float = 0.08):
    """
    Video ke AAKHIRI frame ka screenshot nikal kar image bana deta hai.
    (Duration-fit mein jab video repeat karne ke baad bhi length kam reh jaye,
    to isi image ko zoom/pan ke sath aage chalate hain — freeze jaisa nahi lagta
    aur video kahin ruki hui mehsoos nahi hoti.)
    """
    cmd = ["ffmpeg", "-y", "-sseof", f"-{from_end_offset}", "-i", video_path,
           "-frames:v", "1", "-q:v", "2", out_image]
    try:
        run_ffmpeg(cmd)
    except Exception:
        pass
    if not os.path.exists(out_image) or os.path.getsize(out_image) == 0:
        # Fallback: bilkul pehla frame (jab -sseof kaam na kare, jaise kuch webm/gif par)
        run_ffmpeg(["ffmpeg", "-y", "-i", video_path, "-frames:v", "1", "-q:v", "2", out_image])


def _concat_parts(parts: list, output_path: str, work_dir: str, keep_audio: bool):
    """Duration-fit ke andar bane hisson (video part + image part) ko jodta hai."""
    list_file = os.path.join(work_dir, f"fit_list_{uuid.uuid4().hex[:6]}.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for path in parts:
            escaped = os.path.abspath(path).replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
           "-vf", norm_suffix(), "-r", str(FPS),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast"]
    if keep_audio:
        cmd += ["-c:a", "aac", "-ar", "44100", "-ac", "2"]
    else:
        cmd += ["-an"]
    cmd.append(output_path)
    run_ffmpeg(cmd)
    try:
        os.remove(list_file)
    except OSError:
        pass


def create_video_clip(video_path: str, duration: float, output_path: str, work_dir: str = None,
                       audio_mode: str = "mute", audio_volume: float = 0.4,
                       width: int = WIDTH, height: int = HEIGHT, trim_mode: str = "end"):
    """
    Ek video clip ko given duration tak fit karta hai:

    1. Video LAMBI hai to: default par END se cut hoti hai — yani shuru wala
       hissa rakha jata hai aur aakhir ka extra kaat diya jata hai.
       (trim_mode: "end" = aakhir se cut [default], "start" = shuru se cut
        [aakhir wala hissa rakha jayega], "middle" = beech ka hissa rakho.)
    2. Video THODI chhoti hai to: speed smoothly SLOW (MAX_SLOWDOWN tak) —
       jhatka nahi lagta, exact duration tak stretch ho jati hai.
    3. Video BOHOT chhoti hai to (kabhi freeze nahi karte):
       a) pehle MAX_SLOWDOWN tak slow,
       b) phir wahi slowed clip max MAX_VIDEO_REPEATS baar REPEAT,
       c) agar phir bhi length kam rahe to video ke aakhiri frame ka SCREENSHOT
          le kar image banate hain aur bachi hui duration us image se zoom/pan
          ke sath poori karte hain.
       Is tarah video kahin pause/ruki hui nahi lagti.

    audio_mode: "mute" (video ki apni awaaz bilkul off, DEFAULT — background
    music/voice ke sath clash nahi hoti) ya "keep" (video ki apni awaaz rakhi
    jati hai, halki volume par, aur agar video slow ki gayi ho to awaaz bhi
    usi hisaab se automatically slow ho jati hai — taake sync bana rahe).
    """
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True
    )
    try:
        src_duration = float(probe.stdout.strip())
    except ValueError:
        src_duration = duration

    keep_audio = audio_mode == "keep"
    vf_base = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"

    if src_duration >= duration:
        # Video lambi hai — kahan se cut karna hai
        extra = max(src_duration - duration, 0)
        if trim_mode == "start":
            start_point = extra          # aakhir wala hissa rakho
        elif trim_mode == "middle":
            start_point = extra / 2.0    # beech ka hissa rakho
        else:
            start_point = 0.0            # DEFAULT: end se cut, shuru rakho
        # BUG FIX: is branch mein pehle fps/SAR normalize nahi hota tha, isliye
        # 60fps ya ajeeb SAR wali clips concat par timing bigad deti thin
        cmd = [
            "ffmpeg", "-y", "-ss", str(round(start_point, 3)), "-i", video_path, "-t", str(duration),
            "-vf", f"{vf_base},{norm_suffix()}", "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
        ]
        if keep_audio:
            cmd += ["-af", f"volume={audio_volume},aresample=44100", "-c:a", "aac", "-ar", "44100", "-ac", "2"]
        else:
            cmd += ["-an"]
        cmd.append(output_path)
        run_ffmpeg(cmd)
        return

    # Video CHHOTI hai — kitna slow karna padega, calculate karte hain
    ratio = duration / src_duration if src_duration > 0 else 1.0

    if ratio <= MAX_SLOWDOWN:
        # Poori video ek hi baar mein, smoothly slow karke exact duration tak stretch
        vf = f"{vf_base},setpts={ratio}*PTS,{norm_suffix()}"
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", vf, "-t", str(duration), "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
        ]
        if keep_audio:
            audio_tempo = _build_atempo_chain(1.0 / ratio)  # video slow ho rahi hai, audio bhi slow ho
            cmd += ["-af", f"{audio_tempo},volume={audio_volume},aresample=44100",
                    "-c:a", "aac", "-ar", "44100", "-ac", "2"]
        else:
            cmd += ["-an"]
        cmd.append(output_path)
        run_ffmpeg(cmd)
    else:
        # Bohot chhoti hai — pehle MAX_SLOWDOWN tak slow, phir max 2 repeat,
        # aur agar phir bhi kam pade to aakhiri frame ki image se baqi duration.
        work_dir = work_dir or os.path.dirname(output_path)
        uid = uuid.uuid4().hex[:6]
        slowed_path = os.path.join(work_dir, f"slowed_{uid}.mp4")

        vf_slow = f"{vf_base},setpts={MAX_SLOWDOWN}*PTS,{norm_suffix()}"
        cmd_slow = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", vf_slow, "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
        ]
        if keep_audio:
            audio_tempo = _build_atempo_chain(1.0 / MAX_SLOWDOWN)
            cmd_slow += ["-af", f"{audio_tempo},volume={audio_volume},aresample=44100",
                         "-c:a", "aac", "-ar", "44100", "-ac", "2"]
        else:
            cmd_slow += ["-an"]
        cmd_slow.append(slowed_path)
        run_ffmpeg(cmd_slow)

        slowed_duration = src_duration * MAX_SLOWDOWN

        # Video ko max MAX_VIDEO_REPEATS baar dobara chalate hain (yani total
        # MAX_VIDEO_REPEATS+1 plays), is se zyada repeat ajeeb lagta hai.
        plays_needed = max(int(math.ceil(duration / slowed_duration)), 1)
        plays = min(plays_needed, MAX_VIDEO_REPEATS + 1)
        video_covers = min(slowed_duration * plays, duration)
        needs_image_fill = video_covers + 0.08 < duration

        video_part = output_path if not needs_image_fill else os.path.join(work_dir, f"fitvid_{uid}.mp4")
        cmd_loop = [
            "ffmpeg", "-y", "-stream_loop", str(plays - 1), "-i", slowed_path,
            "-t", str(round(video_covers, 3)), "-vf", norm_suffix(), "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
        ]
        if keep_audio:
            cmd_loop += ["-c:a", "aac", "-ar", "44100", "-ac", "2"]
        else:
            cmd_loop += ["-an"]
        cmd_loop.append(video_part)
        run_ffmpeg(cmd_loop)

        temp_files = [slowed_path]
        if needs_image_fill:
            # Aakhiri frame ka screenshot -> image clip (zoom ke sath, taake
            # tasveer jami hui / freeze na lage) -> dono ko jod dete hain
            remaining = round(duration - video_covers, 3)
            frame_path = os.path.join(work_dir, f"fitframe_{uid}.jpg")
            image_part = os.path.join(work_dir, f"fitimg_{uid}.mp4")
            _extract_frame(slowed_path, frame_path)
            create_image_clip(frame_path, remaining, "zoom_in", image_part,
                              add_silent_audio=keep_audio, width=width, height=height)
            _concat_parts([video_part, image_part], output_path, work_dir, keep_audio)
            temp_files += [video_part, frame_path, image_part]

        # Temp files saaf kar dete hain
        for path in temp_files:
            try:
                os.remove(path)
            except OSError:
                pass


def concatenate_clips(clip_paths: list, output_path: str, work_dir: str):
    """
    Saare video clips ko order mein jodta hai — 'cut' style, koi transition nahi.
    Pehle fast stream-copy try karte hain; agar clips ke parameters bilkul match
    na hon (copy fail ho jaye) to safe re-encode fallback chalta hai.
    """
    list_file = os.path.join(work_dir, "concat_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for path in clip_paths:
            escaped = os.path.abspath(path).replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")

    base = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file]
    try:
        run_ffmpeg(base + ["-c", "copy", output_path])
    except RenderCancelled:
        raise
    except RuntimeError:
        run_ffmpeg(base + [
            "-vf", norm_suffix(), "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
            "-c:a", "aac", "-ar", "44100", "-ac", "2",
            output_path
        ])


def concatenate_clips_with_xfade(clip_paths: list, output_path: str, xfade_names, transition_duration: float,
                                  with_audio: bool = False, work_dir: str = None):
    """
    Clips ko FFmpeg 'xfade' filter se jodta hai — REAL crossfade/wipe/slide transition
    (do clips ka content ek dusre mein blend hota hai, sirf fade-to-black nahi).

    xfade_names: ek single string (sab boundaries pe wahi transition) YA ek list
    (har boundary ke liye alag transition — "Auto" mode ke liye variety).

    with_audio: agar clips ki apni audio rakhi ja rahi hai (video_audio_mode='keep')
    to audio ko bhi 'acrossfade' se jodte hain. BUG FIX: pehle xfade sirf video
    map karta tha, isliye 'keep' mode mein clips ki awaaz poori tarah gayab ho jati thi.

    ZAROORI: Is function ko call karne se PEHLE, clips already is tarah render honi
    chahiye ke pehli clip ko chhod kar, baaki sab clips apni assigned duration se
    'transition_duration' SECONDS ZYADA LAMBI ho (taake overlap consume hone ke
    baad bhi total video ki length bilkul sahi rahe, voice-sync na toote).
    """
    n = len(clip_paths)
    if n < 2:
        raise ValueError("Xfade ke liye kam se kam 2 clips chahiye.")

    if isinstance(xfade_names, str):
        xfade_names = [xfade_names] * (n - 1)

    D = transition_duration

    durations = [probe_duration(path, 1.0) for path in clip_paths]

    if with_audio:
        with_audio = all(video_has_audio_stream(p) for p in clip_paths)

    # ZAROORI (WinError 206 fix): Bohot saare clips (100+) hone par, agar hum
    # har clip ki FULL absolute path command-line mein daalein, to total
    # command-line length Windows ki limit (~32,767 chars) cross ho sakti hai
    # aur CreateProcess "[WinError 206] filename or extension is too long"
    # de kar fail ho jata hai.
    #
    # Fix: FFmpeg ko clips ke work_dir se hi chalate hain (cwd=work_dir) aur
    # sirf chhote RELATIVE filenames (basename) command mein dete hain, poori
    # absolute path nahi — isse command line kaafi chhoti ho jati hai chahe
    # kitne bhi clips hon.
    work_dir = work_dir or os.path.dirname(output_path) or "."

    inputs = []
    for path in clip_paths:
        inputs.extend(["-i", os.path.basename(path)])

    filter_parts = []
    running_duration = durations[0]
    prev_label = "0:v"
    prev_audio = "0:a"

    for i in range(1, n):
        offset = max(running_duration - D, 0)
        out_label = f"v{i}" if i < n - 1 else "vout"
        this_transition = xfade_names[i - 1]
        filter_parts.append(
            f"[{prev_label}][{i}:v]xfade=transition={this_transition}:duration={D}:offset={offset}[{out_label}]"
        )
        if with_audio:
            a_label = f"a{i}" if i < n - 1 else "aout"
            filter_parts.append(
                f"[{prev_audio}][{i}:a]acrossfade=d={D}:c1=tri:c2=tri[{a_label}]"
            )
            prev_audio = a_label
        running_duration = running_duration + durations[i] - D
        prev_label = out_label

    filter_complex = ";".join(filter_parts)

    output_name = os.path.basename(output_path)

    # NOTE: -filter_complex_script option kuch Windows FFmpeg "essentials"
    # builds mein maujood nahi hota ("Unrecognized option" error deta hai),
    # isliye filter_complex ko wapis inline argument ke taur par pass karte
    # hain. Ye ab bhi SAFE hai kyunke humne clips ke FULL paths hata kar
    # chhote RELATIVE filenames (cwd=work_dir ke sath) kar diye hain — isse
    # total command-line length Windows ki ~32,767 char limit se kaafi kam
    # rehti hai, chahe 150+ clips hi kyun na hon.
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
    ]
    if with_audio:
        cmd += ["-map", "[aout]", "-c:a", "aac", "-ar", "44100", "-ac", "2"]
    cmd += [
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
        output_name
    ]
    run_ffmpeg(cmd, cwd=work_dir)


def add_voice_audio(video_path: str, voice_path: str, output_path: str):
    """Video (bina audio wali) ko voice audio ke sath jodta hai."""
    cmd = [
        "ffmpeg", "-y", "-i", video_path, "-i", voice_path,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest", output_path
    ]
    run_ffmpeg(cmd)


def mix_video_audio_with_voice(video_with_audio_path: str, voice_path: str, output_path: str):
    """
    Jab video clips ki apni audio 'keep' ki gayi ho (mute nahi), to use
    voice ke sath MIX karta hai (discard nahi karta) — dono awazein ek sath
    sunayi denge.

    BUG FIX: amix default mein har input ka volume inputs ki ginti se DIVIDE
    kar deta hai — isliye voice aadhi halki ho jati thi. 'normalize=0' se
    har input apna asli volume rakhta hai.
    """
    cmd = [
        "ffmpeg", "-y", "-i", video_with_audio_path, "-i", voice_path,
        "-filter_complex",
        "[0:a]aresample=44100[bg];[1:a]aresample=44100[vo];"
        "[bg][vo]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0,"
        "alimiter=limit=0.97[aout]",
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        output_path
    ]
    run_ffmpeg(cmd)


def video_has_audio_stream(video_path: str) -> bool:
    """Check karta hai ke video file mein audio stream hai ya nahi."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", video_path],
        capture_output=True, text=True
    )
    return bool(result.stdout.strip())


def add_background_music(video_with_voice_path: str, music_path: str, output_path: str, music_volume: float = 0.2,
                          audio_ducking: bool = False, fade_in_out: bool = True, fade_duration: float = 1.5):
    """
    Video (jisme voice already hai) mein background music mix karta hai.
    - Agar music video se chhoti hai: loop karke pura duration cover karti hai
    - Agar music lambi hai: video ki length tak automatically trim ho jati hai
    - Music ka volume 'music_volume' (0.0-1.0) ke hisaab se kam kiya jata hai

    audio_ducking: agar True hai, to jab bhi VOICE bol rahi ho, music
    automatically aur bhi halki ho jati hai (sidechain compression — professional
    editing software jaisa), aur khamoshi ke waqt wapas normal volume par aa jati hai.

    fade_in_out: agar True hai, to music video ke shuru mein dheere se aati hai
    aur aakhir mein dheere se khatam hoti hai (achanak cut nahi hoti).
    """
    video_duration = probe_duration(video_with_voice_path, 1.0)

    filter_parts = [f"[1:a]aresample=44100,volume={music_volume}[music_vol]"]
    music_label = "music_vol"

    if audio_ducking:
        # [0:a] (voice) ko 'sidechain key' ki tarah use karte hain — jab voice
        # bolti hai, music automatically aur dab jati hai
        filter_parts.append(
            f"[{music_label}][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300:makeup=1[music_ducked]"
        )
        music_label = "music_ducked"

    if fade_in_out:
        fade_out_start = max(video_duration - fade_duration, 0)
        filter_parts.append(
            f"[{music_label}]afade=t=in:st=0:d={fade_duration},afade=t=out:st={fade_out_start}:d={fade_duration}[music_final]"
        )
        music_label = "music_final"

    # BUG FIX: normalize=0 — warna voice ka volume aadha ho jata tha
    filter_parts.append(
        f"[0:a][{music_label}]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,"
        f"alimiter=limit=0.97[aout]"
    )
    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_with_voice_path,
        "-stream_loop", "-1", "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-t", str(video_duration),
        output_path
    ]
    run_ffmpeg(cmd)


def apply_sound_effects(video_path: str, output_path: str, sound_effects: list, work_dir: str):
    """
    Video mein multiple sound-effects mix karta hai, har ek apni specific
    'start time' aur volume ke sath.

    sound_effects: [{"sfx_key": "whoosh", "start": 2.5, "volume": 0.8}, ...]
    """
    if not sound_effects:
        return video_path

    from sfx_assets import generate_sfx

    sfx_dir = os.path.join(work_dir, "sfx")
    os.makedirs(sfx_dir, exist_ok=True)

    # Har unique sfx type ek hi baar generate karte hain (cache)
    sfx_cache = {}
    for item in sound_effects:
        key = item["sfx_key"]
        if key not in sfx_cache:
            path = os.path.join(sfx_dir, f"{key}.mp3")
            generate_sfx(key, path, work_dir=sfx_dir)
            sfx_cache[key] = path

    inputs = ["-i", video_path]
    for item in sound_effects:
        inputs.extend(["-i", sfx_cache[item["sfx_key"]]])

    # Har sfx ko uske start-time tak 'delay' karte hain, volume set karte hain,
    # phir sabko original audio ke sath mix (amix) karte hain
    delay_parts = []
    mix_labels = ["0:a"]
    for i, item in enumerate(sound_effects):
        input_idx = i + 1
        start_ms = int(item["start"] * 1000)
        volume = item.get("volume", 0.8)
        label = f"sfx{i}"
        delay_parts.append(
            f"[{input_idx}:a]volume={volume},adelay={start_ms}|{start_ms}[{label}]"
        )
        mix_labels.append(label)

    mix_filter = "".join(f"[{l}]" for l in mix_labels)
    filter_complex = (
        ";".join(delay_parts)
        + f";{mix_filter}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=0:normalize=0,"
          f"alimiter=limit=0.97[aout]"
    )

    video_duration = probe_duration(video_path, 1.0)

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-t", str(video_duration),
        output_path
    ]
    run_ffmpeg(cmd)
    return output_path


def apply_boundary_fades(clip_paths: list, output_dir: str, fade_duration: float = 0.35) -> list:
    """
    Har clip ke start/end pe halka fade-to-black lagata hai (last clip ka end
    aur first clip ka start chhod kar) — taake clips ke darmiyan switch
    "achanak jhatka" na lage, smooth transition jaisa mehsoos ho.

    Ye TOTAL VIDEO DURATION change NAHI karta (voice-sync SAFE rehta hai) —
    kyunke fade khud clip ki apni duration ke andar hi hota hai, koi
    overlap/extra time nahi lagta.
    """
    new_paths = []
    total = len(clip_paths)

    for i, clip_path in enumerate(clip_paths):
        check_cancel()
        clip_duration = probe_duration(clip_path, 0.0)
        if clip_duration <= 0:
            new_paths.append(clip_path)
            continue

        fd = min(fade_duration, clip_duration / 3)  # bohot chhoti clip ho to fade bhi chhota

        filters = []
        if i > 0:  # pehli clip ke shuru mein fade-in nahi chahiye
            filters.append(f"fade=t=in:st=0:d={fd}")
        if i < total - 1:  # aakhri clip ke end mein fade-out nahi chahiye
            filters.append(f"fade=t=out:st={max(clip_duration - fd, 0)}:d={fd}")

        if not filters:
            new_paths.append(clip_path)
            continue

        faded_output = os.path.join(output_dir, f"faded_{i:04d}.mp4")
        filters.append(norm_suffix())
        cmd = [
            "ffmpeg", "-y", "-i", clip_path,
            "-vf", ",".join(filters), "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
            "-c:a", "copy",
            faded_output
        ]
        run_ffmpeg(cmd)
        new_paths.append(faded_output)

    return new_paths


STAGE_ORDER = [
    ("clips", 0.55),
    ("join", 0.09),
    ("filter", 0.04),
    ("captions", 0.10),
    ("overlays", 0.05),
    ("voice", 0.06),
    ("music", 0.05),
    ("sfx", 0.03),
    ("finalize", 0.03),
]


def stage_plan(has_transition=False, has_filter=False, has_captions=False,
               has_overlays=False, has_music=False, has_sfx=False) -> list:
    """Is render mein kaun kaun se stages chalenge — UI checklist isse banti hai."""
    enabled = {
        "clips": True, "join": True, "filter": has_filter, "captions": has_captions,
        "overlays": has_overlays, "voice": True, "music": has_music,
        "sfx": has_sfx, "finalize": True,
    }
    return [{"key": k, "weight": w} for k, w in STAGE_ORDER if enabled.get(k)]


def cleanup_work_dir(work_dir: str, keep_paths: list = None):
    """
    Render ke temp files delete karta hai (final video aur ussey linked files
    chhod kar). Pehle ye kabhi saaf nahi hote the — disk bharti chali jati thi.
    """
    keep = {os.path.abspath(p) for p in (keep_paths or []) if p}
    removed = 0
    if not os.path.isdir(work_dir):
        return 0
    for name in os.listdir(work_dir):
        full = os.path.join(work_dir, name)
        if os.path.abspath(full) in keep:
            continue
        # User ke upload kiye font files (libass inhe fontsdir se uthata hai) aur
        # quick-export outputs delete nahi karte — warna agli render/export toot jati hai.
        lower = name.lower()
        if lower.endswith((".ttf", ".otf", ".ttc")) or lower.startswith("export_"):
            continue
        try:
            if os.path.isdir(full):
                shutil.rmtree(full, ignore_errors=True)
            else:
                os.remove(full)
            removed += 1
        except OSError:
            continue
    return removed


def assemble_video(segments: list, voice_path: str, work_dir: str, default_effect: str = "zoom_in_slow",
                    music_path: str = None, music_volume: float = 0.2, progress_callback=None,
                    transition: str = "cut",  # "cut" | "fade" (safe black-fade) | koi xfade key | "auto_transition"
                    transition_speed: str = "medium",  # "fast" | "medium" | "slow"
                    captions: dict = None,
                    raw_words: list = None,
                    color_filter: str = "none",
                    stickers: list = None,
                    custom_texts: list = None,
                    video_audio_mode: str = "mute",  # "mute" ya "keep"
                    video_audio_volume: float = 0.4,
                    video_trim_mode: str = "end",  # lambi video ka extra hissa kahan se kate: "end" | "start" | "middle"
                    aspect_ratio: str = "9:16",
                    resolution: str = "1080p",
                    sound_effects: list = None,
                    audio_ducking: bool = False,
                    music_fade_in_out: bool = True,
                    cleanup_temp: bool = True) -> str:
    """
    Poora video banane ka main function.
    segments: [{start, end, text, media: {type, full_url ya local_path}, effect (optional)}]
    default_effect: agar "auto" ho, to har IMAGE ke liye AUTO_ROTATE_EFFECTS se
    ek-ek karke effect choose hoga (variety ke liye). VIDEO clips pe kabhi
    zoom/pan effect nahi lagta — wo apni khud ki movement rakhte hain.
    music_path: (optional) background music file ka path.
    transition: "cut" ya "fade" — clips ke darmiyan switch kaisa dikhega.
    captions: caption settings dict — agar enabled hai to video pe burn hoti hain.
    color_filter: video_filters.py ka koi preset naam (jaise "vintage", "black_white").
    progress_callback: function(payload_dict) — payload mein percent, stage,
    stage_index, message, segment_index waghera hota hai (live UI ke liye).
    Returns: final video ka path
    """
    os.makedirs(work_dir, exist_ok=True)
    vid_width, vid_height = get_dimensions(aspect_ratio, resolution)
    clip_paths = []
    image_counter = 0
    total_segments = len(segments)
    started_at = time.time()

    from transitions import get_xfade_name, get_transition_duration, AUTO_ROTATE_TRANSITIONS
    is_xfade_mode = transition not in ("cut", "fade") and total_segments > 1

    has_filter = bool(color_filter and color_filter != "none")
    has_captions = bool(captions and captions.get("enabled"))
    has_overlays = bool(stickers or custom_texts)
    has_music = bool(music_path and os.path.exists(music_path))
    has_sfx = bool(sound_effects)

    plan = stage_plan(is_xfade_mode, has_filter, has_captions, has_overlays, has_music, has_sfx)
    plan_keys = [s["key"] for s in plan]
    total_weight = sum(s["weight"] for s in plan) or 1.0
    done_weight = {"value": 0.0}

    def notify(stage: str, message: str, sub: float = 0.0, segment_index: int = None):
        """
        Staged progress — pehle progress 90% pe atak jata tha kyunke sirf
        segments count hote the. Ab har stage ka apna weight hai.
        """
        check_cancel()
        if stage in plan_keys:
            idx = plan_keys.index(stage)
            base = sum(s["weight"] for s in plan[:idx])
            weight = plan[idx]["weight"]
        else:
            idx, base, weight = 0, done_weight["value"], 0.0
        percent = min(((base + weight * max(0.0, min(sub, 1.0))) / total_weight) * 100.0, 99.5)
        done_weight["value"] = base + weight
        elapsed = time.time() - started_at
        eta = (elapsed / percent * (100 - percent)) if percent > 3 else None
        if progress_callback:
            try:
                progress_callback({
                    "percent": round(percent, 1),
                    "stage": stage,
                    "stage_index": idx,
                    "stage_total": len(plan),
                    "stages": plan_keys,
                    "message": message,
                    "segment_index": segment_index,
                    "total_segments": total_segments,
                    "elapsed": round(elapsed, 1),
                    "eta": round(eta, 1) if eta else None,
                })
            except Exception:
                pass

    # Safety feature: Agar voice length timeline se lambi ho ya speech gaps hon:
    # to gaps ko close karte hain aur aakhiri segment ko automatically voice ke end tak extend kar dete hain,
    # taake FFmpeg add_voice_audio (-shortest) par voice aakhir se cut na ho aur video-audio drift na aaye!
    if voice_path and os.path.exists(voice_path) and segments:
        voice_dur = probe_duration(voice_path, 0.0)
        timeline_dur = sum(max(float(s.get("end", 0)) - float(s.get("start", 0)), 0.0) for s in segments)
        if voice_dur > timeline_dur + 0.3 or voice_dur > float(segments[-1].get("end", 0.0)) + 0.3:
            if float(segments[0].get("start", 0)) > 0:
                segments[0]["start"] = 0.0
            for idx in range(len(segments) - 1):
                nxt_start = float(segments[idx + 1].get("start", 0))
                curr_end = float(segments[idx].get("end", 0))
                if nxt_start > curr_end:
                    segments[idx]["end"] = round(nxt_start, 2)
            segments[-1]["end"] = round(voice_dur, 2)

    xfade_duration = 0.0
    if is_xfade_mode:
        xfade_duration = get_transition_duration(transition_speed)
        # Safety clamp — bohot chhoti clips ke sath negative offset na bane
        original_durations = [seg["end"] - seg["start"] for seg in segments]
        safe_max = min(original_durations) * 0.5
        xfade_duration = min(xfade_duration, safe_max) if safe_max > 0 else 0.3
        if xfade_duration < 0.1:
            xfade_duration = 0.1  # bohot chhota transition bhi na ho, ffmpeg fail kar sakta hai

    for i, seg in enumerate(segments):
        check_cancel()
        duration = seg["end"] - seg["start"]
        media = seg.get("media", {})
        effect = seg.get("effect") or default_effect

        notify("clips", f"Segment {i + 1}/{total_segments} process ho raha hai...",
               sub=i / max(total_segments, 1), segment_index=i)

        # Xfade mode mein pehli clip chhod kar, baaki sabko thoda LAMBA banate hain
        # (transition_duration jitna extra) — taake overlap consume hone ke baad
        # bhi total video length bilkul sahi rahe (voice-sync safe)
        render_duration = duration
        if is_xfade_mode and i > 0:
            render_duration = duration + xfade_duration

        clip_output = os.path.join(work_dir, f"clip_{i:04d}.mp4")
        need_silent_audio = (video_audio_mode == "keep")  # taake concat mein audio-stream consistency rahe

        if not media or media.get("error"):
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={vid_width}x{vid_height}:d={render_duration}",
            ]
            if need_silent_audio:
                cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest"]
            else:
                cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
            cmd.append(clip_output)
            run_ffmpeg(cmd)
        elif media.get("type") == "video":
            local_video = os.path.join(work_dir, f"raw_{i:04d}.mp4")
            source = media.get("full_url") or media.get("local_path") or ""
            if source.startswith("http"):
                download_media(source, local_video)
            else:
                local_video = source
            create_video_clip(local_video, render_duration, clip_output, work_dir=work_dir,
                               audio_mode=video_audio_mode, audio_volume=video_audio_volume,
                               width=vid_width, height=vid_height, trim_mode=video_trim_mode)
        else:
            actual_effect = effect
            if effect == "auto":
                actual_effect = AUTO_ROTATE_EFFECTS[image_counter % len(AUTO_ROTATE_EFFECTS)]
                image_counter += 1

            local_image = os.path.join(work_dir, f"raw_{i:04d}.jpg")
            source = media.get("full_url") or media.get("local_path") or ""
            if source.startswith("http"):
                download_media(source, local_image)
            else:
                local_image = source
            create_image_clip(local_image, render_duration, actual_effect, clip_output, add_silent_audio=need_silent_audio,
                               width=vid_width, height=vid_height)

        clip_paths.append(clip_output)

    silent_video = os.path.join(work_dir, "silent_final.mp4")

    if is_xfade_mode:
        notify("join", "Transitions laga rahe hain...", sub=0.2)
        if transition == "auto_transition":
            xfade_names = [
                get_xfade_name(AUTO_ROTATE_TRANSITIONS[k % len(AUTO_ROTATE_TRANSITIONS)])
                for k in range(len(clip_paths) - 1)
            ]
        else:
            xfade_names = [get_xfade_name(transition)] * (len(clip_paths) - 1)
        concatenate_clips_with_xfade(clip_paths, silent_video, xfade_names, xfade_duration,
                                     with_audio=(video_audio_mode == "keep"), work_dir=work_dir)
    else:
        if transition == "fade":
            notify("join", "Transitions laga rahe hain...", sub=0.2)
            clip_paths = apply_boundary_fades(clip_paths, work_dir)
        notify("join", "Saare clips ko jod rahe hain...", sub=0.6)
        concatenate_clips(clip_paths, silent_video, work_dir)

    current_video = silent_video

    # Color filter (agar select kiya ho) — captions se PEHLE lagate hain,
    # taake caption text ka color/contrast filter se disturb na ho
    if has_filter:
        from video_filters import get_filter_string
        filter_str = get_filter_string(color_filter)
        if filter_str:
            notify("filter", "Color filter apply ho raha hai...", sub=0.3)
            filtered_video = os.path.join(work_dir, "filtered.mp4")
            cmd = [
                "ffmpeg", "-y", "-i", current_video,
                "-vf", f"{filter_str},{norm_suffix()}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                "-c:a", "copy",
                filtered_video
            ]
            run_ffmpeg(cmd)
            current_video = filtered_video

    # Captions (agar enabled hain) — video ko voice add karne se PEHLE burn karte
    # hain (subtitles filter sirf video stream pe kaam karta hai)
    if has_captions:
        notify("captions", "Captions add ho rahi hain...", sub=0.2)
        from caption_generator import build_ass_file, get_burn_filter

        ass_path = os.path.join(work_dir, "captions.ass")
        mode = captions.get("mode", "line")
        info = build_ass_file(
            segments=segments,
            output_path=ass_path,
            mode=mode,
            font=captions.get("font", "clean"),
            font_size=captions.get("font_size", 64),
            color=captions.get("color", "#FFFFFF"),
            position=captions.get("position", "bottom"),
            outline=captions.get("outline", True),
            background_box=captions.get("background_box", False),
            raw_words=raw_words if mode in ("word", "karaoke") else None,
            video_width=vid_width,
            video_height=vid_height,
            custom_font_name=captions.get("custom_font_name"),
            language_mode=captions.get("language_mode", "default"),
            highlight_color=captions.get("highlight_color", "#FFD166"),
            animation=captions.get("animation", "none"),
            bold=captions.get("bold", True),
            all_caps=captions.get("all_caps", False),
            margin_v=captions.get("margin_v", 80),
            max_chars_per_line=captions.get("max_chars_per_line"),
        )

        event_count = info.get("events", 0) if isinstance(info, dict) else 0
        if event_count > 0:
            captioned_video = os.path.join(work_dir, "captioned.mp4")
            burn_filter = get_burn_filter(ass_path)
            cmd = [
                "ffmpeg", "-y", "-i", current_video,
                "-vf", burn_filter,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                "-c:a", "copy",
                captioned_video
            ]
            run_ffmpeg(cmd)
            current_video = captioned_video
            notify("captions", f"Captions burn ho gayi hain ({event_count} lines, font: {info.get('font_name')})", sub=1.0)
        else:
            notify("captions", "⚠️ Captions ON thi magar kisi segment mein text nahi mila — captions skip kar di gayi.", sub=1.0)

    # Stickers + Custom Text Overlays (voice add hone se PEHLE — video-only step)
    if has_overlays:
        notify("overlays", "Stickers/Text overlays add ho rahi hain...", sub=0.3)
        from overlays import apply_overlays
        overlayed_video = os.path.join(work_dir, "overlayed.mp4")
        apply_overlays(current_video, overlayed_video, stickers or [], custom_texts or [], work_dir,
                       video_width=vid_width, video_height=vid_height)
        current_video = overlayed_video

    notify("voice", "Voice audio sync ho raha hai...", sub=0.3)
    video_with_voice = os.path.join(work_dir, "with_voice.mp4")
    if video_audio_mode == "keep" and video_has_audio_stream(current_video):
        mix_video_audio_with_voice(current_video, voice_path, video_with_voice)
    else:
        add_voice_audio(current_video, voice_path, video_with_voice)

    audio_stage_output = video_with_voice

    if has_music:
        notify("music", "Background music mix ho rahi hai...", sub=0.3)
        with_music = os.path.join(work_dir, "final_with_music.mp4")
        add_background_music(audio_stage_output, music_path, with_music, music_volume=music_volume,
                              audio_ducking=audio_ducking, fade_in_out=music_fade_in_out)
        audio_stage_output = with_music

    if has_sfx:
        notify("sfx", "Sound effects mix ho rahe hain...", sub=0.3)
        with_sfx = os.path.join(work_dir, "final_with_sfx.mp4")
        apply_sound_effects(audio_stage_output, with_sfx, sound_effects, work_dir)
        audio_stage_output = with_sfx

    # Final file ko ek saaf naam de dete hain, aur streaming ke liye faststart
    notify("finalize", "Final file taiyar ho rahi hai...", sub=0.4)
    final_output = os.path.join(work_dir, "final_video.mp4")
    if os.path.abspath(audio_stage_output) != os.path.abspath(final_output):
        try:
            run_ffmpeg(["ffmpeg", "-y", "-i", audio_stage_output, "-c", "copy",
                        "-movflags", "+faststart", final_output])
            audio_stage_output = final_output
        except RenderCancelled:
            raise
        except RuntimeError:
            pass

    if cleanup_temp:
        notify("finalize", "Temp files saaf kar rahe hain...", sub=0.8)
        cleanup_work_dir(work_dir, keep_paths=[audio_stage_output, voice_path, music_path])

    notify("finalize", "Mukammal ho gaya! ✅", sub=1.0)
    return audio_stage_output


def quick_export_resolution(existing_video_path: str, output_path: str, aspect_ratio: str, resolution: str,
                            fit_mode: str = "crop"):
    """
    Already-rendered final video ko poori pipeline DOBARA chalaye bina, sirf
    naye resolution/ratio mein convert kar deta hai (fast — render dobara nahi hota).

    fit_mode:
      "crop" -> target frame poora bharta hai, kinare cut ho jate hain
      "pad"  -> poora frame dikhta hai, khali jagah par black bars (kuch bhi cut nahi hota)
    BUG FIX: pehle sirf crop hota tha, isliye 9:16 se 16:9 export mein content
    ka bada hissa kat jata tha aur user ke paas koi option nahi tha.
    """
    target_width, target_height = get_dimensions(aspect_ratio, resolution)
    if fit_mode == "pad":
        vf = (f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
              f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1")
    else:
        vf = (f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
              f"crop={target_width}:{target_height},setsar=1")
    cmd = [
        "ffmpeg", "-y", "-i", existing_video_path,
        "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]
    run_ffmpeg(cmd)
    return output_path
