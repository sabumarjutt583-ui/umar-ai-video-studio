"""
AI Voice Engine for Umar AI Video Studio.
Supports:
- Microsoft Edge-TTS (100% Free, multi-language neural voices with 0 API keys)
- Word-level timestamp generation (JSON & SRT/VTT)
- Emotion & paralinguistic tag parsing ([laugh], [sigh], [gasp], [pause], etc.)
- Voice Cloning profile management
- Direct injection into Video Studio timeline & projects
"""

import os
import re
import json
import asyncio
import uuid
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("tts_engine")

# Try importing edge-tts; graceful fallback if not yet installed
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    edge_tts = None
    EDGE_TTS_AVAILABLE = False

# Popular curated voices for quick selection
FEATURED_VOICES = [
    {
        "id": "ur-PK-AsadNeural",
        "name": "Asad Neural",
        "language": "Urdu",
        "country": "Pakistan",
        "country_code": "PK",
        "locale": "ur-PK",
        "flag": "🇵🇰",
        "gender": "Male",
        "category": "Storyteller / Bayan",
        "sample": "یہ ایک خوبصورت اور دلکش کہانی ہے۔"
    },
    {
        "id": "ur-PK-UzmaNeural",
        "name": "Uzma Neural",
        "language": "Urdu",
        "country": "Pakistan",
        "country_code": "PK",
        "locale": "ur-PK",
        "flag": "🇵🇰",
        "gender": "Female",
        "category": "Narrator / News",
        "sample": "آج کی تازہ ترین خبریں اور اہم معلومات۔"
    },
    {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher Neural",
        "language": "English",
        "country": "United States",
        "country_code": "US",
        "locale": "en-US",
        "flag": "🇺🇸",
        "gender": "Male",
        "category": "Deep Documentary / Cinematic",
        "sample": "In a world driven by innovation, every story matters."
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny Neural",
        "language": "English",
        "country": "United States",
        "country_code": "US",
        "locale": "en-US",
        "flag": "🇺🇸",
        "gender": "Female",
        "category": "Warm / Expressive / YouTube",
        "sample": "Welcome back to the channel! Today we are exploring something amazing."
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy Neural",
        "language": "English",
        "country": "United States",
        "country_code": "US",
        "locale": "en-US",
        "flag": "🇺🇸",
        "gender": "Male",
        "category": "Friendly / Explainer / Tech",
        "sample": "Let's break down how this technology actually works behind the scenes."
    },
    {
        "id": "en-US-AriaNeural",
        "name": "Aria Neural",
        "language": "English",
        "country": "United States",
        "country_code": "US",
        "locale": "en-US",
        "flag": "🇺🇸",
        "gender": "Female",
        "category": "Dynamic / Confident / Commercial",
        "sample": "Take your videos to the next level with studio quality AI."
    },
    {
        "id": "en-GB-RyanNeural",
        "name": "Ryan Neural",
        "language": "English",
        "country": "United Kingdom",
        "country_code": "GB",
        "locale": "en-GB",
        "flag": "🇬🇧",
        "gender": "Male",
        "category": "British Narrative / History",
        "sample": "Deep within the archives of history lies an extraordinary secret."
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "Sonia Neural",
        "language": "English",
        "country": "United Kingdom",
        "country_code": "GB",
        "locale": "en-GB",
        "flag": "🇬🇧",
        "gender": "Female",
        "category": "British Articulate / Drama",
        "sample": "The truth was far more remarkable than anyone could have anticipated."
    },
    {
        "id": "hi-IN-MadhurNeural",
        "name": "Madhur Neural",
        "language": "Hindi",
        "country": "India",
        "country_code": "IN",
        "locale": "hi-IN",
        "flag": "🇮🇳",
        "gender": "Male",
        "category": "Storytelling / Podcast",
        "sample": "नमस्ते दोस्तों, आज हम एक नई और प्रेरणादायक कहानी जानेंगे।"
    },
    {
        "id": "hi-IN-SwaraNeural",
        "name": "Swara Neural",
        "language": "Hindi",
        "country": "India",
        "country_code": "IN",
        "locale": "hi-IN",
        "flag": "🇮🇳",
        "gender": "Female",
        "category": "Energetic / Informative",
        "sample": "वीडियो को अंत तक जरूर देखें और अपनी राय साझा करें।"
    },
    {
        "id": "ar-SA-HamedNeural",
        "name": "Hamed Neural",
        "language": "Arabic",
        "country": "Saudi Arabia",
        "country_code": "SA",
        "locale": "ar-SA",
        "flag": "🇸🇦",
        "gender": "Male",
        "category": "Formal / Eloquent",
        "sample": "مرحباً بكم في استوديو إنتاج الفيديو الذکی."
    },
    {
        "id": "ko-KR-HyunsuNeural",
        "name": "Hyunsu Multilingual",
        "language": "Korean",
        "country": "South Korea",
        "country_code": "KR",
        "locale": "ko-KR",
        "flag": "🇰🇷",
        "gender": "Male",
        "category": "FameSpeak Model / Multilingual",
        "sample": "후회, 안 하시겠어요? 진정한 변화는 지금 시작됩니다."
    },
    {
        "id": "tr-TR-AhmetNeural",
        "name": "Ahmet Neural",
        "language": "Turkish",
        "country": "Turkey",
        "country_code": "TR",
        "locale": "tr-TR",
        "flag": "🇹🇷",
        "gender": "Male",
        "category": "Dramatic / Narration",
        "sample": "Bu inanılmaz yolculukta bize katılmaya hazır mısınız?"
    }
]

# Quick scenario templates inspired by FameSpeak
SCENARIO_TEMPLATES = [
    {
        "id": "youtube_intro",
        "label": "YouTube Intro",
        "icon": "📺",
        "script": "What if I told you that everything you knew about artificial intelligence was about to change? [pause: 1s] In this video, we uncover the shocking truth [excited] that nobody is talking about. Make sure to watch until the very end!"
    },
    {
        "id": "story_narration",
        "label": "Story Narration",
        "icon": "📖",
        "script": "The clock struck midnight. [pause: 1s] Outside the window, the wind began to howl softly. [whisper] He reached for the ancient leather diary, his hands trembling slightly. [sigh] Some secrets were never meant to be discovered."
    },
    {
        "id": "faceless_tiktok",
        "label": "Faceless TikTok / Shorts",
        "icon": "📱",
        "script": "Stop scrolling right now! [excited] Here are three psychological tricks that will make anyone respect you instantly. [pause: 500ms] Number one will completely surprise you."
    },
    {
        "id": "islamic_bayan",
        "label": "Islamic / Moral Bayan",
        "icon": "🕌",
        "script": "زندگی میں سب سے قیمتی چیز وقت اور دل کا سکون ہے۔ [pause: 1s] جب انسان اللہ پر توکل کرتا ہے تو اس کے دل کو وہ اطمینان ملتا ہے جو دنیا کی کوئی دولت نہیں دے سکتی۔"
    },
    {
        "id": "product_demo",
        "label": "Product Demo",
        "icon": "🚀",
        "script": "Say goodbye to hours of tedious video editing. [excited] With our automated AI studio, create studio-quality videos in seconds, not hours. [clear throat] Let's dive right into the demo."
    },
    {
        "id": "motivational",
        "label": "Motivational Speech",
        "icon": "🔥",
        "script": "Every champion was once a contender that refused to give up. [pause: 1s] When the road gets dark and everyone doubts you, [excited] that is the exact moment you push forward!"
    }
]

# Clickable emotion tags metadata
EMOTION_TAGS = [
    {"tag": "[laugh]", "label": "Laugh", "icon": "😊", "desc": "Light conversational laugh"},
    {"tag": "[sigh]", "label": "Sigh", "icon": "💨", "desc": "Reflective deep breath / sigh"},
    {"tag": "[gasp]", "label": "Gasp", "icon": "😮", "desc": "Surprised sudden breath"},
    {"tag": "[whisper]", "label": "Whisper", "icon": "🤫", "desc": "Soft confidential whisper"},
    {"tag": "[clear throat]", "label": "Clear Throat", "icon": "🗣️", "desc": "Natural pause with throat clear"},
    {"tag": "[pause: 1s]", "label": "1s Pause", "icon": "⏳", "desc": "Dramatic 1-second silence"},
    {"tag": "[excited]", "label": "Excited", "icon": "🔥", "desc": "Energetic, high-impact tone"},
    {"tag": "[sad]", "label": "Sad / Serious", "icon": "😢", "desc": "Somber, serious tone"},
    {"tag": "[shush]", "label": "Shush", "icon": "🤐", "desc": "Quiet hushing cue"},
    {"tag": "[cough]", "label": "Cough", "icon": "🤧", "desc": "Conversational micro-cough"}
]


def clean_script_for_edge_tts(raw_text: str) -> str:
    """
    Translates bracket emotion tags for Edge-TTS so it sounds ultra natural
    without awkwardly reading '[laugh]' aloud.
    """
    text = raw_text

    # Convert pauses
    text = re.sub(r'\[pause:\s*(\d+)s\]', r'... ... ', text)
    text = re.sub(r'\[pause:\s*(\d+)ms\]', r'... ', text)
    text = re.sub(r'\[pause\]', r'... ', text)

    # Convert paralinguistic emotions into natural speech pauses/interjections
    text = re.sub(r'\[laugh\]', r' — haha, ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[chuckle\]', r' — heh, ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[sigh\]', r' — phew... ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[gasp\]', r' — oh! ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[clear throat\]', r' — ahem, ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[shush\]', r' — shh... ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[cough\]', r' — uhm, ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[sniff\]', r' — ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[groan\]', r' — ah... ', text, flags=re.IGNORECASE)

    # Emotion inflection hints
    text = re.sub(r'\[excited\]', r'! ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[whisper\]', r'... ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[sad\]', r'... ', text, flags=re.IGNORECASE)

    # Clean any leftover bracket tags
    text = re.sub(r'\[[a-zA-Z0-9_\-\s:]+\]', '', text)
    # Normalize multiple whitespaces and ellipses
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def format_rate_str(speed_multiplier: float) -> str:
    """Converts 1.2 -> '+20%' or 0.8 -> '-20%'"""
    pct = int(round((speed_multiplier - 1.0) * 100))
    if pct >= 0:
        return f"+{pct}%"
    return f"{pct}%"


def format_pitch_str(pitch_hz: int) -> str:
    """Converts 4 -> '+4Hz' or -5 -> '-5Hz'"""
    if pitch_hz >= 0:
        return f"+{pitch_hz}Hz"
    return f"{pitch_hz}Hz"


# ----------------------------------------------------------------------------
# In-Memory Progress Tracking for Live Percentages (0% - 100%)
# ----------------------------------------------------------------------------
TTS_JOBS: Dict[str, Dict[str, Any]] = {}

def set_job_progress(
    job_id: Optional[str],
    percent: int,
    stage: str,
    message: str,
    is_done: bool = False,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
):
    if not job_id:
        return
    TTS_JOBS[job_id] = {
        "job_id": job_id,
        "percent": max(0, min(100, int(percent))),
        "stage": stage,
        "message": message,
        "is_done": is_done,
        "result": result,
        "error": error
    }

def get_job_progress(job_id: str) -> Dict[str, Any]:
    return TTS_JOBS.get(job_id, {
        "job_id": job_id,
        "percent": 0,
        "stage": "not_found",
        "message": "Initializing synthesizer...",
        "is_done": False,
        "result": None,
        "error": None
    })


def get_country_flag(country_code: str) -> str:
    """Converts 2-letter ISO code to Unicode flag emoji (e.g. PK -> 🇵🇰, US -> 🇺🇸)."""
    if not country_code or len(country_code) != 2:
        return "🎙️"
    try:
        return "".join(chr(127397 + ord(c)) for c in country_code.upper())
    except Exception:
        return "🎙️"


def format_srt_time(seconds: float) -> str:
    """Formats float seconds into SRT timestamp '00:00:01,234'."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def words_to_srt(words: List[Dict[str, Any]], words_per_sub: int = 5) -> str:
    """Generates clean, readable SRT subtitle format from aligned word timestamps."""
    if not words:
        return ""
    lines = []
    sub_index = 1
    curr_group = []
    for w in words:
        curr_group.append(w)
        txt = (w.get("word") or "").strip()
        # End subtitle block on sentence punctuation or chunk size
        if len(curr_group) >= words_per_sub or txt.endswith((".", "!", "?", "۔", "؟", "…")):
            start_sec = curr_group[0]["start"]
            end_sec = curr_group[-1]["end"]
            sentence_str = " ".join(item["word"] for item in curr_group)
            lines.append(f"{sub_index}")
            lines.append(f"{format_srt_time(start_sec)} --> {format_srt_time(end_sec)}")
            lines.append(sentence_str)
            lines.append("")
            sub_index += 1
            curr_group = []
    if curr_group:
        start_sec = curr_group[0]["start"]
        end_sec = curr_group[-1]["end"]
        sentence_str = " ".join(item["word"] for item in curr_group)
        lines.append(f"{sub_index}")
        lines.append(f"{format_srt_time(start_sec)} --> {format_srt_time(end_sec)}")
        lines.append(sentence_str)
        lines.append("")
    return "\n".join(lines)


def split_script_into_chunks(text: str, target_chunk_size: int = 750) -> List[str]:
    """Splits a long script cleanly on sentence/paragraph boundaries without cutting words."""
    if len(text) <= target_chunk_size:
        return [text]

    paragraphs = [p.strip() for p in re.split(r'(\n+)', text) if p.strip()]
    chunks = []
    current_chunk = []
    current_len = 0

    for p in paragraphs:
        if len(p) > target_chunk_size:
            sentences = re.split(r'([.?!۔؟…\n]+\s*)', p)
            sent_parts = []
            for i in range(0, len(sentences), 2):
                s = sentences[i]
                delim = sentences[i+1] if i+1 < len(sentences) else ''
                combined = (s + delim).strip()
                if combined:
                    sent_parts.append(combined)
            for s in sent_parts:
                if current_len + len(s) > target_chunk_size and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [s]
                    current_len = len(s)
                else:
                    current_chunk.append(s)
                    current_len += len(s)
        else:
            if current_len + len(p) > target_chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [p]
                current_len = len(p)
            else:
                current_chunk.append(p)
                current_len += len(p)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks if chunks else [text]


async def list_all_available_voices() -> List[Dict[str, Any]]:
    """Returns all voices from edge-tts enriched with name, country, language, flag, and gender."""
    if not EDGE_TTS_AVAILABLE or edge_tts is None:
        return FEATURED_VOICES

    try:
        raw_voices = await edge_tts.list_voices()
        res = []
        for v in raw_voices:
            short_name = v.get("ShortName", "")
            locale = v.get("Locale", "")
            gender = v.get("Gender", "Unknown")
            friendly = v.get("FriendlyName", short_name)
            locale_name = v.get("LocaleName", "")

            parts = locale.split("-")
            lang_code = parts[0] if len(parts) > 0 else ""
            country_code = parts[1] if len(parts) > 1 else ""

            # Parse language and country name from LocaleName: e.g. "Urdu (Pakistan)"
            m = re.match(r"^(.*?)\s*\((.*?)\)$", locale_name)
            if m:
                lang_name = m.group(1).strip()
                country_name = m.group(2).strip()
            else:
                lang_name = locale_name or lang_code
                country_name = country_code or "Global"

            # Clean display name: e.g. "Asad Neural"
            name_match = re.search(r'-([A-Za-z0-9]+)Neural', short_name)
            clean_name = (name_match.group(1) + " Neural") if name_match else short_name
            flag = get_country_flag(country_code)

            res.append({
                "id": short_name,
                "name": clean_name,
                "locale": locale,
                "language": lang_name,
                "country": country_name,
                "country_code": country_code,
                "flag": flag,
                "gender": gender,
                "friendlyName": friendly
            })
        return res if res else FEATURED_VOICES
    except Exception as e:
        logger.warning(f"Failed to fetch live Edge-TTS voices: {e}")
        return FEATURED_VOICES


async def _synthesize_single_chunk(
    chunk_index: int,
    chunk_text: str,
    voice: str,
    rate_str: str,
    pitch_str: str,
    part_audio_path: str
) -> Dict[str, Any]:
    """Synthesizes a single chunk and collects its words & max duration."""
    communicate = edge_tts.Communicate(
        text=chunk_text,
        voice=voice,
        rate=rate_str,
        pitch=pitch_str
    )

    words = []
    max_chunk_end = 0.0

    with open(part_audio_path, "wb") as f_part:
        async for chunk in communicate.stream():
            chunk_type = chunk.get("type", "")
            if chunk_type == "audio":
                f_part.write(chunk.get("data", b""))
            elif chunk_type in ("WordBoundary", "SentenceBoundary"):
                offset_ticks = chunk.get("offset", 0)
                duration_ticks = chunk.get("duration", 0)
                text_seg = chunk.get("text", "")

                start_sec = round(offset_ticks / 10_000_000.0, 3)
                duration_sec = round(duration_ticks / 10_000_000.0, 3)
                end_sec = round(start_sec + duration_sec, 3)
                max_chunk_end = max(max_chunk_end, end_sec)

                if chunk_type == "WordBoundary":
                    words.append({
                        "word": text_seg,
                        "start": start_sec,
                        "end": end_sec,
                        "duration": duration_sec
                    })
                else:
                    sub_words = [w for w in text_seg.split() if w]
                    if sub_words:
                        total_chars = sum(len(w) for w in sub_words) or 1
                        cursor_t = start_sec
                        for w in sub_words:
                            w_dur = round((len(w) / total_chars) * duration_sec, 3)
                            words.append({
                                "word": w,
                                "start": round(cursor_t, 3),
                                "end": round(cursor_t + w_dur, 3),
                                "duration": w_dur
                            })
                            cursor_t = round(cursor_t + w_dur, 3)

    actual_duration = max_chunk_end
    try:
        from audio_tools import probe_duration
        probed = probe_duration(part_audio_path)
        if probed > 0:
            actual_duration = round(probed, 3)
    except Exception:
        pass

    return {
        "index": chunk_index,
        "audio_path": part_audio_path,
        "duration": actual_duration,
        "words": words,
        "text": chunk_text
    }


async def synthesize_speech(
    text: str,
    voice: str = "ur-PK-AsadNeural",
    speed: float = 1.0,
    pitch: int = 0,
    output_dir: str = "",
    file_prefix: str = "tts_voice",
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synthesizes speech using accelerated Edge-TTS with parallel chunks & real-time progress.
    """
    if not EDGE_TTS_AVAILABLE or edge_tts is None:
        raise RuntimeError("edge-tts package is not installed. Run: pip install edge-tts")

    job_id = job_id or uuid.uuid4().hex[:8]
    os.makedirs(output_dir, exist_ok=True)
    audio_filename = f"{file_prefix}_{job_id}.mp3"
    srt_filename = f"{file_prefix}_{job_id}.srt"
    json_filename = f"{file_prefix}_{job_id}_words.json"

    audio_path = os.path.join(output_dir, audio_filename)
    srt_path = os.path.join(output_dir, srt_filename)
    json_path = os.path.join(output_dir, json_filename)

    set_job_progress(job_id, 10, "preparing", "Parsing emotions and optimizing script...")

    clean_text = clean_script_for_edge_tts(text)
    if not clean_text:
        clean_text = "..."

    rate_str = format_rate_str(speed)
    pitch_str = format_pitch_str(pitch)

    # Split into chunks for acceleration
    chunks = split_script_into_chunks(clean_text, target_chunk_size=750)
    total_chunks = len(chunks)

    set_job_progress(job_id, 20, "synthesizing", f"Generating neural speech ({total_chunks} {'stream' if total_chunks == 1 else 'parallel chunks'})...")

    # If only 1 chunk, synthesize directly to target
    if total_chunks == 1:
        res_chunk = await _synthesize_single_chunk(0, clean_text, voice, rate_str, pitch_str, audio_path)
        words = res_chunk["words"]
        total_duration = res_chunk["duration"]
        set_job_progress(job_id, 85, "finalizing", "Aligning word timestamps and creating subtitles...")
    else:
        # Multi-chunk parallel synthesis
        sem = asyncio.Semaphore(4)
        completed_count = 0
        part_results = [None] * total_chunks

        async def worker(idx: int, c_text: str):
            nonlocal completed_count
            part_path = os.path.join(output_dir, f"temp_{job_id}_part_{idx:03d}.mp3")
            async with sem:
                res = await _synthesize_single_chunk(idx, c_text, voice, rate_str, pitch_str, part_path)
            part_results[idx] = res
            completed_count += 1
            pct = 20 + int((completed_count / total_chunks) * 65)
            set_job_progress(job_id, pct, "synthesizing", f"Synthesized chunk {completed_count} of {total_chunks} ({pct}%)...")

        await asyncio.gather(*[worker(i, c) for i, c in enumerate(chunks)])

        set_job_progress(job_id, 88, "merging", "Merging audio streams seamlessly...")

        # Concat chunks using fast ffmpeg concat copy (lossless, instant)
        concat_list_path = os.path.join(output_dir, f"concat_{job_id}.txt")
        with open(concat_list_path, "w", encoding="utf-8") as f_list:
            for part in part_results:
                if part and os.path.exists(part["audio_path"]):
                    escaped = os.path.abspath(part["audio_path"]).replace("\\", "/").replace("'", "'\\''")
                    f_list.write(f"file '{escaped}'\n")

        import subprocess
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", audio_path]
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode != 0:
            # Fallback: re-encode if copy failed
            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c:a", "libmp3lame", "-b:a", "192k", audio_path], capture_output=True)

        # Merge word timestamps with cumulative offset
        words = []
        cumulative_time = 0.0
        for part in part_results:
            if not part:
                continue
            for w in part["words"]:
                words.append({
                    "word": w["word"],
                    "start": round(w["start"] + cumulative_time, 3),
                    "end": round(w["end"] + cumulative_time, 3),
                    "duration": w["duration"]
                })
            cumulative_time += part["duration"]

        total_duration = round(cumulative_time, 3)

        # Cleanup temp part files
        try:
            if os.path.exists(concat_list_path):
                os.remove(concat_list_path)
            for part in part_results:
                if part and os.path.exists(part["audio_path"]):
                    os.remove(part["audio_path"])
        except Exception:
            pass

    # Generate clean SRT subtitles
    srt_content = words_to_srt(words)
    with open(srt_path, "w", encoding="utf-8") as f_srt:
        f_srt.write(srt_content)

    # Save words JSON
    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(words, f_json, indent=2, ensure_ascii=False)

    # Re-probe final duration
    try:
        from audio_tools import probe_duration
        probed = probe_duration(audio_path)
        if probed > 0:
            total_duration = round(probed, 2)
    except Exception:
        pass

    final_result = {
        "job_id": job_id,
        "audio_path": audio_path,
        "audio_filename": audio_filename,
        "srt_path": srt_path,
        "srt_filename": srt_filename,
        "json_path": json_path,
        "json_filename": json_filename,
        "words": words,
        "duration": total_duration,
        "clean_text": clean_text,
        "chunks_count": total_chunks,
        "engine": "edge-tts",
        "voice": voice,
        "speed": speed,
        "pitch": pitch
    }

    set_job_progress(job_id, 100, "completed", "Voice generation complete! (100%)", is_done=True, result=final_result)
    return final_result
