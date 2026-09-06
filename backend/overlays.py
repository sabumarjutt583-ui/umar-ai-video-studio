"""
Overlays Module — Stickers aur Custom Text ko video pe specific time/position
par "burn" karta hai (FFmpeg overlay + drawtext filters se).
"""

import os
import subprocess
from sticker_assets import generate_sticker_png
from caption_generator import detect_script

# Position -> (x_expr, y_expr) for image overlay (uses overlay_w/overlay_h)
OVERLAY_POSITION_MAP = {
    "top_left": ("30", "30"),
    "top_right": ("main_w-overlay_w-30", "30"),
    "bottom_left": ("30", "main_h-overlay_h-30"),
    "bottom_right": ("main_w-overlay_w-30", "main_h-overlay_h-30"),
    "center": ("(main_w-overlay_w)/2", "(main_h-overlay_h)/2"),
    "top_center": ("(main_w-overlay_w)/2", "30"),
    "bottom_center": ("(main_w-overlay_w)/2", "main_h-overlay_h-30"),
}

# Position -> (x_expr, y_expr) for drawtext (uses text_w/text_h)
TEXT_POSITION_MAP = {
    "top_left": ("30", "30"),
    "top_right": ("main_w-text_w-30", "30"),
    "bottom_left": ("30", "main_h-text_h-30"),
    "bottom_right": ("main_w-text_w-30", "main_h-text_h-30"),
    "center": ("(main_w-text_w)/2", "(main_h-text_h)/2"),
    "top_center": ("(main_w-text_w)/2", "30"),
    "bottom_center": ("(main_w-text_w)/2", "main_h-text_h-30"),
}

# Preset font -> font-file path (Windows standard paths; sandbox test ke liye
# DejaVu fallback bhi try karte hain agar Windows path na mile)
FONT_FILE_CANDIDATES = {
    "bold": ["C:/Windows/Fonts/ariblk.ttf", "C:/Windows/Fonts/arialbd.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "clean": ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "elegant": ["C:/Windows/Fonts/georgia.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    "handwritten": ["C:/Windows/Fonts/comic.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"],
    "impact": ["C:/Windows/Fonts/impact.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "modern": ["C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "rounded": ["C:/Windows/Fonts/verdana.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "serif": ["C:/Windows/Fonts/times.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    # Non-Latin scripts (Urdu/Arabic/Hindi/Korean/Chinese waghera) ke liye
    "korean": ["C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/gulim.ttc", "C:/Windows/Fonts/batang.ttc"],
    "urdu": ["C:/Windows/Fonts/NotoNastaliqUrdu-Regular.ttf", "C:/Windows/Fonts/segoeui.ttf"],
    "arabic": ["C:/Windows/Fonts/trado.ttf", "C:/Windows/Fonts/segoeui.ttf"],
    "devanagari": ["C:/Windows/Fonts/Nirmala.ttf", "C:/Windows/Fonts/mangal.ttf"],
    "chinese": ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"],
    "japanese": ["C:/Windows/Fonts/msgothic.ttc", "C:/Windows/Fonts/meiryo.ttc", "C:/Windows/Fonts/yugothr.ttc"],
}


def _resolve_font_file(font_key: str, text: str = "") -> str:
    # Text mein non-Latin script ho (jaise Korean, Urdu, Arabic), to khud ba khud
    # sahi script ka font uthate hain taake tofu boxes [][][] na banein
    if text:
        script = detect_script(text)
        if script != "latin" and script in FONT_FILE_CANDIDATES:
            for path in FONT_FILE_CANDIDATES[script]:
                if os.path.exists(path):
                    return path

    candidates = FONT_FILE_CANDIDATES.get(font_key, FONT_FILE_CANDIDATES["clean"])
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[-1]


def _escape_filter_path(path: str) -> str:
    """
    BUG FIX: Windows font path (C:/Windows/Fonts/...) ka colon FFmpeg filter
    parser option-separator samajh leta tha -> "No option name near ..." error.
    Backslashes ko forward slash karte hain aur colon ko escape karte hain.
    """
    path = path.replace("\\", "/")
    return path.replace(":", "\\:").replace("'", "\\'")


def _escape_drawtext(text: str) -> str:
    return (text.replace("\\", "\\\\\\\\")
                .replace(":", "\\:")
                .replace("'", "\u2019")
                .replace("%", "\\%"))


def _hex_to_rgba(hex_color: str, opacity: float) -> str:
    hex_color = hex_color.lstrip("#")
    return f"0x{hex_color}@{opacity}"


def build_overlay_filter_complex(stickers: list, custom_texts: list, sticker_dir: str,
                                 video_width: int = 1080, video_height: int = 1920):
    """
    stickers: [{"sticker_key", "position", "scale" (0-1, video-width ka fraction),
                "opacity" (0-1), "custom_path" (user ki apni PNG/logo — optional),
                "whole_video" (True = poori video par watermark),
                "times": [{"start": float, "duration": float}, ...]}]
    custom_texts: [{"text", "font", "color", "opacity" (0-1), "position",
                     "start": float, "duration": float}]

    Returns: (filter_complex_string, input_files_list, final_label)
    """
    input_files = []
    filter_chain_parts = []
    current_label = "0:v"
    stage = 0

    sticker_cache = {}
    for sticker in stickers:
        custom_path = sticker.get("custom_path")
        if custom_path and os.path.exists(custom_path):
            # User ka apna logo/watermark/sticker image
            png_path = custom_path
        else:
            key = sticker.get("sticker_key") or "star"
            if key not in sticker_cache:
                generated = os.path.join(sticker_dir, f"sticker_{key}.png")
                generate_sticker_png(key, generated, size=400)
                sticker_cache[key] = generated
            png_path = sticker_cache[key]

        scale = sticker.get("scale", 0.22)
        overlay_w = max(int(video_width * scale), 16)
        opacity = float(sticker.get("opacity", 1.0))

        input_idx = len(input_files) + 1
        input_files.append(png_path)

        pos = OVERLAY_POSITION_MAP.get(sticker.get("position", "top_right"), OVERLAY_POSITION_MAP["top_right"])

        if sticker.get("whole_video"):
            enable_expr = "1"
        else:
            enable_parts = [f"between(t\\,{t['start']}\\,{t['start'] + t['duration']})"
                            for t in sticker.get("times", [])]
            if len(enable_parts) > 1:
                combined = ")+(".join(enable_parts)
                enable_expr = f"gt(({combined})\\,0)"
            elif len(enable_parts) == 1:
                enable_expr = enable_parts[0]
            else:
                enable_expr = "1"

        stage += 1
        scaled_label = f"stk{stage}"
        out_label = f"ov{stage}"

        scale_chain = f"scale={overlay_w}:-1"
        if opacity < 0.999:
            scale_chain += f",format=rgba,colorchannelmixer=aa={max(min(opacity, 1.0), 0.0):.3f}"
        filter_chain_parts.append(f"[{input_idx}:v]{scale_chain}[{scaled_label}]")
        filter_chain_parts.append(
            f"[{current_label}][{scaled_label}]overlay=x={pos[0]}:y={pos[1]}:enable='{enable_expr}'[{out_label}]"
        )
        current_label = out_label

    for text_item in custom_texts:
        text_str = text_item.get("text", "")
        font_file = text_item.get("custom_font_file")
        if not font_file or not os.path.exists(font_file):
            font_file = _resolve_font_file(text_item.get("font", "clean"), text_str)
        color = text_item.get("color", "#FFFFFF")
        opacity = text_item.get("opacity", 1.0)
        rgba = _hex_to_rgba(color, opacity)

        # Agar user ne preview pe click karke exact position di ho (x_percent/y_percent),
        # to wahi use karte hain — warna preset corner/center position use hoti hai
        if text_item.get("x_percent") is not None and text_item.get("y_percent") is not None:
            x_pct = text_item["x_percent"]
            y_pct = text_item["y_percent"]
            x_expr = f"(main_w*{x_pct}/100)-(text_w/2)"
            y_expr = f"(main_h*{y_pct}/100)-(text_h/2)"
        else:
            preset = TEXT_POSITION_MAP.get(text_item.get("position", "center"), TEXT_POSITION_MAP["center"])
            x_expr, y_expr = preset[0], preset[1]

        text_escaped = _escape_drawtext(text_str)
        font_arg = _escape_filter_path(font_file)

        raw_size = float(text_item.get("font_size") or 48)
        # Font size scaling: agar user ne Word/pt jaisi choti value di ho (< 28),
        # to usko video resolution ke mutabiq readable scale karte hain
        if raw_size < 28:
            font_size = int(round(raw_size * (video_height / 400.0)))
        else:
            font_size = int(round(raw_size * (video_height / 1920.0)))
        font_size = max(font_size, 32)

        start = float(text_item.get("start", 0))
        end = start + float(text_item.get("duration", 3))
        box = 1 if text_item.get("background_box", True) else 0
        shadow = "" if box else ":shadowcolor=black@0.8:shadowx=2:shadowy=2:borderw=2:bordercolor=black@0.6"

        stage += 1
        out_label = f"txt{stage}"

        filter_chain_parts.append(
            f"[{current_label}]drawtext=fontfile='{font_arg}':text='{text_escaped}':"
            f"fontsize={font_size}:fontcolor={rgba}:x={x_expr}:y={y_expr}:"
            f"box={box}:boxcolor=black@0.35:boxborderw=10{shadow}:"
            f"enable='between(t\\,{start}\\,{end})'[{out_label}]"
        )
        current_label = out_label

    filter_complex = ";".join(filter_chain_parts)
    return filter_complex, input_files, current_label


def apply_overlays(video_path: str, output_path: str, stickers: list, custom_texts: list, work_dir: str,
                   video_width: int = 1080, video_height: int = 1920):
    """Video pe stickers aur custom text overlays burn karta hai."""
    if not stickers and not custom_texts:
        return video_path

    sticker_dir = os.path.join(work_dir, "stickers")
    os.makedirs(sticker_dir, exist_ok=True)

    filter_complex, sticker_files, final_label = build_overlay_filter_complex(
        stickers, custom_texts, sticker_dir, video_width, video_height
    )

    inputs = ["-i", video_path]
    for f in sticker_files:
        inputs.extend(["-i", f])

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{final_label}]", "-map", "0:a?",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
        "-c:a", "copy",
        output_path
    ]
    # run_ffmpeg use karte hain taake render cancel karne par ye process bhi ruk jaye
    try:
        from video_assembler import run_ffmpeg
        run_ffmpeg(cmd)
    except ImportError:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Overlay error: {result.stderr[-2000:]}")

    return output_path
