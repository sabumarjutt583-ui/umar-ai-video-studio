"""
AI Video Auto-Builder — Backend (v10).

Local computer par chalta hai:
    pip install -r requirements.txt
    python app.py
Phir browser mein: http://127.0.0.1:8000/app

v10 mein naya:
- Manual Timing Table (teesra timing tareeka)
- Script/Timestamp Paste Box (file upload ke bajaye seedha paste)
- Voice Multi-Part Upload (recording ke kai hisse -> ek voice)
- Media Mismatch Flagging (render se PEHLE galtiyan pakadna)
- Live render dashboard (stages + percent + ETA + log + CANCEL)
- Project Save/Load
- Dynamic base URL (hardcoded 127.0.0.1 nahi — LAN/phone se bhi chalta hai)
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import uuid
import shutil
import threading
import time
from typing import Optional
import tts_engine

from timestamp_parser import (parse_timestamp_file, extract_raw_words,
                              group_words_by_sentences, count_sentences)
import video_assembler as va
from video_assembler import assemble_video, quick_export_resolution, RenderCancelled
from trigger_detection import detect_sticker_triggers
from media_import import (extract_segment_number, extract_zip, is_video_file,
                          is_audio_file)
from scene_mapper import (parse_scene_file, match_scenes_to_timestamps,
                          parse_scene_time_table, scene_table_to_segments)
from audio_tools import concat_audio_parts, probe_duration, natural_sort_key
from media_validator import validate_segments
import project_store
import auth
import subprocess

# Dropdown/option lists — frontend inhe /options se leta hai (hardcode nahi karta)
from transitions import TRANSITION_LABELS, SPEED_TO_DURATION
from video_filters import FILTER_LABELS
from sfx_assets import SFX_LABELS
from sticker_assets import STICKER_LABELS
from caption_generator import (FONT_MAP, STYLE_PRESETS, SCRIPT_FONT_CANDIDATES,
                              detect_script)

app = FastAPI(title="AI Video Auto-Builder Backend", version="10.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)

# Har session ka data yahan yaad rakhte hain (simple in-memory store)
SESSIONS = {}
_SESSION_LOCK = threading.Lock()

MAX_LOG_LINES = 300

app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="app")

@app.get("/")
def root():
    return RedirectResponse(url="/app/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # local tool hai — sab allow
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_cache_frontend(request: Request, call_next):
    """
    UI files (/app/...) ko browser cache na kare — warna update ke baad purani
    app.js/styles.css chalti rehti thi aur "fix hi nahi hua" lagta tha.
    """
    response = await call_next(request)
    if request.url.path.startswith("/app"):
        response.headers["Cache-Control"] = "no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def base_url(request: Request) -> str:
    """
    BUG FIX: pehle sab URLs mein 'http://127.0.0.1:8000' hardcoded tha — isliye
    phone/LAN/kisi doosre port se tool khole to media aur download links tootte the.
    Ab URL request se hi banta hai.
    """
    return str(request.base_url).rstrip("/")


def get_session(session_id: str) -> dict:
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session nahi mila. Naya session banayein.")
    return session


def session_dir(session_id: str, *parts) -> str:
    path = os.path.join(UPLOAD_DIR, session_id, *parts)
    os.makedirs(path, exist_ok=True)
    return path


def file_url(request: Request, session_id: str, *parts) -> str:
    rel = "/".join(str(p).replace(os.sep, "/") for p in parts)
    return f"{base_url(request)}/files/{session_id}/{rel}"


def url_to_local_path(url_or_path: str) -> str:
    """
    Media ka URL (ya seedha local path) le kar disk par asli file ka path deta hai.
    Media-validator aur render dono isi se local file dhoondte hain.
    """
    if not url_or_path:
        return None
    if os.path.exists(url_or_path):
        return url_or_path
    marker = "/files/"
    if marker in url_or_path:
        rel = url_or_path.split(marker, 1)[1].split("?")[0]
        candidate = os.path.join(UPLOAD_DIR, *rel.split("/"))
        if os.path.exists(candidate):
            return candidate
    return None


def resolve_media_path(media: dict) -> str:
    if not media:
        return None
    return (url_to_local_path(media.get("local_path"))
            or url_to_local_path(media.get("full_url")))


def sanitize_segments(raw: list) -> list:
    """Manual Timing Table / paste box se aaye segments ko saaf-suthra banata hai."""
    cleaned = []
    for item in raw or []:
        try:
            start = float(item.get("start", 0))
            end = float(item.get("end", 0))
        except (TypeError, ValueError):
            continue
        if end <= start:
            continue
        cleaned.append({
            "start": round(start, 3),
            "end": round(end, 3),
            "text": (item.get("text") or "").strip(),
        })
    cleaned.sort(key=lambda s: s["start"])
    return cleaned


def save_upload(file: UploadFile, dest_path: str):
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return dest_path


def new_session_record() -> dict:
    return {
        "created_at": time.time(),
        "voice_file": None,
        "voice_parts": [],
        "voice_duration": 0.0,
        "music_file": None,
        "segments": None,
        "raw_words": None,
        "manual_media": [],
        "custom_sticker_images": [],
        "final_video": None,
        "render_state": None,
        "render_lock": threading.Lock(),
        "cancel_event": None,
        "timing_source": None,
        "settings": {},
    }


# ----------------------------------------------------------------------------
# Health / session / options
# ----------------------------------------------------------------------------

@app.get("/")
def root():
    """Frontend par bhej dete hain (agar mila to), warna health JSON."""
    if os.path.isdir(FRONTEND_DIR):
        return RedirectResponse(url="/app/")
    return {"status": "ok", "message": "Backend chal raha hai ✅", "version": 10}


@app.get("/health")
def health_check():
    tools = {}
    for tool in ("ffmpeg", "ffprobe"):
        tools[tool] = shutil.which(tool) is not None
    return {"status": "ok", "version": 10, "tools": tools,
            "sessions": len(SESSIONS)}


@app.get("/options")
def get_options():
    """
    Saari dropdown lists ek hi jagah se — frontend inhe hardcode nahi karta,
    isliye backend mein naya preset add karne se UI khud update ho jata hai.
    """
    return {
        "transitions": TRANSITION_LABELS,
        "transition_speeds": list(SPEED_TO_DURATION.keys()),
        "color_filters": FILTER_LABELS,
        "sound_effects": SFX_LABELS,
        "stickers": STICKER_LABELS,
        "caption_fonts": {k: v for k, v in FONT_MAP.items()},
        "caption_presets": STYLE_PRESETS,
        "caption_languages": sorted(SCRIPT_FONT_CANDIDATES.keys()),
        "caption_modes": ["line", "word", "karaoke"],
        "caption_animations": ["none", "fade", "pop", "slide_up"],
        "aspect_ratios": list(va.RESOLUTION_TABLE.keys()),
        "resolutions": ["720p", "1080p", "4k"],
        "effects": list(va.ZOOM_PRESETS.keys()) + list(va.PAN_PRESETS) + ["auto"],
        "render_stages": [s[0] for s in va.STAGE_ORDER],
    }


@app.post("/session/new")
def create_session():
    session_id = str(uuid.uuid4())[:8]
    session_dir(session_id)
    with _SESSION_LOCK:
        SESSIONS[session_id] = new_session_record()
    return {"session_id": session_id}


@app.get("/session/{session_id}/state")
def session_state(session_id: str):
    """Frontend refresh/reload ke baad poora state wapas la sakta hai."""
    session = get_session(session_id)
    return {
        "session_id": session_id,
        "has_voice": bool(session.get("voice_file")),
        "voice_parts": session.get("voice_parts", []),
        "voice_duration": session.get("voice_duration", 0.0),
        "has_music": bool(session.get("music_file")),
        "segments": session.get("segments") or [],
        "segment_count": len(session.get("segments") or []),
        "manual_media": session.get("manual_media", []),
        "custom_sticker_images": session.get("custom_sticker_images", []),
        "timing_source": session.get("timing_source"),
        "custom_font_name": session.get("custom_font_name"),
        "scene_mapping_available": session.get("raw_words") is not None,
        "settings": session.get("settings", {}),
        "render_state": session.get("render_state"),
    }


# ----------------------------------------------------------------------------
# Voice (single + MULTI-PART)
# ----------------------------------------------------------------------------

@app.post("/upload/voice/{session_id}")
async def upload_voice(session_id: str, file: UploadFile = File(...)):
    """Ek single voice file save karta hai."""
    session = get_session(session_id)
    path = os.path.join(session_dir(session_id), f"voice_{file.filename}")
    save_upload(file, path)

    duration = probe_duration(path)
    session["voice_file"] = path
    session["voice_parts"] = []
    session["voice_duration"] = duration
    return {"status": "ok", "message": f"Voice file save ho gayi: {file.filename}",
            "duration": round(duration, 2)}


@app.post("/upload/voice-parts/{session_id}")
async def upload_voice_parts(
    session_id: str,
    files: list[UploadFile] = File(...),
    gap_seconds: float = 0.0,
    order: str = "natural",     # "natural" (part2 < part10) ya "as_uploaded"
):
    """
    VOICE MULTI-PART UPLOAD — jab recording ek file mein na ho (part1.mp3,
    part2.mp3 ...). Sab parts ko sahi ORDER mein jodkar ek single voice
    banata hai, aur har part ka exact start-time bhi wapas deta hai.
    """
    session = get_session(session_id)
    if not files or len(files) < 1:
        raise HTTPException(status_code=400, detail="Kam se kam ek audio part chahiye.")

    parts_dir = session_dir(session_id, "voice_parts")
    saved = []
    for file in files:
        if not is_audio_file(file.filename) and not is_video_file(file.filename):
            raise HTTPException(status_code=400,
                                detail=f"'{file.filename}' audio file nahi lagti.")
        path = os.path.join(parts_dir, os.path.basename(file.filename))
        save_upload(file, path)
        saved.append(path)

    if order == "natural":
        saved.sort(key=natural_sort_key)

    output_path = os.path.join(session_dir(session_id), "voice_joined.m4a")
    try:
        result = concat_audio_parts(saved, output_path, parts_dir,
                                    gap_seconds=max(float(gap_seconds or 0), 0))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice parts jodne mein error: {e}")

    session["voice_file"] = result["output_path"]
    session["voice_parts"] = result["parts"]
    session["voice_duration"] = result["total_duration"]
    return {"status": "ok", **result}


@app.post("/upload/music/{session_id}")
async def upload_music(session_id: str, file: UploadFile = File(...)):
    session = get_session(session_id)
    path = os.path.join(session_dir(session_id), f"music_{file.filename}")
    save_upload(file, path)
    session["music_file"] = path
    return {"status": "ok", "message": f"Music file save ho gayi: {file.filename}",
            "duration": round(probe_duration(path), 2)}


@app.delete("/upload/music/{session_id}")
def remove_music(session_id: str):
    session = get_session(session_id)
    session["music_file"] = None
    return {"status": "ok"}


# ----------------------------------------------------------------------------
# Timing — 5 tareeke: file upload / PASTE BOX / sentence-grouping /
#          scene-mapping / MANUAL TIMING TABLE
# ----------------------------------------------------------------------------

def _ingest_timestamps(session: dict, filename: str, raw_text: str) -> dict:
    try:
        segments = parse_timestamp_file(filename, raw_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Timestamp data parse nahi ho saka: {e}")
    if not segments:
        raise HTTPException(status_code=400, detail="Koi segment nahi mila — file ka format check karein.")

    raw_words = extract_raw_words(filename, raw_text)
    session["raw_words"] = raw_words
    session["segments"] = segments
    session["timing_source"] = "file" if filename else "paste"

    sample = " ".join((s.get("text") or "") for s in segments[:20])
    return {
        "status": "ok",
        "segment_count": len(segments),
        "segments": segments,
        "scene_mapping_available": raw_words is not None,
        "detected_script": detect_script(sample),
    }


@app.post("/upload/timestamps/{session_id}")
async def upload_timestamps(session_id: str, file: UploadFile = File(...)):
    """Timestamp file (.srt / word-level .json) upload aur parse."""
    session = get_session(session_id)
    raw_bytes = await file.read()
    try:
        raw_text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File UTF-8 text format mein honi chahiye.")
    return _ingest_timestamps(session, file.filename, raw_text)


@app.post("/timestamps/paste/{session_id}")
def paste_timestamps(session_id: str,
                     content: str = Body(..., embed=True),
                     format_hint: str = Body("auto", embed=True)):
    """
    SCRIPT / TIMESTAMP PASTE BOX — file banane ki zaroorat nahi, seedha
    text paste kar do (SRT ya word-level JSON dono chal jate hain).
    format_hint: "auto" | "srt" | "json"
    """
    session = get_session(session_id)
    text = (content or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Paste box khali hai.")

    if format_hint == "srt":
        pseudo_name = "pasted.srt"
    elif format_hint == "json":
        pseudo_name = "pasted.json"
    else:
        pseudo_name = "pasted.json" if text.lstrip().startswith(("{", "[")) else "pasted.srt"

    result = _ingest_timestamps(session, pseudo_name, text)
    session["timing_source"] = "paste"
    return result


@app.post("/timestamps/manual/{session_id}")
def manual_timing_table(session_id: str,
                        rows: list = Body(..., embed=True),
                        mode: str = Body("start_end", embed=True)):
    """
    MANUAL TIMING TABLE — teesra timing option (Scene-Mapping aur
    Sentence-Grouping ke saath). User khud table mein rows deta hai.

    mode = "start_end"  -> rows: [{"start": 0, "end": 3.5, "text": "..."}]
    mode = "duration"   -> rows: [{"duration": 3.5, "text": "..."}]
                           (start times khud calculate ho jate hain — sabse asaan)
    """
    session = get_session(session_id)
    if not rows:
        raise HTTPException(status_code=400, detail="Table khali hai — kam se kam 1 row chahiye.")

    if mode == "duration":
        built = []
        cursor = 0.0
        for row in rows:
            try:
                dur = float(row.get("duration", 0))
            except (TypeError, ValueError):
                dur = 0.0
            if dur <= 0:
                continue
            built.append({"start": cursor, "end": cursor + dur, "text": row.get("text", "")})
            cursor += dur
        segments = sanitize_segments(built)
    else:
        segments = sanitize_segments(rows)

    if not segments:
        raise HTTPException(status_code=400,
                            detail="Koi valid row nahi mili (end, start se bada hona chahiye).")

    # Overlap check — user ko batate hain, magar reject nahi karte
    overlaps = []
    for i in range(1, len(segments)):
        if segments[i]["start"] < segments[i - 1]["end"] - 0.001:
            overlaps.append(i + 1)

    voice_duration = session.get("voice_duration") or 0.0
    timeline = segments[-1]["end"] if segments else 0.0

    session["segments"] = segments
    session["timing_source"] = "manual_table"
    return {
        "status": "ok",
        "segments": segments,
        "segment_count": len(segments),
        "overlapping_rows": overlaps,
        "timeline_duration": round(timeline, 2),
        "voice_duration": round(voice_duration, 2),
        "voice_mismatch": bool(voice_duration and abs(timeline - voice_duration) > 1.0),
    }


@app.post("/timestamps/regroup/{session_id}")
def regroup_by_sentences(session_id: str, sentences_per_group: int = Body(1, embed=True)):
    """Sentence-Grouping: N sentences milkar 1 scene (har language mein chalta hai)."""
    session = get_session(session_id)
    raw_words = session.get("raw_words")
    if not raw_words:
        raise HTTPException(status_code=400,
                            detail="Sentence-Grouping ke liye word-level JSON zaroori hai (SRT se nahi chalega).")

    segments = group_words_by_sentences(raw_words, sentences_per_group)
    if not segments:
        raise HTTPException(status_code=400,
                            detail="Sentences detect nahi hui. Text mein punctuation (. ! ? 。 ۔ ।) check karein.")

    session["segments"] = segments
    session["timing_source"] = "sentence_grouping"
    return {"status": "ok", "segments": segments, "segment_count": len(segments),
            "sentence_count": count_sentences(raw_words)}


@app.get("/scenes/info/{session_id}")
def scene_info(session_id: str):
    """
    UI ke live hint ke liye: is voice/script mein kitne sentences bane, aur
    "N sentences = 1 scene" ke different options par kitne scenes banenge.
    """
    session = get_session(session_id)
    raw_words = session.get("raw_words")
    if not raw_words:
        return {"status": "ok", "has_word_level": False, "sentence_count": 0, "preview": {}}
    total = count_sentences(raw_words)
    preview = {str(n): (total + n - 1) // n for n in (1, 2, 3, 4, 5) if total}
    return {
        "status": "ok",
        "has_word_level": True,
        "sentence_count": total,
        "preview": preview,
        "media_count": len([s for s in (session.get("segments") or []) if s.get("media")]),
    }


def _apply_scene_table(session: dict, raw_text: str) -> dict:
    """Scene time table (scene number + start + end) se seedha segments banata hai."""
    try:
        rows, row_errors = parse_scene_time_table(raw_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    segments, warnings = scene_table_to_segments(rows, session.get("raw_words"))
    segments = sanitize_segments(segments)
    if not segments:
        raise HTTPException(status_code=400,
                            detail="Koi valid scene row nahi mili (end, start se bada hona chahiye).")

    voice_duration = session.get("voice_duration") or 0.0
    timeline = segments[-1]["end"]
    session["segments"] = segments
    session["timing_source"] = "scene_table"
    return {
        "status": "ok",
        "segments": segments,
        "segment_count": len(segments),
        "skipped_rows": row_errors[:20],
        "skipped_count": len(row_errors),
        "warnings": warnings[:20],
        "timeline_duration": round(timeline, 2),
        "voice_duration": round(voice_duration, 2),
        "voice_mismatch": bool(voice_duration and abs(timeline - voice_duration) > 1.0),
    }


@app.post("/scenes/table/paste/{session_id}")
def paste_scene_table(session_id: str, content: str = Body(..., embed=True)):
    """
    Scene time table PASTE — sabse tez rasta (200-300 scenes bhi).
    Excel/Sheets se rows copy karke seedha paste: scene, start, end
    (tab / comma / semicolon / pipe se alag; time 12.5 ya 00:04.5 ya 00:01:20.5).
    Word-level JSON ki zarurat NAHI — timing aap de rahe hain.
    """
    session = get_session(session_id)
    if not (content or "").strip():
        raise HTTPException(status_code=400, detail="Paste box khali hai.")
    return _apply_scene_table(session, content)


@app.post("/upload/scenetable/{session_id}")
async def upload_scene_table(session_id: str, file: UploadFile = File(...)):
    """Scene time table file (.csv / .tsv / .txt) upload."""
    session = get_session(session_id)
    raw_bytes = await file.read()
    try:
        raw_text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            raw_text = raw_bytes.decode("utf-16")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File UTF-8 (ya UTF-16) text format mein honi chahiye.")
    return _apply_scene_table(session, raw_text)


def _apply_scene_map(session: dict, raw_text: str) -> dict:
    raw_words = session.get("raw_words")
    if not raw_words:
        raise HTTPException(status_code=400,
                            detail="Scene-Mapping ke liye word-level JSON timestamp zaroori hai.")
    try:
        scenes = parse_scene_file(raw_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Scene file parse nahi ho saki: {e}")
    if not scenes:
        raise HTTPException(status_code=400, detail="Koi 'Scene N:' block nahi mila.")

    matched = match_scenes_to_timestamps(scenes, raw_words)
    new_segments = [
        {"start": m["start"], "end": m["end"], "text": m["text"], "scene_number": m["scene_number"]}
        for m in matched
    ]
    session["segments"] = new_segments
    session["timing_source"] = "scene_mapping"
    low_confidence = [m for m in matched if m["match_confidence"] < 0.7 or m.get("low_confidence")]
    return {
        "status": "ok",
        "segments": new_segments,
        "match_details": matched,
        "segment_count": len(new_segments),
        "low_confidence_count": len(low_confidence),
        "low_confidence_scenes": [m["scene_number"] for m in low_confidence][:20],
    }


@app.post("/upload/scenemap/{session_id}")
async def upload_scene_map(session_id: str, file: UploadFile = File(...)):
    """Scene-Mapping file (Scene N + narration text) se EXACT timing nikalta hai."""
    session = get_session(session_id)
    raw_bytes = await file.read()
    try:
        raw_text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File UTF-8 text format mein honi chahiye.")
    return _apply_scene_map(session, raw_text)


@app.post("/scenemap/paste/{session_id}")
def paste_scene_map(session_id: str, content: str = Body(..., embed=True)):
    """Scene-Mapping ko bhi seedha paste kiya ja sakta hai (paste box)."""
    session = get_session(session_id)
    if not (content or "").strip():
        raise HTTPException(status_code=400, detail="Paste box khali hai.")
    return _apply_scene_map(session, content)


@app.post("/segments/update/{session_id}")
def update_segments(session_id: str, segments: list = Body(..., embed=True)):
    """
    Timeline editor: user segments ka text/timing/effect edit kar sakta hai
    (media assignment safe rehti hai).
    """
    session = get_session(session_id)
    old = session.get("segments") or []
    updated = []
    for i, item in enumerate(segments or []):
        try:
            start = float(item.get("start", 0))
            end = float(item.get("end", 0))
        except (TypeError, ValueError):
            continue
        if end <= start:
            continue
        base = dict(old[i]) if i < len(old) else {}
        base.update({"start": round(start, 3), "end": round(end, 3),
                     "text": (item.get("text") or base.get("text") or "")})
        if item.get("effect"):
            base["effect"] = item["effect"]
        if "media" in item and item["media"]:
            base["media"] = item["media"]
        updated.append(base)

    if not updated:
        raise HTTPException(status_code=400, detail="Koi valid segment nahi mila.")
    session["segments"] = updated
    return {"status": "ok", "segments": updated, "segment_count": len(updated)}


# ----------------------------------------------------------------------------
# AI Voice Studio & Emotion Tags Engine (Edge-TTS, Voice Cloning & Timeline Sync)
# ----------------------------------------------------------------------------

@app.get("/tts/voices")
async def get_tts_voices():
    """Returns curated featured voices, scenario templates, emotion tags, and all available voices."""
    featured = tts_engine.FEATURED_VOICES
    scenarios = tts_engine.SCENARIO_TEMPLATES
    emotion_tags = tts_engine.EMOTION_TAGS
    all_voices = await tts_engine.list_all_available_voices()
    return {
        "status": "ok",
        "available": tts_engine.EDGE_TTS_AVAILABLE,
        "featured": featured,
        "all_voices": all_voices,
        "scenarios": scenarios,
        "emotion_tags": emotion_tags
    }


@app.get("/tts/progress/{job_id}")
async def get_tts_progress(job_id: str):
    """Returns live percentage (0-100%), stage status, and completed payload."""
    return tts_engine.get_job_progress(job_id)


@app.post("/tts/generate")
async def generate_tts(request: Request,
                       text: str = Body(..., embed=True),
                       voice: str = Body("ur-PK-AsadNeural", embed=True),
                       speed: float = Body(1.0, embed=True),
                       pitch: int = Body(0, embed=True),
                       session_id: Optional[str] = Body(None, embed=True),
                       job_id: Optional[str] = Body(None, embed=True)):
    """Generates speech via Edge-TTS and returns audio URL + word-level timestamps."""
    clean = (text or "").strip()
    if not clean:
        raise HTTPException(status_code=400, detail="Script text cannot be empty.")

    target_session = session_id if (session_id and session_id in SESSIONS) else None
    if target_session:
        out_dir = session_dir(target_session, "tts")
    else:
        out_dir = os.path.join(UPLOAD_DIR, "tts_cache")
    os.makedirs(out_dir, exist_ok=True)

    try:
        result = await tts_engine.synthesize_speech(
            text=clean,
            voice=voice,
            speed=float(speed or 1.0),
            pitch=int(pitch or 0),
            output_dir=out_dir,
            job_id=job_id
        )
    except Exception as e:
        if job_id:
            tts_engine.set_job_progress(job_id, 0, "error", f"Generation Error: {str(e)}", is_done=True, error=str(e))
        raise HTTPException(status_code=500, detail=f"TTS Generation Error: {str(e)}")

    if target_session:
        audio_url = file_url(request, target_session, "tts", result["audio_filename"])
    else:
        audio_url = f"{base_url(request)}/files/tts_cache/{result['audio_filename']}"

    response_payload = {
        "status": "ok",
        "job_id": result.get("job_id", job_id),
        "audio_url": audio_url,
        "audio_filename": result["audio_filename"],
        "audio_path": result["audio_path"],
        "duration": result["duration"],
        "words": result["words"],
        "word_count": len(result["words"]),
        "srt_filename": result["srt_filename"],
        "srt_path": result["srt_path"],
        "clean_text": result["clean_text"],
        "chunks_count": result.get("chunks_count", 1),
        "session_id": target_session
    }
    return response_payload


@app.post("/tts/send-to-project/{session_id}")
async def send_tts_to_project(session_id: str,
                              audio_path: str = Body(..., embed=True),
                              srt_path: Optional[str] = Body(None, embed=True)):
    """Transfers generated voiceover and word-level timestamps directly to Video Studio Timeline."""
    session = get_session(session_id)
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found on server.")

    duration = probe_duration(audio_path)
    session["voice_file"] = audio_path
    session["voice_parts"] = []
    session["voice_duration"] = duration

    if srt_path and os.path.exists(srt_path):
        with open(srt_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        _ingest_timestamps(session, os.path.basename(srt_path), raw_text)

    return {
        "status": "ok",
        "message": "AI Voice & word timestamps successfully attached to Video Studio Timeline!",
        "duration": round(duration, 2),
        "segment_count": len(session.get("segments") or []),
        "has_voice": True
    }


@app.post("/tts/clone-sample/{session_id}")
async def upload_clone_sample(session_id: str, file: UploadFile = File(...)):
    """Uploads a 10-30s audio recording to create a Voice Cloning profile."""
    session = get_session(session_id)
    if not is_audio_file(file.filename):
        raise HTTPException(status_code=400, detail="Audio file (.mp3 / .wav / .m4a) zaroori hai.")

    clone_dir = session_dir(session_id, "voice_clones")
    sample_path = os.path.join(clone_dir, f"sample_{file.filename}")
    save_upload(file, sample_path)

    dur = probe_duration(sample_path)
    return {
        "status": "ok",
        "message": f"Voice sample saved: {file.filename}",
        "sample_path": sample_path,
        "filename": file.filename,
        "duration": round(dur, 2)
    }


# ----------------------------------------------------------------------------
# Kokoro-82M Studio HD Voices Endpoints (100% Free, Zero API Keys)
# ----------------------------------------------------------------------------

@app.get("/tts/kokoro/voices")
async def get_kokoro_voices():
    """Returns all 12 language boxes and curated premium voices routed to top engines."""
    try:
        from backend import premium_catalog, kokoro_engine
    except ImportError:
        import premium_catalog, kokoro_engine
    return {
        "status": "ok",
        "languages": premium_catalog.get_all_languages(),
        "voices": premium_catalog.PREMIUM_VOICES,
        "is_installed": kokoro_engine.is_kokoro_installed(),
        "is_model_ready": kokoro_engine.is_kokoro_model_ready()
    }


@app.post("/tts/kokoro/generate")
async def generate_kokoro(request: Request,
                          text: str = Body(..., embed=True),
                          voice: str = Body("am_adam", embed=True),
                          speed: float = Body(1.0, embed=True),
                          pitch: int = Body(0, embed=True),
                          emotion: Optional[str] = Body(None, embed=True),
                          session_id: Optional[str] = Body(None, embed=True)):
    """Generates studio-grade speech via the best engine for the selected voice."""
    clean = (text or "").strip()
    if not clean:
        raise HTTPException(status_code=400, detail="Script text cannot be empty.")

    target_session = session_id if (session_id and session_id in SESSIONS) else None
    if target_session:
        out_dir = session_dir(target_session, "tts")
    else:
        out_dir = os.path.join(UPLOAD_DIR, "tts_cache")
    os.makedirs(out_dir, exist_ok=True)

    try:
        from backend import premium_catalog
    except ImportError:
        import premium_catalog

    v_meta = premium_catalog.find_premium_voice(voice)
    is_kokoro = (v_meta and v_meta.get("engine") == "kokoro") or voice.startswith(("af_", "am_", "bf_", "bm_", "hf_", "hm_", "jf_", "jm_", "zf_", "zm_", "ef_", "em_", "ff_", "if_", "pf_")) or voice in ("af",)

    try:
        if is_kokoro:
            try:
                from backend import kokoro_engine
            except ImportError:
                import kokoro_engine
            res = await kokoro_engine.synthesize_kokoro_speech(
                text=clean,
                voice_id=voice,
                speed=float(speed or 1.0),
                output_dir=out_dir
            )
        else:
            try:
                from backend import tts_engine
            except ImportError:
                import tts_engine
            res = await tts_engine.synthesize_speech(
                text=clean,
                voice=voice,
                speed=float(speed or 1.0),
                pitch=int(pitch or 0),
                output_dir=out_dir,
                file_prefix="premium_studio"
            )
            res["engine"] = (v_meta and v_meta.get("engine_badge")) or "Master Studio HD"
            res["voice"] = voice
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Studio generation error: {str(e)}")

    if target_session:
        audio_url = file_url(request, target_session, "tts", res["audio_filename"])
    else:
        audio_url = f"{base_url(request)}/files/tts_cache/{res['audio_filename']}"

    return {
        "status": "ok",
        "engine": res.get("engine", "Studio HD Voice"),
        "audio_url": audio_url,
        "audio_filename": res["audio_filename"],
        "audio_path": res["audio_path"],
        "duration": res["duration"],
        "words": res.get("words", []),
        "word_count": len(res.get("words", [])),
        "srt_filename": res.get("srt_filename"),
        "srt_path": res.get("srt_path"),
        "clean_text": res.get("clean_text", clean),
        "session_id": target_session
    }


# ----------------------------------------------------------------------------
# F5-TTS Flow-Matching Voice Cloning Endpoints
# ----------------------------------------------------------------------------

@app.post("/tts/f5/clone")
async def clone_voice_f5(request: Request,
                         text: str = Body(..., embed=True),
                         sample_filename: Optional[str] = Body(None, embed=True),
                         speed: float = Body(1.0, embed=True),
                         session_id: Optional[str] = Body(None, embed=True)):
    """Clones voice using F5-TTS Flow Matching from uploaded sample."""
    clean = (text or "").strip()
    if not clean:
        raise HTTPException(status_code=400, detail="Script text cannot be empty.")

    target_session = session_id if (session_id and session_id in SESSIONS) else None
    if target_session:
        out_dir = session_dir(target_session, "tts")
        clone_dir = session_dir(target_session, "voice_clones")
    else:
        out_dir = os.path.join(UPLOAD_DIR, "tts_cache")
        clone_dir = out_dir
    os.makedirs(out_dir, exist_ok=True)

    # Locate uploaded sample
    sample_path = ""
    if sample_filename:
        p = os.path.join(clone_dir, sample_filename)
        if os.path.exists(p):
            sample_path = p
        else:
            p2 = os.path.join(clone_dir, f"sample_{sample_filename}")
            if os.path.exists(p2):
                sample_path = p2

    if not sample_path and os.path.exists(clone_dir):
        files = [os.path.join(clone_dir, f) for f in os.listdir(clone_dir) if is_audio_file(f)]
        if files:
            sample_path = files[-1]

    import f5tts_engine
    try:
        res = await f5tts_engine.synthesize_f5_clone(
            sample_path=sample_path,
            script_text=clean,
            speed=float(speed or 1.0),
            output_dir=out_dir
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"F5-TTS cloning error: {str(e)}")

    if target_session:
        audio_url = file_url(request, target_session, "tts", res["audio_filename"])
    else:
        audio_url = f"{base_url(request)}/files/tts_cache/{res['audio_filename']}"

    return {
        "status": "ok",
        "engine": "F5-TTS Flow-Matching",
        "audio_url": audio_url,
        "audio_filename": res["audio_filename"],
        "audio_path": res["audio_path"],
        "duration": res["duration"],
        "words": res["words"],
        "word_count": len(res["words"]),
        "srt_filename": res["srt_filename"],
        "srt_path": res["srt_path"],
        "clean_text": res["clean_text"],
        "session_id": target_session
    }



def sync_segments_to_voice(segments: list, voice_duration: float) -> list:
    """
    Timeline segments aur voice audio ko exact sync aur same duration ka banata hai:
    1. Pehle segment ka start 0.0 karta hai agar shuru mein chhota silence ho
    2. Consecutive segments ke darmiyan speech pauses / khamoshi ko seamlessly
       agli clip tak extend karta hai (taake beech mein koi dropped frame na ho aur video-audio sync rahe)
    3. Aakhiri segment ko voice_duration ke end tak extend karta hai
    Is se sum(end - start) bilkul voice_duration ke barabar ho jata hai.
    """
    if not segments or voice_duration <= 0:
        return segments

    # 1. Start from 0.0
    if float(segments[0].get("start", 0)) > 0:
        segments[0]["start"] = 0.0

    # 2. Close gaps between consecutive segments
    for i in range(len(segments) - 1):
        next_start = float(segments[i + 1].get("start", 0))
        curr_end = float(segments[i].get("end", 0))
        if next_start > curr_end:
            segments[i]["end"] = round(next_start, 2)

    # 3. Match the final segment to voice_duration
    segments[-1]["end"] = round(float(voice_duration), 2)

    # 4. In case of any slight float rounding difference:
    total_dur = sum(float(s.get("end", 0)) - float(s.get("start", 0)) for s in segments)
    rem = round(voice_duration - total_dur, 2)
    if rem > 0.01:
        segments[-1]["end"] = round(float(segments[-1]["end"]) + rem, 2)

    return segments


@app.post("/timeline/match-voice/{session_id}")
def match_timeline_to_voice(session_id: str):
    """
    Agar voice ki length timeline se zyada ho, to internal silence gaps ko
    close karta hai aur aakhiri segment ko voice ke barabar extend kar deta hai.
    Isse voice aakhir mein cut nahi hoti aur timeline exact voice ke barabar ho jati hai.
    """
    session = get_session(session_id)
    segments = session.get("segments")
    if not segments:
        raise HTTPException(status_code=400, detail="Pehle timing / segments set karein.")

    voice_path = session.get("voice_file")
    voice_dur = session.get("voice_duration") or 0.0
    if not voice_dur and voice_path and os.path.exists(voice_path):
        voice_dur = probe_duration(voice_path)
        session["voice_duration"] = voice_dur

    if not voice_dur or voice_dur <= 0:
        raise HTTPException(status_code=400, detail="Voice file ki duration nahi mil saki.")

    segments = sync_segments_to_voice(segments, voice_dur)
    session["segments"] = segments

    width, height = va.get_dimensions(session.get("aspect_ratio", "9:16"), session.get("resolution", "1080p"))
    validation = validate_segments(segments, resolve_media_path,
                                   target_width=width, target_height=height,
                                   voice_duration=voice_dur)
    session["last_validation"] = validation

    return {
        "status": "ok",
        "segments": segments,
        "timeline_duration": round(voice_dur, 2),
        "voice_duration": round(voice_dur, 2),
        "validation": validation,
    }


# ----------------------------------------------------------------------------
# Media (manual upload / zip import / assign / validate)
# ----------------------------------------------------------------------------

def _auto_assign(session: dict, uploaded: list, provider: str) -> int:
    segments = session.get("segments") or []
    if not segments:
        return 0
    updated = list(segments)
    count = 0
    for item in uploaded:
        seg_num = item.get("segment_number")
        if seg_num is not None and 1 <= seg_num <= len(updated):
            idx = seg_num - 1
            updated[idx] = {**updated[idx], "media": {
                "type": item["type"],
                "thumbnail": item["url"],
                "full_url": item["url"],
                "local_path": item.get("local_path"),
                "source_page": None,
                "provider": provider,
            }}
            count += 1
    session["segments"] = updated
    return count


@app.post("/media/manual/{session_id}")
async def upload_manual_media(session_id: str, request: Request,
                              files: list[UploadFile] = File(...)):
    """
    Manual Mode: user apni images/videos upload karta hai (bulk ya ek-ek).
    Filename mein number ho ('1_beach.jpg', 'scene3.mp4') to seedha us segment
    se auto-assign ho jata hai.
    """
    session = get_session(session_id)
    media_dir = session_dir(session_id, "manual_media")

    uploaded = []
    for file in files:
        safe_name = f"{uuid.uuid4().hex[:6]}_{os.path.basename(file.filename)}"
        path = os.path.join(media_dir, safe_name)
        save_upload(file, path)
        is_vid = (file.content_type or "").startswith("video") or is_video_file(file.filename)
        uploaded.append({
            "filename": file.filename,
            "url": file_url(request, session_id, "manual_media", safe_name),
            "local_path": path,
            "type": "video" if is_vid else "photo",
            "segment_number": extract_segment_number(file.filename),
        })

    session["manual_media"] = (session.get("manual_media") or []) + uploaded
    auto_assigned = _auto_assign(session, uploaded, "manual")

    return {
        "status": "ok",
        "uploaded": uploaded,
        "all_manual_media": session["manual_media"],
        "auto_assigned_count": auto_assigned,
        "segments": session.get("segments") or [],
    }


@app.post("/media/manual/{session_id}/import-zip")
async def import_zip_media(session_id: str, request: Request, file: UploadFile = File(...)):
    """Zip (jaise B-Roll Finder Pro output) se bulk media import + auto-assign."""
    session = get_session(session_id)
    if not session.get("segments"):
        raise HTTPException(status_code=400, detail="Pehle timing (timestamp/manual table) set karein.")

    media_dir = session_dir(session_id, "manual_media")
    zip_path = os.path.join(media_dir, f"import_{uuid.uuid4().hex[:6]}.zip")
    save_upload(file, zip_path)

    try:
        extracted = extract_zip(zip_path, media_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Zip kholne mein error: {e}")
    finally:
        try:
            os.remove(zip_path)
        except OSError:
            pass

    if not extracted:
        raise HTTPException(status_code=400, detail="Zip mein koi valid image/video nahi mili.")

    uploaded = []
    for item in extracted:
        uploaded.append({
            "filename": item["filename"],
            "url": file_url(request, session_id, "manual_media", os.path.basename(item["local_path"])),
            "local_path": item["local_path"],
            "type": item["type"],
            "segment_number": item["segment_number"],
        })

    session["manual_media"] = (session.get("manual_media") or []) + uploaded
    auto_assigned = _auto_assign(session, uploaded, "zip_import")

    return {
        "status": "ok",
        "uploaded": uploaded,
        "all_manual_media": session["manual_media"],
        "auto_assigned_count": auto_assigned,
        "segments": session.get("segments") or [],
    }


@app.post("/media/manual/{session_id}/assign")
def assign_manual_media(session_id: str, assignments: dict = Body(...)):
    """
    assignments: {"0": "<media url>", "1": null, ...}
    null bhejne se us segment ki media hat jati hai.
    """
    session = get_session(session_id)
    segments = session.get("segments")
    if not segments:
        raise HTTPException(status_code=400, detail="Pehle timing set karein.")

    by_url = {m["url"]: m for m in (session.get("manual_media") or [])}
    updated = []
    for i, seg in enumerate(segments):
        key = str(i)
        if key in assignments:
            url = assignments[key]
            if not url:
                seg = {k: v for k, v in seg.items() if k != "media"}
            elif url in by_url:
                m = by_url[url]
                seg = {**seg, "media": {
                    "type": m["type"], "thumbnail": m["url"], "full_url": m["url"],
                    "local_path": m.get("local_path"), "source_page": None,
                    "provider": "manual",
                }}
        updated.append(seg)

    session["segments"] = updated
    return {"status": "ok", "segments": updated}


@app.post("/media/validate/{session_id}")
def validate_media(session_id: str,
                   aspect_ratio: str = Body("9:16", embed=True),
                   resolution: str = Body("1080p", embed=True)):
    """
    MEDIA MISMATCH FLAGGING — render se PEHLE har segment ki media check karta
    hai: media missing, file gayab, unreadable, duplicate, bohot chhoti video,
    low resolution, aspect mismatch, low fps, timeline-vs-voice mismatch.
    """
    session = get_session(session_id)
    segments = session.get("segments")
    if not segments:
        raise HTTPException(status_code=400, detail="Pehle timing set karein.")

    width, height = va.get_dimensions(aspect_ratio, resolution)
    voice_duration = session.get("voice_duration") or 0.0
    if not voice_duration and session.get("voice_file"):
        voice_duration = probe_duration(session["voice_file"])
        session["voice_duration"] = voice_duration

    report = validate_segments(segments, resolve_media_path,
                               target_width=width, target_height=height,
                               voice_duration=voice_duration)
    session["last_validation"] = report
    return report


@app.post("/overlay/image/{session_id}")
async def upload_overlay_image(session_id: str, request: Request, file: UploadFile = File(...)):
    """
    Custom sticker / logo / watermark image upload — built-in stickers ke
    ilawa user apni PNG bhi laga sakta hai.
    """
    session = get_session(session_id)
    overlay_dir = session_dir(session_id, "overlays")
    safe_name = f"{uuid.uuid4().hex[:6]}_{os.path.basename(file.filename)}"
    path = os.path.join(overlay_dir, safe_name)
    save_upload(file, path)

    item = {
        "filename": file.filename,
        "local_path": path,
        "url": file_url(request, session_id, "overlays", safe_name),
    }
    session["custom_sticker_images"] = (session.get("custom_sticker_images") or []) + [item]
    return {"status": "ok", "image": item,
            "all_images": session["custom_sticker_images"]}


@app.post("/upload/font/{session_id}")
async def upload_caption_font(session_id: str, file: UploadFile = File(...)):
    """
    Custom caption font (.ttf/.otf/.ttc). File ko render folder mein rakhte hain
    kyunki libass wahin se `fontsdir` uthata hai — yani font system mein install
    hone ki zaroorat nahi. Wapas milta hua `font_name` captions.custom_font_name
    mein bhejna hota hai.
    """
    session = get_session(session_id)
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".ttf", ".otf", ".ttc"):
        raise HTTPException(status_code=400, detail="Sirf .ttf, .otf ya .ttc font file chalegi.")

    render_dir = session_dir(session_id, "render")
    safe_name = os.path.basename(file.filename)
    path = os.path.join(render_dir, safe_name)
    save_upload(file, path)

    font_name = os.path.splitext(safe_name)[0].replace("_", " ").replace("-", " ").strip()
    session["custom_font_file"] = path
    session["custom_font_name"] = font_name
    return {"status": "ok", "font_name": font_name, "filename": safe_name}


# ----------------------------------------------------------------------------
# Render (live dashboard + cancel)
# ----------------------------------------------------------------------------

def _log(state: dict, message: str):
    state["log"].append({"t": round(time.time() - state["started_at"], 1), "message": message})
    if len(state["log"]) > MAX_LOG_LINES:
        del state["log"][:-MAX_LOG_LINES]


@app.post("/render/{session_id}")
def render_video(
    session_id: str,
    request: Request,
    effect: str = Body("zoom_in_slow"),
    music_volume: float = Body(0.2),
    audio_ducking: bool = Body(False),
    music_fade_in_out: bool = Body(True),
    transition: str = Body("cut"),
    transition_speed: str = Body("medium"),
    captions: dict = Body(None),
    color_filter: str = Body("none"),
    stickers: list = Body(None),
    custom_texts: list = Body(None),
    video_audio_mode: str = Body("mute"),
    video_audio_volume: float = Body(0.4),
    video_trim_mode: str = Body("end"),
    aspect_ratio: str = Body("9:16"),
    resolution: str = Body("1080p"),
    sound_effects: list = Body(None),
    smart_trigger_enabled: bool = Body(False),
    cleanup_temp: bool = Body(True),
    skip_validation: bool = Body(False),
):
    """
    Render background thread mein shuru karta hai aur turant return karta hai.
    Live progress /render/status/{sid} se milti hai (stages + percent + ETA + log).
    """
    session = get_session(session_id)

    segments = session.get("segments")
    if not segments:
        raise HTTPException(status_code=400, detail="Pehle timing (timestamps ya manual table) set karein.")

    voice_path = session.get("voice_file")
    if not voice_path or not os.path.exists(voice_path):
        raise HTTPException(status_code=400, detail="Pehle voice file upload karein.")

    # BUG FIX: pehle ek hi session mein do render ek sath chal sakte the aur
    # render_state aapas mein bigad jati thi. Ab per-session lock hai.
    lock = session["render_lock"]
    if not lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Is session ki ek render already chal rahi hai.")

    try:
        width, height = va.get_dimensions(aspect_ratio, resolution)

        # Render se pehle validation — errors ho to render shuru hi nahi karte
        validation = None
        if not skip_validation:
            validation = validate_segments(segments, resolve_media_path,
                                           target_width=width, target_height=height,
                                           voice_duration=session.get("voice_duration") or 0.0)
            if not validation["summary"]["ready"]:
                lock.release()
                return {
                    "status": "blocked",
                    "message": "Render se pehle kuch errors theek karne honge.",
                    "validation": validation,
                }

        music_path = session.get("music_file")
        raw_words = session.get("raw_words")
        work_dir = os.path.join(UPLOAD_DIR, session_id, "render")

        final_stickers = list(stickers) if stickers else []
        if smart_trigger_enabled and raw_words:
            final_stickers += detect_sticker_triggers(raw_words)

        # Custom sticker images: frontend url bhejta hai, hum local path resolve karte hain
        for sticker in final_stickers:
            if sticker.get("custom_url") and not sticker.get("custom_path"):
                sticker["custom_path"] = url_to_local_path(sticker["custom_url"])

        cancel_event = threading.Event()
        session["cancel_event"] = cancel_event

        plan = va.stage_plan(
            has_transition=transition not in ("cut", "fade") and len(segments) > 1,
            has_filter=bool(color_filter and color_filter != "none"),
            has_captions=bool(captions and captions.get("enabled")),
            has_overlays=bool(final_stickers or custom_texts),
            has_music=bool(music_path and os.path.exists(music_path)),
            has_sfx=bool(sound_effects),
        )

        state = {
            "status": "processing",
            "percent": 0.0,
            "stage": "clips",
            "stages": [s["key"] for s in plan],
            "completed_stages": [],
            "message": "Shuru ho raha hai...",
            "segment_index": None,
            "total_segments": len(segments),
            "elapsed": 0.0,
            "eta": None,
            "started_at": time.time(),
            "log": [],
            "download_url": None,
            "error": None,
            "validation": validation,
            "settings": {
                "aspect_ratio": aspect_ratio, "resolution": resolution,
                "transition": transition, "effect": effect,
            },
        }
        session["render_state"] = state
        _log(state, "Render shuru — settings taiyar.")
        if captions and captions.get("enabled"):
            has_text = any(bool((s.get("text") or "").strip()) for s in segments) or bool(raw_words)
            if not has_text:
                _log(state, "⚠️ Note: Captions enabled hain magar segments mein text nahi mila.")

        def progress_callback(payload: dict):
            prev_stage = state.get("stage")
            state.update({
                "percent": payload.get("percent", state["percent"]),
                "stage": payload.get("stage", state["stage"]),
                "message": payload.get("message", ""),
                "segment_index": payload.get("segment_index"),
                "elapsed": payload.get("elapsed"),
                "eta": payload.get("eta"),
            })
            if prev_stage and prev_stage != payload.get("stage"):
                if prev_stage not in state["completed_stages"]:
                    state["completed_stages"].append(prev_stage)
            msg = payload.get("message")
            if msg and (not state["log"] or state["log"][-1]["message"] != msg):
                _log(state, msg)

        def run_render():
            va.set_cancel_event(cancel_event)
            try:
                final_path = assemble_video(
                    segments, voice_path, work_dir, default_effect=effect,
                    music_path=music_path, music_volume=music_volume,
                    progress_callback=progress_callback,
                    transition=transition, transition_speed=transition_speed,
                    captions=captions, raw_words=raw_words,
                    color_filter=color_filter,
                    stickers=final_stickers, custom_texts=custom_texts,
                    video_audio_mode=video_audio_mode, video_audio_volume=video_audio_volume,
                    video_trim_mode=video_trim_mode,
                    aspect_ratio=aspect_ratio, resolution=resolution,
                    sound_effects=sound_effects, audio_ducking=audio_ducking,
                    music_fade_in_out=music_fade_in_out, cleanup_temp=cleanup_temp,
                )
                session["final_video"] = final_path
                session["settings"] = state["settings"]
                filename = os.path.basename(final_path)
                state.update({
                    "status": "done",
                    "percent": 100.0,
                    "stage": "finalize",
                    "message": "Video ban gayi! ✅",
                    "duration": round(probe_duration(final_path), 2),
                    "size_mb": round(os.path.getsize(final_path) / (1024 * 1024), 2),
                    "download_url": f"{base_url(request)}/files/{session_id}/render/{filename}",
                })
                if "finalize" not in state["completed_stages"]:
                    state["completed_stages"].append("finalize")
                _log(state, "Mukammal ✅")
            except RenderCancelled:
                state.update({"status": "cancelled", "message": "Render cancel ho gayi.",
                              "error": None})
                _log(state, "User ne cancel kiya ❌")
            except Exception as e:
                state.update({"status": "error", "message": "Error aayi.", "error": str(e)})
                _log(state, f"ERROR: {e}")
            finally:
                va.clear_cancel_event()
                session["cancel_event"] = None
                lock.release()

        threading.Thread(target=run_render, daemon=True).start()
        return {"status": "started", "stages": state["stages"], "validation": validation}

    except HTTPException:
        if lock.locked():
            lock.release()
        raise
    except Exception:
        if lock.locked():
            lock.release()
        raise


@app.get("/render/status/{session_id}")
def render_status(session_id: str):
    """Live render status — frontend dashboard isse poll karta hai."""
    session = get_session(session_id)
    state = session.get("render_state")
    if not state:
        return {"status": "idle", "percent": 0.0, "message": "Abhi koi render shuru nahi hui.",
                "log": [], "stages": []}
    if state["status"] == "processing":
        state["elapsed"] = round(time.time() - state["started_at"], 1)
    return state


@app.post("/render/cancel/{session_id}")
def cancel_render(session_id: str):
    """
    Chalti hui render ko rok deta hai (FFmpeg process bhi kill hoti hai).
    Pehle cancel ka koi tareeka nahi tha — 20 minute wait karna padta tha.
    """
    session = get_session(session_id)
    event = session.get("cancel_event")
    if not event:
        raise HTTPException(status_code=400, detail="Koi render chal hi nahi rahi.")
    event.set()
    state = session.get("render_state")
    if state:
        state["message"] = "Cancel ho rahi hai..."
    return {"status": "cancelling"}


@app.post("/render/quick-export/{session_id}")
def quick_export(session_id: str, request: Request,
                 aspect_ratio: str = Body(...), resolution: str = Body(...),
                 fit_mode: str = Body("crop")):
    """
    Already-rendered video ko naye ratio/resolution mein FAST export.
    fit_mode: "crop" (frame bhar jaye, kinare cut) ya "pad" (sab dikhe, black bars).
    """
    session = get_session(session_id)
    final_video = session.get("final_video")
    if not final_video or not os.path.exists(final_video):
        raise HTTPException(status_code=400, detail="Pehle ek video render karein.")

    work_dir = session_dir(session_id, "render")
    filename = f"export_{aspect_ratio.replace(':', 'x')}_{resolution}_{fit_mode}.mp4"
    output_path = os.path.join(work_dir, filename)

    try:
        quick_export_resolution(final_video, output_path, aspect_ratio, resolution, fit_mode=fit_mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export mein error: {e}")

    return {"status": "ok", "filename": filename,
            "size_mb": round(os.path.getsize(output_path) / (1024 * 1024), 2),
            "download_url": f"{base_url(request)}/files/{session_id}/render/{filename}"}


@app.get("/download/{session_id}")
def download_final(session_id: str):
    """Final video ko attachment ki tarah bhejta hai (browser save dialog)."""
    session = get_session(session_id)
    final_video = session.get("final_video")
    if not final_video or not os.path.exists(final_video):
        raise HTTPException(status_code=404, detail="Koi rendered video nahi mili.")
    return FileResponse(final_video, media_type="video/mp4",
                        filename=f"video_{session_id}.mp4")


# ----------------------------------------------------------------------------
# Project save / load  (kaam kabhi zaya na ho — server restart ke baad bhi)
# ----------------------------------------------------------------------------

def _project_payload(session: dict) -> dict:
    """Session se sirf woh cheezein jo JSON mein safe hain (Lock/Event nahi)."""
    return {
        "voice_file": session.get("voice_file"),
        "voice_parts": session.get("voice_parts") or [],
        "voice_duration": session.get("voice_duration") or 0.0,
        "music_file": session.get("music_file"),
        "segments": session.get("segments"),
        "raw_words": session.get("raw_words"),
        "manual_media": session.get("manual_media") or [],
        "custom_sticker_images": session.get("custom_sticker_images") or [],
        "timing_source": session.get("timing_source"),
        "settings": session.get("settings") or {},
    }


@app.post("/project/save/{session_id}")
def project_save(session_id: str, name: str = Body(...), settings: dict = Body(None)):
    """Poora project (segments + media + settings) ek JSON file mein save."""
    session = get_session(session_id)
    if settings:
        session["settings"] = settings

    payload = _project_payload(session)
    try:
        info = project_store.save_project(PROJECTS_DIR, name, payload)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Save nahi ho saka: {e}")

    return {"status": "ok", "message": f"Project '{name}' save ho gaya ✅",
            "name": info["name"], "saved_at": info["saved_at"],
            "segment_count": len(payload.get("segments") or [])}


@app.get("/project/list")
def project_list():
    """Saare saved projects (naye pehle)."""
    return {"projects": project_store.list_projects(PROJECTS_DIR)}


@app.post("/project/load/{session_id}")
def project_load(session_id: str, request: Request, name: str = Body(..., embed=True)):
    """
    Saved project ko is session mein load karta hai. Jo files ab disk par
    maujood nahi, unhein missing report kar dete hain (chup-chaap fail nahi).
    """
    session = get_session(session_id)
    if session.get("render_lock").locked():
        raise HTTPException(status_code=409, detail="Render chal raha hai — pehle rukwaein.")

    try:
        record = project_store.load_project(PROJECTS_DIR, name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Project nahi mila.")
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=400, detail=f"Project file kharab hai: {e}")

    data = record.get("data") or {}
    missing = []

    voice_file = data.get("voice_file")
    if voice_file and not os.path.exists(voice_file):
        missing.append({"kind": "voice", "path": voice_file})
        voice_file = None

    music_file = data.get("music_file")
    if music_file and not os.path.exists(music_file):
        missing.append({"kind": "music", "path": music_file})
        music_file = None

    manual_media = []
    for item in data.get("manual_media") or []:
        local = item.get("local_path")
        if local and not os.path.exists(local):
            missing.append({"kind": "media", "path": local,
                            "filename": item.get("filename")})
            continue
        # URL session-specific hoti hai + host badal sakta hai — dobara banate hain
        if local:
            rel = os.path.relpath(local, UPLOAD_DIR).replace("\\", "/")
            item = dict(item)
            item["full_url"] = f"{base_url(request)}/files/{rel}"
        manual_media.append(item)

    session["voice_file"] = voice_file
    session["voice_parts"] = data.get("voice_parts") or []
    session["voice_duration"] = data.get("voice_duration") or 0.0
    session["music_file"] = music_file
    session["segments"] = data.get("segments")
    session["raw_words"] = data.get("raw_words")
    session["manual_media"] = manual_media
    session["custom_sticker_images"] = data.get("custom_sticker_images") or []
    session["timing_source"] = data.get("timing_source")
    session["settings"] = data.get("settings") or {}

    return {"status": "ok", "message": f"Project '{record.get('name', name)}' load ho gaya ✅",
            "name": record.get("name", name),
            "saved_at": record.get("saved_at"),
            "segments": session["segments"],
            "settings": session["settings"],
            "manual_media": manual_media,
            "voice_duration": session["voice_duration"],
            "has_voice": bool(voice_file),
            "has_music": bool(music_file),
            "missing_files": missing,
            "warning": (f"{len(missing)} file(s) disk par nahi milin — unhein dobara "
                        f"upload karein." if missing else None)}


@app.delete("/project/{name}")
def project_delete(name: str):
    if not project_store.delete_project(PROJECTS_DIR, name):
        raise HTTPException(status_code=404, detail="Project nahi mila.")
    return {"status": "ok", "message": f"Project '{name}' delete ho gaya."}


# ----------------------------------------------------------------------------
# Authentication & Branding Endpoints (Multi-User + Locked Owner Branding)
# ----------------------------------------------------------------------------

@app.post("/auth/signup")
def auth_signup(payload: dict = Body(...)):
    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")
    try:
        res = auth.register_user(name, email, password)
        return {"status": "ok", **res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login")
def auth_login(payload: dict = Body(...)):
    email = payload.get("email")
    password = payload.get("password")
    try:
        res = auth.authenticate_user(email, password)
        return {"status": "ok", **res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/quick-creator")
def auth_quick_creator(payload: dict = Body(...)):
    name = payload.get("name") or "Creator"
    try:
        res = auth.quick_creator_login(name)
        return {"status": "ok", **res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/logout")
def auth_logout(payload: dict = Body({})):
    token = payload.get("token") or ""
    auth.logout_user(token)
    return {"status": "ok", "message": "Logout kamyab."}


@app.get("/")
def root_redirect():
    return RedirectResponse(url="/app/")


@app.get("/auth/me")
def auth_me(request: Request):
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif "token" in request.query_params:
        token = request.query_params["token"]

    user = auth.get_current_user(token)
    has_custom_logo = bool(auth.get_tool_logo_path())
    logo_url = f"{base_url(request)}/branding/logo" if has_custom_logo else None
    branding = auth.get_branding_settings()

    return {
        "status": "ok",
        "user": user,
        "is_authenticated": bool(user),
        "is_owner": bool(user and user.get("role") == "owner"),
        "creator": {
            "name": "Hafiz Muhammad Umar",
            "title": "Creator & Owner",
            "verified": True,
            "locked": True,
        },
        "tool_name": branding.get("tool_name", "Umar AI Video Studio"),
        "logo_url": logo_url,
    }


@app.get("/branding/settings")
def get_branding_settings(request: Request):
    branding = auth.get_branding_settings()
    has_custom_logo = bool(auth.get_tool_logo_path())
    branding["logo_url"] = f"{base_url(request)}/branding/logo" if has_custom_logo else None
    return {"status": "ok", "branding": branding}


@app.post("/branding/settings")
def update_branding_settings(request: Request, payload: dict = Body(...)):
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif "token" in request.query_params:
        token = request.query_params["token"]

    if not auth.is_owner(token):
        raise HTTPException(status_code=403, detail="Sirf tool ke owner (Hafiz Muhammad Umar) settings tabdeel kar sakte hain.")

    updated = auth.save_branding_settings(payload)
    has_custom_logo = bool(auth.get_tool_logo_path())
    updated["logo_url"] = f"{base_url(request)}/branding/logo" if has_custom_logo else None
    return {"status": "ok", "message": "Branding settings update ho gayin! ✅", "branding": updated}


@app.post("/branding/logo")
async def upload_branding_logo(request: Request, file: UploadFile = File(...)):
    # Verify owner permission
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif "token" in request.query_params:
        token = request.query_params["token"]

    if not auth.is_owner(token):
        raise HTTPException(status_code=403, detail="Sirf tool ke owner (Hafiz Muhammad Umar) logo tabdeel kar sakte hain.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Logo file khali hai.")

    auth.save_tool_logo(content, file.filename)
    return {
        "status": "ok",
        "message": "Tool logo kamyabi se upload aur save ho gaya! ✅",
        "logo_url": f"{base_url(request)}/branding/logo?t={int(time.time())}",
    }


@app.get("/branding/logo")
def get_branding_logo():
    path = auth.get_tool_logo_path()
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Custom logo maujood nahi hai.")
    ext = os.path.splitext(path)[1].lower()
    media_type = "image/png" if ext == ".png" else ("image/jpeg" if ext in (".jpg", ".jpeg") else "image/svg+xml")
    return FileResponse(path, media_type=media_type)



# ----------------------------------------------------------------------------
# System Diagnostics & Self-Healing Repairs (Owner / Admin Hub)
# ----------------------------------------------------------------------------

@app.get("/system/diagnostics")
def system_diagnostics(request: Request):
    """System ki health aur resources check karta hai."""
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    ffprobe_ok = shutil.which("ffprobe") is not None

    total_disk_gb, used_disk_gb, free_disk_gb = 0, 0, 0
    try:
        disk = shutil.disk_usage(BASE_DIR)
        total_disk_gb = round(disk.total / (1024 ** 3), 1)
        used_disk_gb = round(disk.used / (1024 ** 3), 1)
        free_disk_gb = round(disk.free / (1024 ** 3), 1)
    except Exception:
        pass

    uploads_mb = 0
    try:
        for root, _, files in os.walk(UPLOAD_DIR):
            for f in files:
                uploads_mb += os.path.getsize(os.path.join(root, f))
        uploads_mb = round(uploads_mb / (1024 * 1024), 2)
    except Exception:
        pass

    nvenc_supported = False
    try:
        proc = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True, timeout=3)
        if "h264_nvenc" in proc.stdout:
            nvenc_supported = True
    except Exception:
        pass

    users = auth._load_users()

    return {
        "status": "ok",
        "tools": {
            "ffmpeg": ffmpeg_ok,
            "ffprobe": ffprobe_ok,
            "nvenc_gpu": nvenc_supported,
        },
        "disk": {
            "total_gb": total_disk_gb,
            "used_gb": used_disk_gb,
            "free_gb": free_disk_gb,
            "uploads_mb": uploads_mb,
        },
        "active_sessions_count": len(SESSIONS),
        "registered_users_count": len(users),
        "owner_name": "Hafiz Muhammad Umar",
    }


@app.post("/system/repair/clean-cache")
def repair_clean_cache():
    """Temporary renders aur incomplete work files ko delete karke disk free karta hai."""
    cleaned_count = 0
    for item in os.listdir(UPLOAD_DIR):
        item_path = os.path.join(UPLOAD_DIR, item)
        if os.path.isdir(item_path):
            work_dir = os.path.join(item_path, "work")
            if os.path.isdir(work_dir):
                try:
                    shutil.rmtree(work_dir, ignore_errors=True)
                    cleaned_count += 1
                except Exception:
                    pass
    return {"status": "ok", "message": f"Cache clean ho gaya! {cleaned_count} work directories saaf kiye gaye. ✅"}


# ----------------------------------------------------------------------------
# Server entrypoint  —  `python app.py`
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    missing_tools = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing_tools:
        print(f"[WARNING] Ye tools PATH mein nahi mile: {', '.join(missing_tools)} — "
              f"render fail hoga. Pehle FFmpeg install karein.")
    port = int(os.environ.get("PORT", 8000))
    print(f"Umar AI Video Studio  ->  http://0.0.0.0:{port}/app/")
    uvicorn.run(app, host="0.0.0.0", port=port)


