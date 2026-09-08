"""
AI Video Studio Engine - Phase 1 (Script-to-Video Pipeline)
Automated 100% Free AI Video Generation:
1. Script Breakdown / Scene Director (Rule-based or Gemini Flash)
2. Character Consistency & Visual Prompt Synthesizer
3. 4K Visual Art Generation via Pollinations FLUX.1
4. Neural Voiceover & Word-by-Word Timestamps via Edge-TTS
5. Multi-Scene Ken Burns 3D Motion & Subtitle Assembly via FFmpeg
"""

import os
import re
import json
import time
import uuid
import urllib.parse
import urllib.request
import asyncio
import logging
from typing import Dict, List, Any, Optional

import tts_engine
import video_assembler as va
from video_assembler import assemble_video, get_dimensions

logger = logging.getLogger("ai_video_engine")

# ---------------------------------------------------------------------------
# Art Styles & Cinematic Anchors
# ---------------------------------------------------------------------------
STYLE_PRESETS = {
    "cinematic": {
        "id": "cinematic",
        "name": "Cinematic Photorealism",
        "icon": "🎬",
        "desc": "Ultra-realistic 8K movie cinematography with anamorphic depth",
        "prompt_anchor": "cinematic photograph, photorealistic, 8k resolution, dramatic atmospheric lighting, anamorphic lens flare, shallow depth of field, sharp focus, award winning masterpiece, hyperdetailed",
        "negative": "blurry, low quality, deformed, distorted, watermark, signature, cartoon"
    },
    "pixar": {
        "id": "pixar",
        "name": "3D Pixar Animation",
        "icon": "🧸",
        "desc": "Vibrant 3D Disney & Pixar animated character aesthetics",
        "prompt_anchor": "3D Disney Pixar animation style, vibrant vivid colors, highly expressive character, soft studio rim lighting, subsurface scattering, cute appealing aesthetic, 8k octane render, masterpiece",
        "negative": "ugly, realistic human skin, creepy, dark, grainy, low resolution"
    },
    "anime": {
        "id": "anime",
        "name": "Modern Anime / Manga",
        "icon": "🎨",
        "desc": "Makoto Shinkai style high-budget cinematic anime",
        "prompt_anchor": "modern high-budget cinematic anime, Makoto Shinkai aesthetic, gorgeous atmospheric sky, beautiful vibrant lighting, clean lineart, emotional depth, 4k digital anime art, masterpiece",
        "negative": "photo, live action, low quality, ugly, blurry, deformed face"
    },
    "documentary": {
        "id": "documentary",
        "name": "Historical Documentary",
        "icon": "📜",
        "desc": "Archival historical photograph with authentic vintage mood",
        "prompt_anchor": "historical documentary photograph, authentic archival feel, natural cinematic lighting, National Geographic editorial style, rich realistic textures, sharp focus, vintage tone",
        "negative": "modern, futuristic, bright neon, cartoon, 3d, fantasy"
    },
    "luxury": {
        "id": "luxury",
        "name": "Cash Cow Luxury",
        "icon": "💰",
        "desc": "High-end luxury commercial aesthetics & dark moody gold tones",
        "prompt_anchor": "ultra luxury commercial cinematography, sleek dark moody aesthetic, golden hour rim lighting, 8k hyper-detailed, elegant minimalist composition, billionaire lifestyle vibe, ultra premium",
        "negative": "cheap, cluttered, blurry, poor lighting, low resolution, amateur"
    },
    "cyberpunk": {
        "id": "cyberpunk",
        "name": "Cyberpunk Neon",
        "icon": "⚡",
        "desc": "Futuristic neon cityscapes & high-tech atmospheres",
        "prompt_anchor": "cyberpunk futuristic neon aesthetic, glowing neon reflections, rain drenched futuristic city, volumetric lighting, high tech atmosphere, hyperdetailed cinematic night photography",
        "negative": "daylight, medieval, countryside, cartoon, low contrast"
    },
    "fantasy": {
        "id": "fantasy",
        "name": "Epic Fantasy",
        "icon": "🧙",
        "desc": "Mythical fantasy realms with enchanting atmospheric glow",
        "prompt_anchor": "epic high fantasy concept art, mystical glowing ethereal lighting, magical particles, grand scale atmospheric world, highly detailed digital painting, artstation trending",
        "negative": "modern cars, technology, blurry, low resolution, bad anatomy"
    }
}

CAMERA_MOTIONS = [
    "zoom_in_slow",
    "pan_left_right",
    "zoom_out_slow",
    "pan_right_left",
    "zoom_in_fast"
]

# In-memory pipeline job tracker
AI_VIDEO_JOBS: Dict[str, Dict[str, Any]] = {}


def get_ai_video_job(job_id: str) -> Dict[str, Any]:
    return AI_VIDEO_JOBS.get(job_id, {
        "job_id": job_id,
        "percent": 0,
        "stage": "not_found",
        "message": "Job not found",
        "is_done": False,
        "result": None,
        "error": None
    })


def set_ai_video_progress(
    job_id: str,
    percent: int,
    stage: str,
    message: str,
    is_done: bool = False,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
):
    if not job_id:
        return
    current = AI_VIDEO_JOBS.get(job_id, {})
    current.update({
        "job_id": job_id,
        "percent": max(0, min(100, int(percent))),
        "stage": stage,
        "message": message,
        "is_done": is_done,
        "updated_at": time.time()
    })
    if result is not None:
        current["result"] = result
    if error is not None:
        current["error"] = error
    AI_VIDEO_JOBS[job_id] = current


# ---------------------------------------------------------------------------
# 1. Script Breakdown & Scene Director
# ---------------------------------------------------------------------------
def split_script_into_scenes_rule_based(
    script_text: str,
    style_key: str = "cinematic",
    character_desc: str = ""
) -> List[Dict[str, Any]]:
    """
    Intelligently breaks script into 4-6 second visual scenes without cutting sentences.
    Generates rich, contextual visual prompts with character anchor and art style.
    """
    style_info = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cinematic"])
    anchor = style_info["prompt_anchor"]

    clean_text = script_text.strip()
    # Remove bracket emotion tags like [laugh], [sigh], [pause] for scene text
    clean_text = re.sub(r'\[[a-zA-Z0-9_\-\s:]+\]', '', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    # Split by paragraphs or sentence delimiters (. ! ? Urdu: ۔ ؟)
    sentences = [s.strip() for s in re.split(r'([.?!۔؟\n]+)', clean_text) if s.strip()]
    merged_sentences = []
    i = 0
    while i < len(sentences):
        s = sentences[i]
        if i + 1 < len(sentences) and re.match(r'^[.?!۔؟\n]+$', sentences[i+1]):
            s += sentences[i+1]
            i += 2
        else:
            i += 1
        if len(s.strip()) > 3:
            merged_sentences.append(s.strip())

    if not merged_sentences:
        merged_sentences = [clean_text or "A scenic journey begins."]

    # Group short sentences into ~15-30 words per scene
    scene_texts = []
    current_group = []
    current_word_count = 0

    for s in merged_sentences:
        w_count = len(s.split())
        if current_word_count + w_count > 25 and current_group:
            scene_texts.append(" ".join(current_group))
            current_group = [s]
            current_word_count = w_count
        else:
            current_group.append(s)
            current_word_count += w_count

    if current_group:
        scene_texts.append(" ".join(current_group))

    # Build scene objects
    scenes = []
    for idx, stext in enumerate(scene_texts):
        motion = CAMERA_MOTIONS[idx % len(CAMERA_MOTIONS)]

        # Synthesize visual prompt
        prompt_parts = []
        if character_desc and character_desc.strip():
            prompt_parts.append(f"Featuring {character_desc.strip()}")

        # Clean words for prompt idea
        words = re.findall(r'\b[A-Za-z0-9\'-]+\b', stext)
        if words and len(words) > 3:
            visual_idea = " ".join(words[:12])
            prompt_parts.append(f"Depicting {visual_idea}")
        else:
            prompt_parts.append(f"Scene illustrating: {stext[:80]}")

        prompt_parts.append(anchor)
        full_prompt = ", ".join(prompt_parts)

        scenes.append({
            "index": idx,
            "id": f"scene_{idx:03d}",
            "text": stext,
            "prompt": full_prompt,
            "motion": motion,
            "image_url": None,
            "local_image_path": None,
            "start": 0.0,
            "end": 0.0,
            "duration": 0.0
        })

    return scenes


async def breakdown_script_with_gemini_or_fallback(
    script_text: str,
    style_key: str = "cinematic",
    character_desc: str = "",
    gemini_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Uses Google Gemini Flash if API key is provided, otherwise falls back smoothly to rule-based.
    """
    key = gemini_key or os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        logger.info("No Gemini API key provided; using smart rule-based Scene Director.")
        return split_script_into_scenes_rule_based(script_text, style_key, character_desc)

    style_info = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cinematic"])
    style_anchor = style_info["prompt_anchor"]

    system_instruction = f"""
You are a master Hollywood film director and AI prompt engineer.
Break down the given narration script into sequential cinematic scenes (each ~4-6 seconds of speech).
For each scene, provide:
1. "text": The exact verbatim spoken line(s) for this scene from the script.
2. "prompt": A highly detailed English visual prompt for FLUX.1.
   Include character: "{character_desc if character_desc else 'cinematic subject'}"
   Include style: "{style_anchor}"
   Describe composition, lighting, camera angle, facial emotion, environment.
3. "motion": One of ["zoom_in_slow", "zoom_out_slow", "pan_left_right", "pan_right_left", "zoom_in_fast"].

Output ONLY a valid JSON array of objects with keys: index, text, prompt, motion.
Do NOT output markdown blocks or conversational text.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": system_instruction + "\n\nScript:\n" + script_text}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.4
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=20))
        resp_data = json.loads(resp.read().decode("utf-8"))

        raw_content = resp_data["candidates"][0]["content"]["parts"][0]["text"]
        raw_content = re.sub(r'^```json\s*', '', raw_content.strip())
        raw_content = re.sub(r'```$', '', raw_content.strip())
        parsed_scenes = json.loads(raw_content)

        results = []
        for i, item in enumerate(parsed_scenes):
            results.append({
                "index": i,
                "id": f"scene_{i:03d}",
                "text": item.get("text", "").strip(),
                "prompt": item.get("prompt", "").strip() or style_anchor,
                "motion": item.get("motion", CAMERA_MOTIONS[i % len(CAMERA_MOTIONS)]),
                "image_url": None,
                "local_image_path": None,
                "start": 0.0,
                "end": 0.0,
                "duration": 0.0
            })
        if results:
            return results
    except Exception as e:
        logger.warning(f"Gemini director call failed ({e}); falling back to smart rule-based breakdown.")

    return split_script_into_scenes_rule_based(script_text, style_key, character_desc)


# ---------------------------------------------------------------------------
# 2. 4K Visual Generation via Pollinations FLUX.1
# ---------------------------------------------------------------------------
def get_flux_dimensions(aspect_ratio: str = "9:16") -> tuple[int, int]:
    """Returns optimal width & height for FLUX.1 generation."""
    if aspect_ratio == "9:16":
        return 768, 1344  # Crisp vertical (Shorts / Reels)
    elif aspect_ratio == "16:9":
        return 1344, 768  # Wide cinematic (YouTube)
    else:
        return 1024, 1024  # Square (Instagram post)


async def generate_single_scene_image(
    scene_idx: int,
    prompt: str,
    aspect_ratio: str,
    save_path: str,
    seed: int
) -> bool:
    """
    Downloads an AI image from Pollinations FLUX.1 with fallback to turbo model.
    """
    width, height = get_flux_dimensions(aspect_ratio)
    encoded_prompt = urllib.parse.quote_plus(prompt.strip())

    # Primary attempt: FLUX.1 model
    primary_url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={width}&height={height}&model=flux&seed={seed}&nologo=true"
    )

    # Fallback attempt: Turbo model (ultra-fast if FLUX is busy)
    fallback_url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={width}&height={height}&model=turbo&seed={seed}&nologo=true"
    )

    urls_to_try = [primary_url, fallback_url]

    for attempt_url in urls_to_try:
        try:
            req = urllib.request.Request(
                attempt_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) UmarVideoStudio/10.0"}
            )
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=35))
            if resp.status == 200:
                img_bytes = resp.read()
                if len(img_bytes) > 2048:
                    with open(save_path, "wb") as f_out:
                        f_out.write(img_bytes)
                    return True
        except Exception as e:
            logger.warning(f"Scene {scene_idx} image generation attempt failed: {e}")
            await asyncio.sleep(1.0)

    # If both remote attempts fail, generate a solid color background with text fallback
    try:
        import subprocess
        dim = get_dimensions(aspect_ratio, "1080p")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=0x111827:s={dim[0]}x{dim[1]}:d=1",
            "-frames:v", "1", save_path
        ], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


async def generate_scene_images_batch(
    scenes: List[Dict[str, Any]],
    aspect_ratio: str,
    output_dir: str,
    session_id: str,
    base_seed: int = 42,
    progress_callback=None
) -> List[Dict[str, Any]]:
    """
    Generates high-res FLUX images for all scenes with concurrency and progress updates.
    """
    os.makedirs(output_dir, exist_ok=True)
    total = len(scenes)
    sem = asyncio.Semaphore(2)  # 2 parallel requests to avoid rate limits

    async def worker(idx: int, scene: Dict[str, Any]):
        filename = f"scene_{idx:03d}.jpg"
        local_path = os.path.join(output_dir, filename)
        seed = (base_seed + (idx * 1337)) % 999999

        async with sem:
            ok = await generate_single_scene_image(
                scene_idx=idx,
                prompt=scene["prompt"],
                aspect_ratio=aspect_ratio,
                save_path=local_path,
                seed=seed
            )

        if ok and os.path.exists(local_path):
            scene["local_image_path"] = local_path
            scene["image_url"] = f"/files/{session_id}/{filename}"
        else:
            scene["local_image_path"] = None
            scene["image_url"] = None

        if progress_callback:
            progress_callback(idx, total, scene)

    await asyncio.gather(*[worker(i, s) for i, s in enumerate(scenes)])
    return scenes


# ---------------------------------------------------------------------------
# 3. Audio & Subtitle Alignment to Scenes
# ---------------------------------------------------------------------------
def align_scenes_to_audio(
    scenes: List[Dict[str, Any]],
    words: List[Dict[str, Any]],
    total_duration: float
) -> List[Dict[str, Any]]:
    """
    Precisely maps synthesized word timestamps to each scene so visuals switch
    smoothly in sync with speech rhythm.
    """
    total_scenes = len(scenes)
    if total_scenes == 0:
        return scenes

    if not words or total_duration <= 0.5:
        dur_per_scene = max(total_duration / total_scenes, 3.0)
        curr = 0.0
        for s in scenes:
            s["start"] = round(curr, 2)
            s["end"] = round(curr + dur_per_scene, 2)
            s["duration"] = round(dur_per_scene, 2)
            curr += dur_per_scene
        return scenes

    total_words = len(words)
    total_scene_chars = sum(len(s.get("text", "").replace(" ", "")) for s in scenes) or 1

    current_word_idx = 0
    running_start = 0.0

    for i, s in enumerate(scenes):
        stext = s.get("text", "").replace(" ", "")
        ratio = len(stext) / total_scene_chars
        words_for_this_scene = max(1, int(round(ratio * total_words)))

        end_word_idx = min(current_word_idx + words_for_this_scene, total_words)
        if i == total_scenes - 1:
            end_word_idx = total_words

        if current_word_idx < total_words:
            scene_start = running_start
            if end_word_idx > 0 and end_word_idx <= total_words:
                scene_end = words[end_word_idx - 1]["end"]
            else:
                scene_end = total_duration
        else:
            scene_start = running_start
            scene_end = total_duration

        if scene_end <= scene_start:
            scene_end = scene_start + 3.0

        if i == total_scenes - 1:
            scene_end = max(scene_end, total_duration)

        s["start"] = round(scene_start, 2)
        s["end"] = round(scene_end, 2)
        s["duration"] = round(scene_end - scene_start, 2)

        running_start = s["end"]
        current_word_idx = end_word_idx

    scenes[0]["start"] = 0.0
    scenes[-1]["end"] = max(scenes[-1]["end"], total_duration)
    scenes[-1]["duration"] = round(scenes[-1]["end"] - scenes[-1]["start"], 2)

    return scenes


# ---------------------------------------------------------------------------
# 4. Master All-in-One Pipeline Execution
# ---------------------------------------------------------------------------
async def run_ai_video_pipeline(
    job_id: str,
    script_text: str,
    aspect_ratio: str = "9:16",
    style_key: str = "cinematic",
    character_desc: str = "",
    voice_id: str = "ur-PK-AsadNeural",
    speed: float = 1.0,
    pitch: int = 0,
    subtitles_enabled: bool = True,
    subtitle_style: str = "tiktok_yellow",
    session_upload_dir: str = "",
    gemini_key: Optional[str] = None,
    custom_scenes: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Executes the entire end-to-end Script-to-Video pipeline:
    1. Scene Breakdown
    2. Edge-TTS Audio & Word Timestamps
    3. FLUX.1 4K Visual Generation
    4. Ken Burns 3D Assembly + Subtitle Burning
    """
    os.makedirs(session_upload_dir, exist_ok=True)
    session_id = os.path.basename(session_upload_dir)

    set_ai_video_progress(job_id, 5, "breakdown", "Director is analyzing script & composing scenes...")

    # Stage 1: Scene Breakdown
    if custom_scenes and len(custom_scenes) > 0:
        scenes = custom_scenes
    else:
        scenes = await breakdown_script_with_gemini_or_fallback(
            script_text=script_text,
            style_key=style_key,
            character_desc=character_desc,
            gemini_key=gemini_key
        )

    set_ai_video_progress(
        job_id,
        20,
        "voice",
        f"Synthesizing neural voiceover with {voice_id}...",
        result={"scenes": scenes}
    )

    # Stage 2: Voiceover & Timestamp Synthesis
    tts_result = await tts_engine.synthesize_speech(
        text=script_text,
        voice=voice_id,
        speed=speed,
        pitch=pitch,
        output_dir=session_upload_dir,
        file_prefix=f"aivideo_voice_{job_id}"
    )

    voice_audio_path = tts_result["audio_path"]
    words = tts_result["words"]
    total_audio_duration = tts_result["duration"]

    # Align scenes to audio timing
    scenes = align_scenes_to_audio(scenes, words, total_audio_duration)

    set_ai_video_progress(
        job_id,
        35,
        "images",
        f"Generating 4K consistent visuals with Pollinations FLUX.1 (0/{len(scenes)})...",
        result={"scenes": scenes, "audio_url": f"/files/{session_id}/{tts_result['audio_filename']}"}
    )

    # Stage 3: Image Generation via FLUX.1
    completed_img_count = 0

    def on_image_done(idx: int, total: int, scene_obj: Dict[str, Any]):
        nonlocal completed_img_count
        completed_img_count += 1
        pct = 35 + int((completed_img_count / total) * 35)  # 35% -> 70%
        set_ai_video_progress(
            job_id,
            pct,
            "images",
            f"Generating 4K consistent visuals with FLUX.1 ({completed_img_count}/{total})...",
            result={"scenes": scenes}
        )

    # Generate images
    images_dir = os.path.join(session_upload_dir, "scenes")
    scenes = await generate_scene_images_batch(
        scenes=scenes,
        aspect_ratio=aspect_ratio,
        output_dir=images_dir,
        session_id=f"{session_id}/scenes",
        base_seed=abs(hash(character_desc or script_text[:30])) % 999999,
        progress_callback=on_image_done
    )

    set_ai_video_progress(
        job_id,
        72,
        "rendering",
        "Applying Ken Burns 3D camera motion & rendering final MP4...",
        result={"scenes": scenes}
    )

    # Stage 4: FFmpeg Ken Burns Video Assembly
    render_work_dir = os.path.join(session_upload_dir, "render_work")
    os.makedirs(render_work_dir, exist_ok=True)

    # Build segments structure for assemble_video
    segments = []
    for s in scenes:
        media_item = {
            "type": "image",
            "local_path": s.get("local_image_path")
        }
        segments.append({
            "start": s["start"],
            "end": s["end"],
            "text": s["text"],
            "media": media_item,
            "effect": s.get("motion", "zoom_in_slow")
        })

    # Subtitle configuration
    caption_cfg = None
    if subtitles_enabled:
        from caption_generator import STYLE_PRESETS as CAP_PRESETS
        preset = CAP_PRESETS.get(subtitle_style, CAP_PRESETS.get("tiktok_yellow", {}))
        caption_cfg = {
            "enabled": True,
            "mode": "word",
            "font": preset.get("font", "impact"),
            "font_size": 64 if aspect_ratio == "9:16" else 52,
            "color": preset.get("color", "#FFD166"),
            "highlight_color": "#00F0FF",
            "position": "middle" if aspect_ratio == "9:16" else "bottom",
            "outline": True,
            "background_box": preset.get("background_box", False),
            "bold": True,
            "language_mode": "urdu" if "ur-" in voice_id else "default"
        }

    final_video_filename = f"ai_video_{job_id}_final.mp4"
    final_video_path = os.path.join(session_upload_dir, final_video_filename)

    def on_render_progress(p: Dict[str, Any]):
        base_pct = 72
        add_pct = int((p.get("percent", 0) / 100.0) * 26)  # 72% -> 98%
        set_ai_video_progress(
            job_id,
            base_pct + add_pct,
            "rendering",
            f"Rendering Video: {p.get('message', 'Processing...')}",
            result={"scenes": scenes}
        )

    # Run assembly in executor to not block asyncio event loop
    loop = asyncio.get_event_loop()
    rendered_file = await loop.run_in_executor(
        None,
        lambda: assemble_video(
            segments=segments,
            voice_path=voice_audio_path,
            work_dir=render_work_dir,
            default_effect="zoom_in_slow",
            transition="fade",
            captions=caption_cfg,
            raw_words=words,
            aspect_ratio=aspect_ratio,
            resolution="1080p",
            progress_callback=on_render_progress
        )
    )

    # Move rendered file to final destination
    if os.path.exists(rendered_file):
        if rendered_file != final_video_path:
            import shutil
            shutil.copyfile(rendered_file, final_video_path)

    final_result = {
        "job_id": job_id,
        "video_url": f"/files/{session_id}/{final_video_filename}",
        "video_path": final_video_path,
        "audio_url": f"/files/{session_id}/{tts_result['audio_filename']}",
        "srt_url": f"/files/{session_id}/{tts_result['srt_filename']}",
        "scenes": scenes,
        "total_duration": total_audio_duration,
        "aspect_ratio": aspect_ratio,
        "style": style_key,
        "voice": voice_id,
        "segments_for_editor": segments,
        "raw_words": words
    }

    set_ai_video_progress(
        job_id,
        100,
        "completed",
        "AI Video generation complete! Ready to watch & share. 🎬✨",
        is_done=True,
        result=final_result
    )

    return final_result
