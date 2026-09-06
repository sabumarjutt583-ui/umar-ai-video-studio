"""
Caption Generator Module (v10).

ASS (Advanced SubStation Alpha) subtitle files banata hai — font, color, size,
position, outline/box, RTL, auto line-wrap, aur 3 display modes (line /
word-by-word / karaoke highlight) support karta hai — phir FFmpeg ke
'subtitles' filter se video mein "burn" (permanently embed) karta hai.

Naya (v10):
- 20+ languages/scripts ke liye sahi font (Urdu Nastaliq, Hebrew, Bengali,
  Tamil, Telugu, Gujarati, Greek, Vietnamese waghera)
- RTL languages (Urdu/Arabic/Hebrew/Farsi) ke liye sahi handling
- Auto line-wrap — lambi line screen se bahar nahi jati
- Karaoke mode — poori line dikhti hai, bolne wala word highlight hota hai
- Resolution-aware font scaling — 720p/1080p/4K sab mein same look
"""

import os
import re

# Position -> ASS Alignment number (numpad-style: 2=bottom-center, 5=middle-center, 8=top-center)
POSITION_MAP = {
    "top": 8,
    "middle": 5,
    "bottom": 2,
}

# Built-in font choices
FONT_MAP = {
    "bold": "Arial Black",
    "clean": "Arial",
    "elegant": "Georgia",
    "handwritten": "Comic Sans MS",
    "impact": "Impact",
    "modern": "Segoe UI",
    "rounded": "Verdana",
    "serif": "Times New Roman",
}

# Caption Style Presets — pre-made font+color+size+position combos
STYLE_PRESETS = {
    "youtube_bold": {"label": "YouTube Bold", "font": "bold", "font_size": 68,
                     "color": "#FFFFFF", "position": "bottom", "outline": True, "background_box": False},
    "tiktok_yellow": {"label": "TikTok Yellow Pop", "font": "impact", "font_size": 72,
                      "color": "#FFD166", "position": "middle", "outline": True, "background_box": False},
    "clean_box": {"label": "Clean Box", "font": "clean", "font_size": 56,
                  "color": "#FFFFFF", "position": "bottom", "outline": False, "background_box": True},
    "neon_cyan": {"label": "Neon Cyan", "font": "bold", "font_size": 64,
                  "color": "#22D3EE", "position": "bottom", "outline": True, "background_box": False},
    "elegant_gold": {"label": "Elegant Gold", "font": "elegant", "font_size": 58,
                     "color": "#F4C430", "position": "bottom", "outline": True, "background_box": False},
    "minimal_white": {"label": "Minimal White (Top)", "font": "clean", "font_size": 52,
                      "color": "#FFFFFF", "position": "top", "outline": True, "background_box": False},
    "hot_pink": {"label": "Hot Pink Pop", "font": "impact", "font_size": 70,
                 "color": "#FF5F7A", "position": "middle", "outline": True, "background_box": False},
    "podcast_clean": {"label": "Podcast Clean", "font": "modern", "font_size": 54,
                      "color": "#F5F5F5", "position": "bottom", "outline": True, "background_box": False},
    "documentary": {"label": "Documentary Serif", "font": "serif", "font_size": 52,
                    "color": "#FFFFFF", "position": "bottom", "outline": False, "background_box": True},
}

# Script -> font candidates (pehla jo system mein mil jaye wahi use hoga)
SCRIPT_FONT_CANDIDATES = {
    "urdu": ["Jameel Noori Nastaleeq", "Noto Nastaliq Urdu", "Alvi Nastaleeq", "Urdu Typesetting", "Segoe UI"],
    "arabic": ["Segoe UI", "Traditional Arabic", "Arial", "Noto Naskh Arabic"],
    "hebrew": ["Segoe UI", "David", "Arial", "Noto Sans Hebrew"],
    "korean": ["Malgun Gothic", "Noto Sans KR", "Gulim"],
    "japanese": ["Yu Gothic", "MS Gothic", "Noto Sans JP", "Meiryo"],
    "chinese": ["Microsoft YaHei", "SimHei", "Noto Sans SC"],
    "cyrillic": ["Segoe UI", "Arial", "Noto Sans"],
    "greek": ["Segoe UI", "Arial", "Noto Sans"],
    "devanagari": ["Nirmala UI", "Mangal", "Noto Sans Devanagari"],
    "bengali": ["Nirmala UI", "Vrinda", "Noto Sans Bengali"],
    "tamil": ["Nirmala UI", "Latha", "Noto Sans Tamil"],
    "telugu": ["Nirmala UI", "Gautami", "Noto Sans Telugu"],
    "gujarati": ["Nirmala UI", "Shruti", "Noto Sans Gujarati"],
    "kannada": ["Nirmala UI", "Tunga", "Noto Sans Kannada"],
    "malayalam": ["Nirmala UI", "Kartika", "Noto Sans Malayalam"],
    "gurmukhi": ["Nirmala UI", "Raavi", "Noto Sans Gurmukhi"],
    "sinhala": ["Nirmala UI", "Iskoola Pota", "Noto Sans Sinhala"],
    "thai": ["Leelawadee UI", "Tahoma", "Noto Sans Thai"],
    "khmer": ["Leelawadee UI", "Khmer UI", "Noto Sans Khmer"],
    "myanmar": ["Myanmar Text", "Noto Sans Myanmar"],
    "georgian": ["Sylfaen", "Segoe UI", "Noto Sans Georgian"],
    "armenian": ["Sylfaen", "Segoe UI", "Noto Sans Armenian"],
    "ethiopic": ["Ebrima", "Nyala", "Noto Sans Ethiopic"],
    "latin": [],   # matlab: user ke selected font-preset ko hi use karo
}

# RTL (right-to-left) scripts — inke liye alignment/punctuation handling alag hai
RTL_SCRIPTS = {"urdu", "arabic", "hebrew", "farsi"}

# Unicode ranges se script detect karte hain (100% offline)
SCRIPT_RANGES = {
    "korean": [(0xAC00, 0xD7A3), (0x1100, 0x11FF), (0x3130, 0x318F)],
    "japanese": [(0x3040, 0x309F), (0x30A0, 0x30FF)],
    "chinese": [(0x4E00, 0x9FFF), (0x3400, 0x4DBF)],
    "arabic": [(0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    "hebrew": [(0x0590, 0x05FF)],
    "cyrillic": [(0x0400, 0x04FF)],
    "greek": [(0x0370, 0x03FF)],
    "devanagari": [(0x0900, 0x097F)],
    "bengali": [(0x0980, 0x09FF)],
    "gurmukhi": [(0x0A00, 0x0A7F)],
    "gujarati": [(0x0A80, 0x0AFF)],
    "tamil": [(0x0B80, 0x0BFF)],
    "telugu": [(0x0C00, 0x0C7F)],
    "kannada": [(0x0C80, 0x0CFF)],
    "malayalam": [(0x0D00, 0x0D7F)],
    "sinhala": [(0x0D80, 0x0DFF)],
    "thai": [(0x0E00, 0x0E7F)],
    "khmer": [(0x1780, 0x17FF)],
    "myanmar": [(0x1000, 0x109F)],
    "georgian": [(0x10A0, 0x10FF)],
    "armenian": [(0x0530, 0x058F)],
    "ethiopic": [(0x1200, 0x137F)],
}

# Urdu-specific characters — inse Urdu ko Arabic se alag pehchanate hain
URDU_MARKERS = set("ٹڈڑںھےۂۃیۓپچژگک")

# Ye scripts word-boundary space use nahi karte — inke liye wrap character-count se
NO_SPACE_SCRIPTS = {"chinese", "japanese", "thai", "khmer", "myanmar"}

# Ek line mein kitne characters (script ke hisaab se) — isse zyada ho to wrap
DEFAULT_MAX_CHARS = {
    "default": 38,
    "cjk": 16,
}

# Windows/Linux/macOS font directories — installed font check ke liye
FONT_DIRS = [
    "C:/Windows/Fonts",
    os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts"),
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/.fonts"),
    "/Library/Fonts",
    "/System/Library/Fonts",
]

_font_index_cache = None


def _installed_font_names() -> set:
    """
    System mein maujood font FILES ke naam (lowercase, bina extension) ka set.
    Isse hum guess kar sakte hain ke koi font install hai ya nahi.
    """
    global _font_index_cache
    if _font_index_cache is not None:
        return _font_index_cache

    names = set()
    for directory in FONT_DIRS:
        if not os.path.isdir(directory):
            continue
        try:
            for root, _dirs, files in os.walk(directory):
                for filename in files:
                    if filename.lower().endswith((".ttf", ".otf", ".ttc")):
                        names.add(os.path.splitext(filename)[0].lower().replace(" ", ""))
        except OSError:
            continue

    _font_index_cache = names
    return names


def pick_font_for_script(script: str, fallback: str = "Arial") -> str:
    """
    Script ke liye best AVAILABLE font choose karta hai — jo system par
    actually installed ho. Kuch na mile to fallback.
    """
    candidates = SCRIPT_FONT_CANDIDATES.get(script) or []
    if not candidates:
        return fallback

    installed = _installed_font_names()
    for name in candidates:
        key = name.lower().replace(" ", "")
        if any(key in font_file or font_file.startswith(key[:8]) for font_file in installed):
            return name

    # Kuch bhi confirm na ho to pehla candidate hi de dete hain (libass khud
    # substitute kar lega) — magar Segoe UI mostly har Windows par hota hai
    return candidates[0]


def detect_script(text: str) -> str:
    """
    Text mein sabse zyada kis script ke characters hain, wo pehchanta hai
    (Unicode ranges se — 100% offline). Urdu ko Arabic se alag pehchanta hai.
    """
    counts = {key: 0 for key in SCRIPT_RANGES}
    urdu_hits = 0

    for ch in text:
        if ch in URDU_MARKERS:
            urdu_hits += 1
        code = ord(ch)
        for script, ranges in SCRIPT_RANGES.items():
            for start, end in ranges:
                if start <= code <= end:
                    counts[script] += 1
                    break

    # Japanese ka priority Chinese se zyada (Kanji Chinese range se overlap karta hai)
    if counts["japanese"] > 0:
        return "japanese"

    # Arabic script mila hai — Urdu ke special characters mile to Urdu hai
    if counts["arabic"] > 0 and urdu_hits >= 2:
        return "urdu"

    best_script = max(counts, key=counts.get)
    if counts[best_script] == 0:
        return "latin"
    return best_script


def is_rtl_script(script: str) -> bool:
    return script in RTL_SCRIPTS


def wrap_text(text: str, script: str = "latin", max_chars: int = None) -> str:
    """
    Lambi caption line ko 2-3 lines mein todta hai taake screen se bahar na jaye.
    CJK/Thai jaisi scripts (jinme space nahi hota) ke liye character-count se
    todta hai, baaki ke liye word-boundary par.
    """
    text = (text or "").strip()
    if not text:
        return text

    if max_chars is None:
        max_chars = DEFAULT_MAX_CHARS["cjk"] if script in NO_SPACE_SCRIPTS else DEFAULT_MAX_CHARS["default"]

    if len(text) <= max_chars:
        return text

    if script in NO_SPACE_SCRIPTS:
        lines = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
        return "\n".join(lines)

    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    # 3 se zyada lines ho to balance kar dete hain (barabar tukde)
    if len(lines) > 3:
        per_line = max(len(text) // 3 + 1, max_chars)
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) <= per_line or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

    return "\n".join(lines)


def _color_to_ass(hex_color: str, alpha: str = "00") -> str:
    """'#FFFFFF' hex ko ASS '&HAABBGGRR' format mein (ASS colors BGR order mein)."""
    hex_color = (hex_color or "").lstrip("#")
    if len(hex_color) != 6:
        hex_color = "FFFFFF"
    r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
    return f"&H{alpha}{b}{g}{r}"


def _format_ass_time(seconds: float) -> str:
    """Seconds ko ASS time format mein: H:MM:SS.CC"""
    seconds = max(float(seconds), 0.0)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _escape_ass_text(text: str) -> str:
    """ASS ke special characters escape + line-breaks ko \\N mein."""
    return (text.replace("\\", "\\\\")
                .replace("{", "\\{")
                .replace("}", "\\}")
                .replace("\r\n", "\n")
                .replace("\n", "\\N"))


def _scale_font_size(font_size: int, video_height: int) -> int:
    """
    Font size 1080x1920 (vertical) ke hisaab se design hua hai. Doosre
    resolutions/ratios mein same LOOK rakhne ke liye height se scale karte hain.
    """
    try:
        scaled = int(round(float(font_size) * (video_height / 1920.0)))
    except (TypeError, ValueError, ZeroDivisionError):
        return int(font_size or 64)
    return max(scaled, 12)


def _wrap_words(words: list, script: str, max_chars: int = None) -> list:
    """
    Word list ko lines mein todta hai — return: [[word,...], [word,...]]
    (karaoke mode mein har word ka index yaad rakhna hota hai, isliye
    plain-text wrap se kaam nahi chalta)
    """
    if max_chars is None:
        max_chars = DEFAULT_MAX_CHARS["cjk"] if script in NO_SPACE_SCRIPTS else DEFAULT_MAX_CHARS["default"]

    lines = []
    current = []
    current_len = 0
    for word in words:
        add_len = len(word) + (1 if current else 0)
        if current and current_len + add_len > max_chars:
            lines.append(current)
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += add_len
    if current:
        lines.append(current)
    return lines or [[]]


def _words_in_range(raw_words: list, start: float, end: float) -> list:
    """Kisi segment ke andar aane wale words (word ka center segment ke andar ho)."""
    result = []
    for w in raw_words or []:
        try:
            w_start = float(w["start"])
            w_end = float(w.get("end", w_start))
        except (KeyError, TypeError, ValueError):
            continue
        center = (w_start + w_end) / 2
        if start - 0.01 <= center <= end + 0.01:
            result.append(w)
    return result


def _animation_tag(animation: str) -> str:
    """Caption ke andar inline animation override tag."""
    if animation == "fade":
        return "{\\fad(150,150)}"
    if animation == "pop":
        return "{\\fscx80\\fscy80\\t(0,140,\\fscx100\\fscy100)}"
    if animation == "slide_up":
        return "{\\fad(120,120)\\move(0,0,0,0)}"
    return ""


def resolve_font_name(font: str = "clean", custom_font_name: str = None,
                      language_mode: str = "default", sample_text: str = "") -> tuple:
    """
    Font decide karta hai. Priority:
      1. custom_font_name (user ne khud type kiya)
      2. language_mode ('auto' = text se detect, ya koi specific language)
      3. font preset dropdown
    Returns: (font_name, detected_script)
    """
    preset_font = FONT_MAP.get(font, "Arial")

    if language_mode in ("auto", "default") or not language_mode:
        script = detect_script(sample_text or "")
    elif language_mode in SCRIPT_FONT_CANDIDATES:
        script = language_mode
    else:
        script = "latin"

    if custom_font_name:
        return custom_font_name.strip(), script

    if script == "latin":
        return preset_font, script

    return pick_font_for_script(script, preset_font), script


def build_ass_file(
    segments: list,
    output_path: str,
    mode: str = "line",              # "line" | "word" | "karaoke"
    font: str = "clean",
    font_size: int = 64,
    color: str = "#FFFFFF",
    position: str = "bottom",
    outline: bool = True,
    background_box: bool = False,
    raw_words: list = None,
    video_width: int = 1080,
    video_height: int = 1920,
    custom_font_name: str = None,
    language_mode: str = "default",
    highlight_color: str = "#FFD166",   # karaoke mode mein active word ka color
    animation: str = "none",            # "none" | "fade" | "pop"
    bold: bool = True,
    all_caps: bool = False,
    margin_v: int = 80,
    max_chars_per_line: int = None,
):
    """Segments (ya raw_words) se ek .ass subtitle file banata hai."""
    sample_text = " ".join((s.get("text") or "") for s in (segments or []))
    if not sample_text.strip() and raw_words:
        sample_text = " ".join((w.get("word") or "") for w in raw_words)

    font_name, script = resolve_font_name(font, custom_font_name, language_mode, sample_text)
    rtl = is_rtl_script(script)

    ass_color = _color_to_ass(color)
    hl_color = _color_to_ass(highlight_color)
    alignment = POSITION_MAP.get(position, 2)
    effective_size = _scale_font_size(font_size, video_height)
    effective_margin = max(int(round(margin_v * (video_height / 1920.0))), 10)

    outline_width = max(int(round(effective_size * 0.055)), 2) if outline else 0
    shadow = 1 if outline else 0
    border_style = 3 if background_box else 1     # 3 = opaque box, 1 = outline+shadow
    if background_box:
        outline_width = max(int(round(effective_size * 0.18)), 6)   # box ka padding
        shadow = 0

    bold_flag = 1 if bold else 0
    side_margin = int(video_width * 0.055)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes
WrapStyle: 0
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{effective_size},{ass_color},&H000000FF,&H00000000,&H90000000,{bold_flag},0,0,0,100,100,0,0,{border_style},{outline_width},{shadow},{alignment},{side_margin},{side_margin},{effective_margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    anim = _animation_tag(animation)
    events = []

    def add_event(start, end, text):
        if end <= start:
            end = start + 0.05
        events.append(
            f"Dialogue: 0,{_format_ass_time(start)},{_format_ass_time(end)},Default,,0,0,0,,{anim}{text}"
        )

    def prep(text: str) -> str:
        return (text or "").upper() if all_caps else (text or "")

    # RTL scripts ke liye ASS mein har line ke shuru mein RLE mark lagate hain
    rtl_prefix = "‫" if rtl else ""

    def styled(text: str) -> str:
        return rtl_prefix + _escape_ass_text(text)

    segments = segments or []

    # ---------- MODE 1: LINE (poori line ek sath) ----------
    if mode == "line" or not raw_words:
        for seg in segments:
            try:
                start = float(seg.get("start", 0))
                end = float(seg.get("end", start))
            except (TypeError, ValueError):
                continue
            text = prep((seg.get("text") or "").strip())
            if not text:
                continue
            wrapped = wrap_text(text, script, max_chars_per_line)
            add_event(start, end, styled(wrapped))

    # ---------- MODE 2: WORD (ek waqt mein ek word) ----------
    elif mode == "word":
        for seg in segments:
            try:
                seg_start = float(seg.get("start", 0))
                seg_end = float(seg.get("end", seg_start))
            except (TypeError, ValueError):
                continue

            # BUG FIX: sirf iss segment ke andar wale words (pehle poora
            # transcript use hota tha, isliye captions video se lambi ho jati thin)
            words = _words_in_range(raw_words, seg_start, seg_end)
            if not words:
                text = prep((seg.get("text") or "").strip())
                if text:
                    add_event(seg_start, seg_end, styled(wrap_text(text, script, max_chars_per_line)))
                continue

            for idx, w in enumerate(words):
                try:
                    w_start = max(float(w["start"]), seg_start)
                    w_end = float(w.get("end", w_start))
                except (KeyError, TypeError, ValueError):
                    continue
                # Agla word aane tak dikhao (gap mein caption gayab na ho)
                if idx + 1 < len(words):
                    try:
                        w_end = max(w_end, float(words[idx + 1]["start"]) - 0.01)
                    except (KeyError, TypeError, ValueError):
                        pass
                else:
                    w_end = max(w_end, min(seg_end, w_end))
                w_end = min(w_end, seg_end)
                word_text = prep((w.get("word") or "").strip())
                if not word_text:
                    continue
                add_event(w_start, w_end, styled(word_text))

    # ---------- MODE 3: KARAOKE (poori line, bolne wala word highlight) ----------
    else:
        for seg in segments:
            try:
                seg_start = float(seg.get("start", 0))
                seg_end = float(seg.get("end", seg_start))
            except (TypeError, ValueError):
                continue

            words = _words_in_range(raw_words, seg_start, seg_end)
            if not words:
                text = prep((seg.get("text") or "").strip())
                if text:
                    add_event(seg_start, seg_end, styled(wrap_text(text, script, max_chars_per_line)))
                continue

            word_texts = [prep((w.get("word") or "").strip()) for w in words]
            line_groups = _wrap_words(word_texts, script, max_chars_per_line)

            # Har word ka (line_index, position_in_line) map banate hain
            flat_index = 0
            index_map = {}
            for line_i, line_words in enumerate(line_groups):
                for pos in range(len(line_words)):
                    index_map[flat_index] = (line_i, pos)
                    flat_index += 1

            for idx, w in enumerate(words):
                if not word_texts[idx]:
                    continue
                try:
                    w_start = max(float(w["start"]), seg_start)
                    w_end = float(w.get("end", w_start))
                except (KeyError, TypeError, ValueError):
                    continue
                if idx + 1 < len(words):
                    try:
                        w_end = max(w_end, float(words[idx + 1]["start"]) - 0.01)
                    except (KeyError, TypeError, ValueError):
                        pass
                w_end = min(max(w_end, w_start + 0.05), seg_end)

                active = index_map.get(idx)
                rendered_lines = []
                for line_i, line_words in enumerate(line_groups):
                    parts = []
                    for pos, word in enumerate(line_words):
                        escaped = _escape_ass_text(word)
                        if active and active == (line_i, pos):
                            parts.append(f"{{\\c{hl_color}}}{escaped}{{\\c{ass_color}}}")
                        else:
                            parts.append(escaped)
                    rendered_lines.append(" ".join(parts))
                body = rtl_prefix + "\\N".join(rendered_lines)
                add_event(w_start, w_end, body)

    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(header)
        f.write("\n".join(events))
        f.write("\n")

    return {
        "path": output_path,
        "events": len(events),
        "font_name": font_name,
        "script": script,
        "rtl": rtl,
        "font_size": effective_size,
        "mode": mode,
    }


def get_burn_filter(ass_path: str) -> str:
    """
    FFmpeg 'subtitles' filter string banata hai. Windows paths mein backslash
    aur colon ko escape karna zaroori hai warna filtergraph parse fail hota hai.
    """
    path = os.path.abspath(ass_path).replace("\\", "/")
    path = path.replace(":", "\\:").replace("'", "\\'")
    fonts_dir = os.path.dirname(os.path.abspath(ass_path)).replace("\\", "/").replace(":", "\\:")
    return f"subtitles=filename='{path}':fontsdir='{fonts_dir}'"


