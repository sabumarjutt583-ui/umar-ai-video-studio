"""
Audio Tools — Voice Multi-Part Upload ka core.

Agar user ki recording ek hi file mein nahi hai (jaise part1.mp3, part2.mp3,
part3.mp3), to ye module unhe ORDER mein jodkar ek single voice file bana deta
hai — jise baaki poori pipeline normal voice ki tarah use karti hai.

Har part ka exact offset bhi return hota hai, taake user ko pata chale ke
kis part ki awaaz video mein kis waqt shuru hogi.
"""

import os
import re
import subprocess
import uuid


def _run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Audio tool error: {result.stderr[-1500:]}")
    return result


def probe_duration(path: str) -> float:
    """Kisi bhi audio/video file ki duration (seconds) deta hai. Fail ho to 0.0."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except (ValueError, AttributeError):
        return 0.0


def natural_sort_key(filename: str):
    """
    'part2.mp3' ko 'part10.mp3' se PEHLE rakhta hai (normal alphabetical sort
    isko ulta kar deta hai). Human-friendly ordering.
    """
    name = os.path.basename(filename).lower()
    return [int(chunk) if chunk.isdigit() else chunk for chunk in re.split(r"(\d+)", name)]


def concat_audio_parts(part_paths: list, output_path: str, work_dir: str,
                       gap_seconds: float = 0.0) -> dict:
    """
    Multiple audio parts ko ORDER mein jodkar ek single file banata hai.

    Sab parts ko pehle ek common format (44.1kHz stereo WAV) mein normalize
    karte hain — warna different sample-rate/channel wali files jodne par
    awaaz kharab (speed/pitch issue) ho jati hai.

    gap_seconds: har part ke darmiyan khamoshi (optional, jaise 0.3s breathing gap)

    Returns: {"output_path", "total_duration", "parts": [{filename, start, duration}]}
    """
    if not part_paths:
        raise ValueError("Koi audio part nahi mila.")

    os.makedirs(work_dir, exist_ok=True)
    normalized = []
    parts_info = []
    running_offset = 0.0

    silence_path = None
    if gap_seconds > 0:
        silence_path = os.path.join(work_dir, f"_gap_{uuid.uuid4().hex[:6]}.wav")
        _run(["ffmpeg", "-y", "-f", "lavfi", "-i",
              f"anullsrc=channel_layout=stereo:sample_rate=44100",
              "-t", str(gap_seconds), "-c:a", "pcm_s16le", silence_path])

    for i, path in enumerate(part_paths):
        norm_path = os.path.join(work_dir, f"_voicepart_{i:03d}.wav")
        _run(["ffmpeg", "-y", "-i", path,
              "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", norm_path])

        duration = probe_duration(norm_path)
        parts_info.append({
            "filename": os.path.basename(path),
            "start": round(running_offset, 2),
            "duration": round(duration, 2),
        })
        running_offset += duration

        normalized.append(norm_path)
        if silence_path and i < len(part_paths) - 1:
            normalized.append(silence_path)
            running_offset += gap_seconds

    list_file = os.path.join(work_dir, f"_voice_concat_{uuid.uuid4().hex[:6]}.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for p in normalized:
            escaped = os.path.abspath(p).replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")

    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
          "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", output_path])

    # Temp cleanup
    for p in set(normalized + [list_file]):
        try:
            os.remove(p)
        except OSError:
            pass

    return {
        "output_path": output_path,
        "total_duration": round(probe_duration(output_path), 2),
        "parts": parts_info,
    }
