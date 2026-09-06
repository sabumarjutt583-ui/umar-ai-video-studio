"""
Media Mismatch Flagging — render se PEHLE galtiyan pakadne wala module.

Har segment ki media ko check karta hai aur teen level ke issues deta hai:
  - "error"   -> render kharab hogi (jaise media hi nahi hai)
  - "warning" -> render ho jayegi magar quality/look pe asar padega
  - "info"    -> sirf jaan lene ki baat

Isse user ko 20 minute render ke BAAD pata nahi chalta ke kuch galat tha.
"""

import json
import os
import subprocess

# Video itni chhoti ho ke isse zyada slow karna pade — to repeat lagega
MAX_SLOWDOWN = 2.5
# Slow ke baad video max itni baar dobara chalti hai (video_assembler se match)
MAX_VIDEO_REPEATS = 2
# Image ki chhoti side target se itne guna kam ho to "low resolution" warning
LOW_RES_FACTOR = 0.75
# Aspect ratio itna alag ho to heavy crop hoga
ASPECT_TOLERANCE = 0.45
# Isse chhoti duration wale segments par media theek nahi dikhti
MIN_USEFUL_DURATION = 0.4


def probe_media(path: str) -> dict:
    """ffprobe se width/height/duration/has_video/has_audio nikalta hai."""
    info = {"ok": False, "width": 0, "height": 0, "duration": 0.0,
            "has_video": False, "has_audio": False, "fps": 0.0}
    if not path or not os.path.exists(path):
        return info

    result = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_streams", "-show_format", path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return info

    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return info

    try:
        info["duration"] = float(data.get("format", {}).get("duration", 0) or 0)
    except (TypeError, ValueError):
        info["duration"] = 0.0

    for stream in data.get("streams", []):
        codec_type = stream.get("codec_type")
        if codec_type == "video" and not info["has_video"]:
            info["has_video"] = True
            info["width"] = int(stream.get("width") or 0)
            info["height"] = int(stream.get("height") or 0)
            rate = stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "0/1"
            try:
                num, den = rate.split("/")
                info["fps"] = round(float(num) / float(den), 2) if float(den) else 0.0
            except (ValueError, ZeroDivisionError):
                info["fps"] = 0.0
        elif codec_type == "audio":
            info["has_audio"] = True

    info["ok"] = info["has_video"]
    return info


def _issue(segment_index, level, code, data=None):
    """Frontend ko translate-able issue deta hai (message frontend i18n se banta hai)."""
    return {
        "segment_index": segment_index,
        "segment_number": segment_index + 1,
        "level": level,
        "code": code,
        "data": data or {},
    }


def validate_segments(segments: list, resolve_local_path, target_width: int = 1080,
                      target_height: int = 1920, voice_duration: float = 0.0) -> dict:
    """
    Saare segments check karta hai.

    resolve_local_path: function(media_dict) -> local file path (ya None)
    Returns: {"issues": [...], "summary": {...}, "segment_status": [...]}
    """
    issues = []
    segment_status = []
    seen_paths = {}
    target_aspect = target_width / target_height if target_height else 1.0

    total_timeline = 0.0
    with_media = 0

    for i, seg in enumerate(segments):
        duration = max(float(seg.get("end", 0)) - float(seg.get("start", 0)), 0.0)
        total_timeline += duration
        media = seg.get("media") or {}
        status = {"segment_index": i, "level": "ok", "duration": round(duration, 2)}

        if duration <= 0:
            issues.append(_issue(i, "error", "zero_duration"))
            status["level"] = "error"
        elif duration < MIN_USEFUL_DURATION:
            issues.append(_issue(i, "warning", "very_short_segment",
                                 {"duration": round(duration, 2)}))
            status["level"] = "warning"

        if not media or not (media.get("full_url") or media.get("local_path")):
            issues.append(_issue(i, "error", "no_media"))
            status["level"] = "error"
            segment_status.append(status)
            continue

        with_media += 1
        local_path = resolve_local_path(media)

        # Ek hi file do jagah? (aksar galti se hoti hai — filename numbering clash)
        dup_key = (local_path or media.get("full_url") or "").lower()
        if dup_key:
            if dup_key in seen_paths:
                issues.append(_issue(i, "warning", "duplicate_media",
                                     {"other_segment": seen_paths[dup_key] + 1}))
                status["level"] = status["level"] if status["level"] == "error" else "warning"
            else:
                seen_paths[dup_key] = i

        if not local_path or not os.path.exists(local_path):
            # Remote URL ho sakta hai — us case mein skip, warna file missing hai
            if not str(media.get("full_url", "")).startswith("http"):
                issues.append(_issue(i, "error", "file_missing"))
                status["level"] = "error"
            segment_status.append(status)
            continue

        info = probe_media(local_path)
        status["probe"] = {"width": info["width"], "height": info["height"],
                           "duration": round(info["duration"], 2), "fps": info["fps"]}

        if not info["ok"]:
            issues.append(_issue(i, "error", "unreadable_media",
                                 {"file": os.path.basename(local_path)}))
            status["level"] = "error"
            segment_status.append(status)
            continue

        is_video = media.get("type") == "video"

        if is_video and info["duration"] > 0:
            needed_ratio = duration / info["duration"]
            max_cover_ratio = MAX_SLOWDOWN * (MAX_VIDEO_REPEATS + 1)
            if needed_ratio > max_cover_ratio:
                # Slow + max repeat ke baad bhi length kam — aakhiri frame ki
                # image se baqi duration poori hogi (freeze nahi, zoom ke sath)
                issues.append(_issue(i, "warning", "video_needs_image_fill", {
                    "have": round(info["duration"], 2),
                    "need": round(duration, 2),
                }))
                status["level"] = "warning" if status["level"] != "error" else "error"
            elif needed_ratio > MAX_SLOWDOWN:
                # Slow + repeat se cover ho jayega — sirf info
                issues.append(_issue(i, "info", "video_too_short", {
                    "have": round(info["duration"], 2),
                    "need": round(duration, 2),
                }))
            elif info["duration"] > duration * 4 and info["duration"] > 12:
                issues.append(_issue(i, "info", "video_much_longer", {
                    "have": round(info["duration"], 2),
                    "need": round(duration, 2),
                }))

        # Resolution check — target se kaafi chhoti media blurry dikhegi
        if info["width"] and info["height"]:
            if (info["width"] < target_width * LOW_RES_FACTOR and
                    info["height"] < target_height * LOW_RES_FACTOR):
                issues.append(_issue(i, "warning", "low_resolution", {
                    "have": f"{info['width']}x{info['height']}",
                    "target": f"{target_width}x{target_height}",
                }))
                status["level"] = "warning" if status["level"] != "error" else "error"

            media_aspect = info["width"] / info["height"]
            if target_aspect > 0 and abs(media_aspect - target_aspect) / target_aspect > ASPECT_TOLERANCE:
                issues.append(_issue(i, "info", "aspect_mismatch", {
                    "media": f"{info['width']}x{info['height']}",
                    "target": f"{target_width}x{target_height}",
                }))

            if is_video and info["fps"] and info["fps"] < 20:
                issues.append(_issue(i, "info", "low_fps", {"fps": info["fps"]}))

        segment_status.append(status)

    # Timeline vs voice length — 1 second se zyada farq ho to batate hain
    if voice_duration > 0 and abs(total_timeline - voice_duration) > 1.0:
        issues.append(_issue(-1, "warning", "timeline_voice_mismatch", {
            "timeline": round(total_timeline, 2),
            "voice": round(voice_duration, 2),
        }))

    has_text = any(bool((s.get("text") or "").strip()) for s in segments)
    if not has_text:
        issues.append(_issue(-1, "info", "no_caption_text", {}))

    summary = {
        "total_segments": len(segments),
        "with_media": with_media,
        "missing_media": len(segments) - with_media,
        "errors": sum(1 for x in issues if x["level"] == "error"),
        "warnings": sum(1 for x in issues if x["level"] == "warning"),
        "infos": sum(1 for x in issues if x["level"] == "info"),
        "timeline_duration": round(total_timeline, 2),
        "voice_duration": round(voice_duration, 2),
        "ready": all(x["level"] != "error" for x in issues),
    }

    return {"issues": issues, "summary": summary, "segment_status": segment_status}
