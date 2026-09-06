"""
Scene-Mapping Module.

User do files deta hai:
1. Timestamp file (word-level) — har word ka exact time
2. Scene-Mapping file — har scene number ke sath uska poora narration text, jaise:

   Scene 1
   The line is walking down the street.

   Scene 2
   He stopped and looked around confused.

Ye module Scene ke text ko timestamp ke raw words ke sath "align" karta hai,
taake har scene ka EXACT start/end time nikal sake — chahe scene 1
sentence ka ho ya 5 sentences ka, timing hamesha sahi milegi.
"""

import re
from difflib import SequenceMatcher

# "Scene 1" header — kisi bhi language mein ho sakta hai (ya sirf number bhi):
#   Scene 1 / SCENE 1: / Сцена 1 / シーン1 / 场景1 / 장면 1 / سین 1 / منظر ١ / सीन 1 / 1.
SCENE_WORDS = (
    "scene", "scenes", "сцена", "シーン", "场景", "場景", "장면", "씬",
    "سین", "منظر", "سین نمبر", "सीन", "दृश्य", "দৃশ্য", "sahne", "escena",
    "scène", "cena", "adegan", "ฉาก", "მოქმედება",
)
SCENE_HEADER_PATTERN = re.compile(
    r"^\s*(?:" + "|".join(re.escape(w) for w in SCENE_WORDS) + r")?\s*[#:\-]?\s*(\d+)\s*[:.\-–)]?\s*$",
    re.IGNORECASE,
)


def parse_scene_file(raw_text: str):
    """
    Scene-mapping text file ko parse karta hai.
    Format: 'Scene N' ek line pe, uske baad narration text (1 ya zyada lines),
    khali line se agla scene shuru hota hai.
    Returns: [{"scene_number": 1, "text": "..."}, ...]
    """
    lines = raw_text.splitlines()
    scenes = []
    current_scene_num = None
    current_text_lines = []

    def flush():
        if current_scene_num is not None:
            text = " ".join(l.strip() for l in current_text_lines if l.strip()).strip()
            if text:
                scenes.append({"scene_number": current_scene_num, "text": text})

    for line in lines:
        header_match = SCENE_HEADER_PATTERN.match(line)
        if header_match:
            flush()
            current_scene_num = int(header_match.group(1))
            current_text_lines = []
        else:
            if current_scene_num is not None:
                current_text_lines.append(line)

    flush()

    if not scenes:
        raise ValueError("Scene file parse nahi ho saki. Format 'Scene 1' (line) phir uske neeche text hona chahiye.")

    return scenes


def _normalize(word: str) -> str:
    """
    Punctuation hata kar, lowercase karke compare karne layak banata hai.
    UNICODE-safe: Japanese/Korean/Chinese/Russian/Urdu/Hindi ke characters
    zinda rehte hain (pehle sirf a-z0-9 bachta tha, is se non-English script
    khali ho jati thi aur matching chup-chaap ghalat timing de deti thi).
    """
    return re.sub(r"[^\w']", "", str(word).casefold(), flags=re.UNICODE)


def _normalize_text(text: str) -> str:
    """Poore text ko ek normalized character-stream bana deta hai (space bhi hata kar)
    — taake space-less scripts (Japanese/Chinese/Thai) bhi theek match hon."""
    return "".join(_normalize(part) for part in str(text).split())


def _build_char_index(raw_words: list):
    """Raw words ka normalized character stream + har char ka word-index."""
    chars, owner = [], []
    for i, w in enumerate(raw_words):
        for c in _normalize(w.get("word", "")):
            chars.append(c)
            owner.append(i)
    return "".join(chars), owner


def match_scenes_to_timestamps(scenes: list, raw_words: list, min_confidence: float = 0.5):
    """
    Har scene ke text ko raw_words (timestamp data) ke sath align karta hai,
    taake exact start/end time mil sake — HAR language mein.

    Matching character-level hoti hai (word-level nahi), isliye un scripts par
    bhi chalti hai jinme words ke darmiyan space nahi hota (Japanese, Chinese,
    Thai) aur un par bhi jinme hota hai (English, Russian, Urdu, Hindi).

    scenes: [{"scene_number": 1, "text": "..."}]
    raw_words: [{"word": "Hello", "start": 0.0, "end": 0.5}, ...] (poori script, order mein)

    Returns: [{"scene_number", "text", "start", "end", "match_confidence", "low_confidence"}]
    """
    if not raw_words:
        raise ValueError("Scene-Mapping ke liye word-level timestamp data zaroori hai.")

    raw_chars, owner = _build_char_index(raw_words)
    total = len(raw_chars)
    if total == 0:
        raise ValueError("Timestamp file ke words khali hain — scene matching nahi ho sakti.")

    pointer = 0   # character pointer: yahan tak match ho chuka hai
    results = []

    for scene in scenes:
        needle = _normalize_text(scene.get("text", ""))
        if not needle:
            continue

        confidence = 0.0
        start_idx = end_idx = None

        if pointer < total:
            # Sirf pointer ke aage ka mehdood hissa dekhte hain (200-300 scenes par bhi tez)
            window_len = min(int(len(needle) * 2) + 80, total - pointer)
            hay = raw_chars[pointer:pointer + window_len]
            matcher = SequenceMatcher(None, hay, needle, autojunk=False)
            blocks = [b for b in matcher.get_matching_blocks() if b.size > 0]
            if blocks:
                start_idx = pointer + blocks[0].a
                end_idx = pointer + blocks[-1].a + blocks[-1].size
                confidence = sum(b.size for b in blocks) / len(needle)

        low_confidence = False
        if confidence >= min_confidence and start_idx is not None and end_idx > start_idx:
            start_word = owner[min(start_idx, total - 1)]
            end_word = owner[min(end_idx - 1, total - 1)]
            pointer = end_idx
        else:
            # Match nahi mila — sequential fallback (aur user ko warning milegi)
            low_confidence = True
            fallback_end = min(pointer + len(needle), total)
            if fallback_end <= pointer:
                fallback_end = min(pointer + 1, total)
            start_word = owner[min(pointer, total - 1)]
            end_word = owner[min(max(fallback_end - 1, 0), total - 1)]
            pointer = fallback_end

        start_time = float(raw_words[start_word]["start"])
        end_time = float(raw_words[end_word]["end"])
        if end_time <= start_time:
            end_time = start_time + 0.5

        results.append({
            "scene_number": scene["scene_number"],
            "text": scene["text"],
            "start": round(start_time, 2),
            "end": round(end_time, 2),
            "match_confidence": round(confidence, 2),
            "low_confidence": low_confidence,
        })

    return results


# --------------------------- Scene TIME TABLE (paste ya file) ---------------------------
# User ke liye sabse tez rasta: scene number + start + end ki rows, seedha
# Excel/Sheets se copy-paste. Is mein word-level JSON ki zarurat NAHI —
# timing user khud de raha hai. 200-300 rows bhi bilkul theek chalti hain.

_TIME_SPLIT = re.compile(r"[\t,;|]+")


def parse_time_value(value: str) -> float:
    """
    Time ko seconds mein badalta hai. Ye sab formats chalte hain:
      12.5 | 12,5 | 00:04.5 | 4:05 | 00:01:20.5 | 00:01:20,500 | 1m20s
    """
    text = str(value).strip().replace("،", "").replace("s", "").strip()
    if not text:
        raise ValueError("khali time")
    text = text.replace("m", ":")
    if ":" in text:
        parts = [p.strip().replace(",", ".") for p in text.split(":") if p.strip() != ""]
        if not parts:
            raise ValueError("time parse nahi hui")
        parts = [float(p) for p in parts]
        seconds = 0.0
        for p in parts:
            seconds = seconds * 60 + p
        return round(seconds, 3)
    return round(float(text.replace(",", ".")), 3)


_HEADER_WORDS = ("start", "end", "scene", "time", "شروع", "اختتام", "سین",
                 "开始", "结束", "场景", "начало", "конец", "сцена", "शुरू", "अंत")


def _looks_like_header(cells: list) -> bool:
    """Row header/kachra hai ya asli time row — 2 parse-hone wale time chahiye."""
    parsed = 0
    for c in cells[:3]:
        try:
            parse_time_value(re.sub(r"(?i)^scene\s*", "", c))
            parsed += 1
        except Exception:
            pass
    return parsed < 2


def parse_scene_time_table(raw_text: str):
    """
    Scene time table parse karta hai (paste box ya .csv/.tsv/.txt file).

    Har row: scene_number, start, end   (tab / comma / semicolon / pipe se alag)
    - Header row ("scene, start, end") khud pehchan kar chhod di jati hai
    - 2 columns wali rows bhi chalti hain: start, end (scene number khud lagta hai)
    - 4th column (text/description) ho to wo scene ka text ban jata hai
    - "Scene 1" jaisa prefix bhi chalta hai

    Returns: [{"scene_number", "start", "end", "text"}] — start ke hisaab se sorted
    """
    rows = []
    errors = []
    for line_no, line in enumerate(str(raw_text).splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        cells = [c.strip() for c in _TIME_SPLIT.split(stripped) if c.strip() != ""]
        if len(cells) < 2:
            cells = [c for c in re.split(r"\s{2,}|\s+", stripped) if c]
        if len(cells) < 2:
            errors.append(f"line {line_no}: kam columns")
            continue

        # Header row ("scene | start | end") ya kachra line — agar row mein
        # do parse-hone wale time hi na hon to isko row nahi maante.
        joined = " ".join(cells).lower()
        if _looks_like_header(cells):
            if not any(k in joined for k in _HEADER_WORDS):
                errors.append(f"line {line_no}: is line mein time nahi mila")
            continue

        scene_no = None
        first = re.sub(r"(?i)^scene\s*", "", cells[0]).strip()
        try:
            if len(cells) >= 3 and re.fullmatch(r"\d+", first):
                scene_no = int(first)
                start_raw, end_raw = cells[1], cells[2]
                text = " ".join(cells[3:]).strip()
            else:
                start_raw, end_raw = cells[0], cells[1]
                text = " ".join(cells[2:]).strip()
        except Exception:
            errors.append(f"line {line_no}: columns samajh nahi aaye")
            continue

        try:
            start = parse_time_value(start_raw)
            end = parse_time_value(end_raw)
        except Exception:
            errors.append(f"line {line_no}: time '{start_raw} / {end_raw}' parse nahi hui")
            continue

        if end <= start:
            errors.append(f"line {line_no}: end ({end}) start ({start}) se bada hona chahiye")
            continue

        rows.append({"scene_number": scene_no, "start": start, "end": end, "text": text})

    if not rows:
        detail = "; ".join(errors[:3])
        raise ValueError(
            "Scene time table parse nahi ho saki. Har row aisi honi chahiye: "
            "scene number, start, end (jaise '1, 0.0, 4.5' ya '1 | 00:00.0 | 00:04.5')."
            + (f" Misaal masail: {detail}" if detail else "")
        )

    rows.sort(key=lambda r: r["start"])
    for i, r in enumerate(rows, start=1):
        if r["scene_number"] is None:
            r["scene_number"] = i

    return rows, errors


def scene_table_to_segments(rows: list, raw_words: list = None):
    """
    Time table rows ko render-ready segments mein badalta hai.
    Agar word-level data maujood ho aur row mein text na ho, to us waqt ke
    words se text khud bhar dete hain (captions ke liye faidemand).
    Overlap ho to warning list mein aata hai (timing user ki hai, badalte nahi).
    """
    segments, warnings = [], []
    prev_end = None
    for i, r in enumerate(rows):
        text = r.get("text") or ""
        if not text and raw_words:
            picked = [w for w in raw_words
                      if float(w.get("start", 0)) < r["end"] and float(w.get("end", 0)) > r["start"]]
            if picked:
                from timestamp_parser import join_words
                text = join_words(picked)
        if prev_end is not None and r["start"] + 0.001 < prev_end:
            warnings.append(f"Scene {r['scene_number']} ka start ({r['start']}s) pichle scene ke end ({prev_end}s) se pehle hai — overlap.")
        prev_end = r["end"]
        segments.append({
            "start": round(r["start"], 2),
            "end": round(r["end"], 2),
            "text": text,
            "scene_number": r["scene_number"],
        })
    return segments, warnings
