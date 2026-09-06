"""
Sound Effects Generator.

Har sound effect FFmpeg ke audio-synthesis filters (aevalsrc/anoisesrc) se
generate hota hai — koi internet download nahi chahiye, hamesha available rehta hai.
"""

import subprocess
import os

SAMPLE_RATE = 44100


def _run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"SFX generation error: {result.stderr[-500:]}")


def generate_click(output_path: str):
    """Chhota, sharp 'tick' sound — button click jaisa."""
    expr = "sin(2*PI*1400*t)*exp(-40*t)"
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s={SAMPLE_RATE}:d=0.1", output_path]
    _run(cmd)


def generate_pop(output_path: str):
    """Pitch-drop 'pop' sound."""
    expr = "sin(2*PI*(250+900*exp(-35*t))*t)*exp(-22*t)"
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s={SAMPLE_RATE}:d=0.18", output_path]
    _run(cmd)


def generate_whoosh(output_path: str):
    """Filtered noise 'whoosh' — camera pan/transition jaisi."""
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anoisesrc=d=0.4:c=pink:a=0.6:r={SAMPLE_RATE}",
        "-af", "afade=t=in:d=0.05,afade=t=out:st=0.22:d=0.18,highpass=f=400,lowpass=f=3500",
        output_path
    ]
    _run(cmd)


def generate_ding(output_path: str):
    """Do-tone notification/bell 'ding' sound."""
    expr = "0.6*sin(2*PI*880*t)*exp(-6*t)+0.4*sin(2*PI*1320*t)*exp(-6*t)"
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s={SAMPLE_RATE}:d=0.8", output_path]
    _run(cmd)


def generate_notification(output_path: str):
    """Chhota, crisp notification-tone (single beep)."""
    expr = "sin(2*PI*1600*t)*exp(-18*t)"
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s={SAMPLE_RATE}:d=0.3", output_path]
    _run(cmd)


def generate_success_chime(output_path: str, work_dir: str):
    """2 ascending notes (success/achievement feel)."""
    note1 = os.path.join(work_dir, "_chime_n1.mp3")
    note2 = os.path.join(work_dir, "_chime_n2.mp3")
    _run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"aevalsrc='sin(2*PI*659*t)*exp(-8*t)':s={SAMPLE_RATE}:d=0.25", note1])
    _run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"aevalsrc='sin(2*PI*988*t)*exp(-6*t)':s={SAMPLE_RATE}:d=0.4", note2])

    list_file = os.path.join(work_dir, "_chime_list.txt")
    with open(list_file, "w") as f:
        f.write(f"file '{os.path.abspath(note1)}'\nfile '{os.path.abspath(note2)}'\n")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_path])


def generate_drum_hit(output_path: str):
    """Low, punchy drum-hit — emphasis/impact ke liye."""
    expr = "sin(2*PI*(120+60*exp(-20*t))*t)*exp(-15*t)"
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s={SAMPLE_RATE}:d=0.35", output_path]
    _run(cmd)


SFX_GENERATORS = {
    "click": generate_click,
    "pop": generate_pop,
    "whoosh": generate_whoosh,
    "ding": generate_ding,
    "notification": generate_notification,
    "drum_hit": generate_drum_hit,
}

SFX_LABELS = {
    "click": "Click",
    "pop": "Pop",
    "whoosh": "Whoosh (Transition)",
    "ding": "Ding (Bell)",
    "notification": "Notification Beep",
    "success_chime": "Success Chime",
    "drum_hit": "Drum Hit (Impact)",
}


def generate_sfx(sfx_key: str, output_path: str, work_dir: str = None):
    """SFX generate karke MP3 file save karta hai."""
    if sfx_key == "success_chime":
        generate_success_chime(output_path, work_dir or os.path.dirname(output_path))
        return output_path

    generator = SFX_GENERATORS.get(sfx_key)
    if not generator:
        raise ValueError(f"Unknown sound effect: {sfx_key}")
    generator(output_path)
    return output_path
