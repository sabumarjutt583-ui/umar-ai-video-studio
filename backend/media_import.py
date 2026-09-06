"""
Filename se segment-number nikalna, aur Zip files se bulk media extract karna.

Supported filename patterns (case-insensitive):
- "1_beach.jpg", "2_city.mp4"          -> number pehle
- "segment1.jpg", "segment_2.mp4"      -> "segment" ke baad number
- "scene1.jpg", "scene_3.mp4"          -> "scene" ke baad number (B-Roll Finder Pro jaisa)
- "clip-04.mp4", "shot_7.png"          -> clip/shot/part/img ke baad number
- Aakhri fallback: filename mein akela number (magar sirf tab jab wo
  plausible ho — camera dumps jaise "IMG_20240101_123456.jpg" ko galti se
  segment 20240101 nahi banate)
"""

import re
import os
import zipfile

# Maximum plausible segment number — isse bada number milne par usse
# "date/timestamp" samjha jata hai, segment number nahi
MAX_PLAUSIBLE_SEGMENT = 2000

# Camera/phone dump patterns jinme number date-time hota hai, segment nahi
CAMERA_DUMP_PATTERN = re.compile(
    r"^(img|dsc|dscn|pxl|photo|video|vid|screenshot|snapchat|whatsapp|mvimg|p)[\s_\-]*\d{6,}",
    re.IGNORECASE,
)

NUMBER_PATTERNS = [
    re.compile(r"^(\d{1,4})[\s_\-\.]"),                                    # "1_beach.jpg" -> 1
    re.compile(r"(?:segment|seg)[\s_\-]?(\d{1,4})", re.IGNORECASE),        # "segment_2.mp4" -> 2
    re.compile(r"(?:scene|sc)[\s_\-]?(\d{1,4})", re.IGNORECASE),           # "scene3.jpg" -> 3
    re.compile(r"(?:clip|shot|part|line|sentence)[\s_\-]?(\d{1,4})", re.IGNORECASE),
]

# Fallback (sirf safe cases mein use hota hai)
LOOSE_NUMBER_PATTERN = re.compile(r"(\d{1,4})")


def extract_segment_number(filename: str):
    """
    Filename se segment number nikalta hai. Nahi mila (ya bharosemand na ho)
    to None deta hai — taake galat segment se auto-assign na ho jaye.
    """
    name = os.path.splitext(os.path.basename(filename))[0]

    for pattern in NUMBER_PATTERNS:
        match = pattern.search(name)
        if match:
            num = int(match.group(1))
            if 1 <= num <= MAX_PLAUSIBLE_SEGMENT:
                return num

    # Camera dump (IMG_20240101_1234) ho to koi number bharosemand nahi
    if CAMERA_DUMP_PATTERN.match(name):
        return None

    # Fallback: sirf tab jab filename mein EXACTLY ek chhota number ho
    all_numbers = re.findall(r"\d+", name)
    if len(all_numbers) == 1:
        num = int(all_numbers[0])
        if 1 <= num <= MAX_PLAUSIBLE_SEGMENT:
            return num

    return None


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".avif", ".heic"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v", ".wmv", ".flv", ".mpeg", ".mpg", ".3gp"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus", ".wma"}


def is_media_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in IMAGE_EXTS or ext in VIDEO_EXTS


def is_video_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in VIDEO_EXTS


def is_audio_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in AUDIO_EXTS


def _safe_member_name(member: str) -> str:
    """
    Zip-slip protection: zip ke andar ka path se koi bhi '..' ya absolute path
    hata kar sirf SAAF filename banata hai — taake malicious zip system mein
    kahin bhi file na likh sake.
    """
    name = member.replace("\\", "/")
    name = os.path.basename(name)          # sirf filename, koi directory nahi
    name = name.replace("..", "_").strip()
    name = re.sub(r'[<>:"|?*\x00-\x1f]', "_", name)   # Windows-illegal chars
    return name or "file"


def extract_zip(zip_path: str, extract_dir: str) -> list:
    """
    Zip file ko SAFELY extract karta hai (zip-slip proof — sab files seedha
    extract_dir mein flat likhi jati hain) aur andar ki saari media files ki
    list deta hai, har ek ke sath uska detected segment-number.
    """
    os.makedirs(extract_dir, exist_ok=True)
    results = []
    used_names = set()

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if member.endswith("/"):
                continue  # directory entry
            original_name = os.path.basename(member.replace("\\", "/"))
            if not original_name or not is_media_file(original_name):
                continue

            safe_name = _safe_member_name(original_name)
            # Naam clash ho to suffix laga dete hain
            final_name = safe_name
            counter = 1
            while final_name.lower() in used_names:
                stem, ext = os.path.splitext(safe_name)
                final_name = f"{stem}_{counter}{ext}"
                counter += 1
            used_names.add(final_name.lower())

            target_path = os.path.join(extract_dir, final_name)
            with zf.open(member) as src, open(target_path, "wb") as dst:
                dst.write(src.read())

            results.append({
                "filename": original_name,
                "local_path": target_path,
                "segment_number": extract_segment_number(original_name),
                "type": "video" if is_video_file(original_name) else "photo",
            })

    results.sort(key=lambda r: (r["segment_number"] is None, r["segment_number"] or 0, r["filename"]))
    return results
