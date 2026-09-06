"""
Sticker Asset Generator.

Har sticker ko PIL (vector shapes) se generate karta hai — koi internet
download nahi chahiye, hamesha consistent quality milti hai.
"""

from PIL import Image, ImageDraw, ImageFont
import os
import math

# Cross-platform font candidates — Windows pehle (kyunke tool mostly Windows par
# chalta hai), phir Linux/macOS fallbacks. Pehle jo mil jaye wahi use hota hai.
BOLD_FONT_CANDIDATES = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/ariblk.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
REGULAR_FONT_CANDIDATES = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _get_font(size, bold=True):
    candidates = BOLD_FONT_CANDIDATES if bold else REGULAR_FONT_CANDIDATES
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    # Aakhri fallback: PIL ka built-in font (chhota hota hai, isliye scale-up karte hain)
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def youtube_subscribe_button(size=400):
    """Red 'SUBSCRIBE' button, YouTube-style rounded rectangle."""
    w, h = size, int(size * 0.32)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(255, 0, 0, 255))
    font = _get_font(int(h * 0.42))
    text = "SUBSCRIBE"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) / 2, (h - th) / 2 - bbox[1]), text, font=font, fill=(255, 255, 255, 255))
    return img


def bell_icon(size=300):
    """Notification bell (YouTube-style), red/white."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, int(size * 0.45)
    r = int(size * 0.32)
    # Bell body (rounded top, wide bottom via polygon + arc)
    draw.pieslice([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=(255, 255, 255, 255))
    draw.rectangle([cx - r, cy, cx + r, cy + int(r * 0.9)], fill=(255, 255, 255, 255))
    draw.polygon([
        (cx - int(r * 1.15), cy + int(r * 0.9)),
        (cx + int(r * 1.15), cy + int(r * 0.9)),
        (cx + int(r * 0.85), cy + int(r * 1.15)),
        (cx - int(r * 0.85), cy + int(r * 1.15)),
    ], fill=(255, 255, 255, 255))
    # Bell base knob
    draw.ellipse([cx - int(r * 0.22), cy + int(r * 1.1), cx + int(r * 0.22), cy + int(r * 1.5)], fill=(255, 255, 255, 255))
    # Red notification dot
    dot_r = int(size * 0.14)
    draw.ellipse([size - dot_r * 2 - 5, 5, size - 5, dot_r * 2 + 5], fill=(255, 0, 0, 255))
    return img


def arrow_icon(size=300, direction="up", color=(255, 209, 102, 255)):
    """Simple bold arrow — direction: up/down/left/right."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    m = size * 0.15
    if direction == "up":
        pts_head = [(size / 2, m), (m, size * 0.5), (size * 0.38, size * 0.5),
                    (size * 0.38, size - m), (size * 0.62, size - m),
                    (size * 0.62, size * 0.5), (size - m, size * 0.5)]
    elif direction == "down":
        pts_head = [(size / 2, size - m), (m, size * 0.5), (size * 0.38, size * 0.5),
                    (size * 0.38, m), (size * 0.62, m),
                    (size * 0.62, size * 0.5), (size - m, size * 0.5)]
    elif direction == "left":
        pts_head = [(m, size / 2), (size * 0.5, m), (size * 0.5, size * 0.38),
                    (size - m, size * 0.38), (size - m, size * 0.62),
                    (size * 0.5, size * 0.62), (size * 0.5, size - m)]
    else:  # right
        pts_head = [(size - m, size / 2), (size * 0.5, m), (size * 0.5, size * 0.38),
                    (m, size * 0.38), (m, size * 0.62),
                    (size * 0.5, size * 0.62), (size * 0.5, size - m)]
    draw.polygon(pts_head, fill=color)
    return img


def ring_icon(size=300, color=(255, 209, 102, 255)):
    """Notification 'ring/circle' highlight — jaise kisi cheez ke around gol nishan."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    stroke = max(int(size * 0.06), 4)
    m = stroke
    draw.ellipse([m, m, size - m, size - m], outline=color, width=stroke)
    return img


def star_icon(size=300, color=(255, 209, 102, 255)):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size / 2, size / 2
    outer_r, inner_r = size * 0.48, size * 0.2
    points = []
    for i in range(10):
        angle = math.pi / 5 * i - math.pi / 2
        r = outer_r if i % 2 == 0 else inner_r
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=color)
    return img


def heart_icon(size=300, color=(255, 82, 82, 255)):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = size * 0.26
    draw.ellipse([size * 0.12, size * 0.18, size * 0.12 + 2 * r, size * 0.18 + 2 * r], fill=color)
    draw.ellipse([size * 0.48, size * 0.18, size * 0.48 + 2 * r, size * 0.18 + 2 * r], fill=color)
    draw.polygon([
        (size * 0.15, size * 0.42), (size * 0.85, size * 0.42), (size * 0.5, size * 0.92)
    ], fill=color)
    return img


def fire_icon(size=300, color=(255, 122, 0, 255)):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = size / 2
    # Flame shape: teardrop banaya multiple curve-points se (smooth flame jaisa)
    outer_pts = [
        (cx, size * 0.05),
        (cx + size * 0.22, size * 0.30),
        (cx + size * 0.30, size * 0.55),
        (cx + size * 0.22, size * 0.75),
        (cx + size * 0.10, size * 0.90),
        (cx, size * 0.95),
        (cx - size * 0.10, size * 0.90),
        (cx - size * 0.22, size * 0.75),
        (cx - size * 0.30, size * 0.55),
        (cx - size * 0.22, size * 0.30),
    ]
    draw.polygon(outer_pts, fill=color)
    # Andar ek halki inner-flame (lighter shade) taake depth dikhe
    inner_color = (255, 210, 90, 255)
    inner_pts = [
        (cx, size * 0.35),
        (cx + size * 0.12, size * 0.55),
        (cx + size * 0.08, size * 0.72),
        (cx, size * 0.85),
        (cx - size * 0.08, size * 0.72),
        (cx - size * 0.12, size * 0.55),
    ]
    draw.polygon(inner_pts, fill=inner_color)
    return img


def thumbsup_icon(size=300, color=(61, 220, 132, 255)):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Fist/palm (neeche wala chunky block)
    draw.rounded_rectangle(
        [size * 0.15, size * 0.5, size * 0.42, size * 0.88],
        radius=int(size * 0.06), fill=color
    )
    # Thumb (upar jata hua, tilted rectangle jaisa via polygon)
    draw.polygon([
        (size * 0.40, size * 0.5),
        (size * 0.40, size * 0.30),
        (size * 0.48, size * 0.12),
        (size * 0.58, size * 0.12),
        (size * 0.62, size * 0.22),
        (size * 0.55, size * 0.42),
        (size * 0.55, size * 0.5),
    ], fill=color)
    # Thumb ko rounded look dene ke liye chhota circle uske top pe
    draw.ellipse([size * 0.46, size * 0.10, size * 0.60, size * 0.24], fill=color)
    return img


STICKER_GENERATORS = {
    "youtube_subscribe": youtube_subscribe_button,
    "bell": bell_icon,
    "arrow_up": lambda size=300: arrow_icon(size, "up"),
    "arrow_down": lambda size=300: arrow_icon(size, "down"),
    "arrow_left": lambda size=300: arrow_icon(size, "left"),
    "arrow_right": lambda size=300: arrow_icon(size, "right"),
    "ring": ring_icon,
    "star": star_icon,
    "heart": heart_icon,
    "fire": fire_icon,
    "thumbsup": thumbsup_icon,
}

STICKER_LABELS = {
    "youtube_subscribe": "YouTube Subscribe Button",
    "bell": "Notification Bell",
    "arrow_up": "Arrow Up",
    "arrow_down": "Arrow Down",
    "arrow_left": "Arrow Left",
    "arrow_right": "Arrow Right",
    "ring": "Ring / Circle Highlight",
    "star": "Star",
    "heart": "Heart",
    "fire": "Fire",
    "thumbsup": "Thumbs Up",
}


def generate_sticker_png(sticker_key: str, output_path: str, size: int = 300):
    """Sticker generate karke PNG file save karta hai."""
    generator = STICKER_GENERATORS.get(sticker_key)
    if not generator:
        raise ValueError(f"Unknown sticker: {sticker_key}")
    img = generator(size)
    img.save(output_path, "PNG")
    return output_path
