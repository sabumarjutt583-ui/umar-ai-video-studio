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
        "language": "Urdu (Pakistan)",
        "locale": "ur-PK",
        "flag": "🇵🇰",
        "gender": "Male",
        "category": "Storyteller / Bayan",
        "sample": "یہ ایک خوبصورت اور دلکش کہانی ہے۔"
    },
    {
        "id": "ur-PK-UzmaNeural",
        "name": "Uzma Neural",
        "language": "Urdu (Pakistan)",
        "locale": "ur-PK",
        "flag": "🇵🇰",
        "gender": "Female",
        "category": "Narrator / News",
        "sample": "آج کی تازہ ترین خبریں اور اہم معلومات۔"
    },
    {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher Neural",
        "language": "English (United States)",
        "locale": "en-US",
        "flag": "🇺🇸",
        "gender": "Male",
        "category": "Deep Documentary / Cinematic",
        "sample": "In a world driven by innovation, every story matters."
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny Neural",
        "language": "English (United States)",
        "locale": "en-US",
        "flag": "🇺🇸",
        "gender": "Female",
        "category": "Warm / Expressive / YouTube",
        "sample": "Welcome back to the channel! Today we are exploring something amazing."
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy Neural",
        "language": "English (United States)",
        "locale": "en-US",
        "flag": "🇺🇸",
        "gender": "Male",
        "category": "Friendly / Explainer / Tech",
        "sample": "Let's break down how this technology actually works behind the scenes."
    },
    {
        "id": "en-US-AriaNeural",
        "name": "Aria Neural",
        "language": "English (United States)",
        "locale": "en-US",
        "flag": "🇺🇸",
        "gender": "Female",
        "category": "Dynamic / Confident / Commercial",
        "sample": "Take your videos to the next level with studio quality AI."
    },
    {
        "id": "en-GB-RyanNeural",
        "name": "Ryan Neural",
        "language": "English (United Kingdom)",
        "locale": "en-GB",
        "flag": "🇬🇧",
        "gender": "Male",
        "category": "British Narrative / History",
        "sample": "Deep within the archives of history lies an extraordinary secret."
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "Sonia Neural",
        "language": "English (United Kingdom)",
        "locale": "en-GB",
        "flag": "🇬🇧",
        "gender": "Female",
        "category": "British Articulate / Drama",
        "sample": "The truth was far more remarkable than anyone could have anticipated."
    },
    {
        "id": "hi-IN-MadhurNeural",
        "name": "Madhur Neural",
        "language": "Hindi (India)",
        "locale": "hi-IN",
        "flag": "🇮🇳",
        "gender": "Male",
        "category": "Storytelling / Podcast",
        "sample": "नमस्ते दोस्तों, आज हम एक नई और प्रेरणादायक कहानी जानेंगे।"
    },
    {
        "id": "hi-IN-SwaraNeural",
        "name": "Swara Neural",
        "language": "Hindi (India)",
        "locale": "hi-IN",
        "flag": "🇮🇳",
        "gender": "Female",
        "category": "Energetic / Informative",
        "sample": "वीडियो को अंत तक जरूर देखें और अपनी राय साझा करें।"
    },
    {
        "id": "ar-SA-HamedNeural",
        "name": "Hamed Neural",
        "language": "Arabic (Saudi Arabia)",
        "locale": "ar-SA",
        "flag": "🇸🇦",
        "gender": "Male",
        "category": "Formal / Eloquent",
        "sample": "مرحباً بكم في استوديو إنتاج الفيديو الذكي."
    },
    {
        "id": "ko-KR-HyunsuNeural",
        "name": "Hyunsu Multilingual",
        "language": "Korean (South Korea)",
        "locale": "ko-KR",
        "flag": "🇰🇷",
        "gender": "Male",
        "category": "FameSpeak Model / Multilingual",
        "sample": "후회, 안 하시겠어요? 진정한 변화는 지금 시작됩니다."
    },
    {
        "id": "tr-TR-AhmetNeural",
        "name": "Ahmet Neural",
        "language": "Turkish (Turkey)",
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


async def list_all_available_voices() -> List[Dict[str, Any]]:
    """Returns all voices from edge-tts if available, else featured list."""
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
            
            # Extract clean display name
            name_match = re.search(r'-([A-Za-z0-9]+)Neural', short_name)
            clean_name = name_match.group(1) if name_match else short_name

            res.append({
                "id": short_name,
                "name": clean_name,
                "locale": locale,
                "gender": gender,
                "friendlyName": friendly
            })
        return res if res else FEATURED_VOICES
    except Exception as e:
        logger.warning(f"Failed to fetch live Edge-TTS voices: {e}")
        return FEATURED_VOICES


async def synthesize_speech(
    text: str,
    voice: str = "ur-PK-AsadNeural",
    speed: float = 1.0,
    pitch: int = 0,
    output_dir: str = "",
    file_prefix: str = "tts_voice"
) -> Dict[str, Any]:
    """
    Synthesizes speech using Edge-TTS with word-level timestamps.
    Returns:
    {
        "audio_path": "/path/to/file.mp3",
        "audio_filename": "tts_voice_xyz.mp3",
        "srt_path": "/path/to/file.srt",
        "words": [{"word": "hello", "start": 0.0, "end": 0.45}, ...],
        "duration": 5.2,
        "clean_text": "...",
        "engine": "edge-tts"
    }
    """
    if not EDGE_TTS_AVAILABLE or edge_tts is None:
        raise RuntimeError("edge-tts package is not installed. Run: pip install edge-tts")

    os.makedirs(output_dir, exist_ok=True)
    job_id = uuid.uuid4().hex[:8]
    audio_filename = f"{file_prefix}_{job_id}.mp3"
    srt_filename = f"{file_prefix}_{job_id}.srt"
    json_filename = f"{file_prefix}_{job_id}_words.json"

    audio_path = os.path.join(output_dir, audio_filename)
    srt_path = os.path.join(output_dir, srt_filename)
    json_path = os.path.join(output_dir, json_filename)

    clean_text = clean_script_for_edge_tts(text)
    if not clean_text:
        clean_text = "..."

    rate_str = format_rate_str(speed)
    pitch_str = format_pitch_str(pitch)

    communicate = edge_tts.Communicate(
        text=clean_text,
        voice=voice,
        rate=rate_str,
        pitch=pitch_str
    )

    words = []
    submaker = edge_tts.SubMaker()
    max_end_time = 0.0

    with open(audio_path, "wb") as f_audio:
        async for chunk in communicate.stream():
            chunk_type = chunk.get("type", "")
            if chunk_type == "audio":
                f_audio.write(chunk.get("data", b""))
            elif chunk_type in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
                offset_ticks = chunk.get("offset", 0)
                duration_ticks = chunk.get("duration", 0)
                text_seg = chunk.get("text", "")

                start_sec = round(offset_ticks / 10_000_000.0, 3)
                duration_sec = round(duration_ticks / 10_000_000.0, 3)
                end_sec = round(start_sec + duration_sec, 3)
                max_end_time = max(max_end_time, end_sec)

                if chunk_type == "WordBoundary":
                    words.append({
                        "word": text_seg,
                        "start": start_sec,
                        "end": end_sec,
                        "duration": duration_sec
                    })
                else:
                    # SentenceBoundary: interpolate word timing within sentence span
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

    # Generate SRT subtitles file
    srt_content = submaker.get_srt()
    with open(srt_path, "w", encoding="utf-8") as f_srt:
        f_srt.write(srt_content)

    # Save words JSON
    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(words, f_json, indent=2, ensure_ascii=False)

    # Get precise duration
    total_duration = max_end_time
    try:
        from audio_tools import probe_duration
        probed = probe_duration(audio_path)
        if probed > 0:
            total_duration = round(probed, 2)
    except Exception:
        pass

    return {
        "audio_path": audio_path,
        "audio_filename": audio_filename,
        "srt_path": srt_path,
        "srt_filename": srt_filename,
        "json_path": json_path,
        "json_filename": json_filename,
        "words": words,
        "duration": total_duration,
        "clean_text": clean_text,
        "engine": "edge-tts",
        "voice": voice,
        "speed": speed,
        "pitch": pitch
    }
