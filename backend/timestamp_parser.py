"""
Timestamp file parser.

Do formats support karte hain:
1. Word-level JSON: [{"word": "hello", "start": 0.52, "end": 0.81}, ...]
2. SRT file: standard subtitle format with numbered blocks + time ranges + text

Dono ko ek common format mein convert karte hain: list of segments,
har segment mein { start, end, text }.
"""

import json
import re


def parse_word_json(raw_text: str):
    """Word-level JSON parse karke groups mein todta hai (~4 second ke segments)."""
    data = json.loads(raw_text)

    # Agar {"words": [...]} wrapper hai to andar se nikal lo
    if isinstance(data, dict) and "words" in data:
        data = data["words"]

    if not isinstance(data, list) or not data:
        raise ValueError("JSON file mein 'word/start/end' wali list honi chahiye.")

    segments = []
    current_words = []
    current_start = None
    SEGMENT_MAX_DURATION = 4.0  # har segment ~4 second ka

    for item in data:
        word = item.get("word") or item.get("text") or ""
        start = float(item.get("start", 0))
        end = float(item.get("end", start))

        if current_start is None:
            current_start = start

        current_words.append(word)

        if (end - current_start) >= SEGMENT_MAX_DURATION:
            segments.append({
                "start": round(current_start, 2),
                "end": round(end, 2),
                "text": " ".join(current_words).strip()
            })
            current_words = []
            current_start = None

    # Bacha hua hissa bhi ek segment ban jaye
    if current_words:
        segments.append({
            "start": round(current_start, 2),
            "end": round(end, 2),
            "text": " ".join(current_words).strip()
        })

    return segments


def srt_time_to_seconds(t: str) -> float:
    """'00:00:04,320' jaise format ko seconds mein convert karta hai."""
    t = t.replace(",", ".")
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_srt(raw_text: str):
    """Standard .srt file parse karta hai."""
    blocks = re.split(r"\n\s*\n", raw_text.strip())
    segments = []

    for block in blocks:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 2:
            continue

        time_line_idx = 0
        for i, line in enumerate(lines):
            if "-->" in line:
                time_line_idx = i
                break

        time_line = lines[time_line_idx]
        text_lines = lines[time_line_idx + 1:]

        start_str, end_str = [p.strip() for p in time_line.split("-->")]
        start = srt_time_to_seconds(start_str)
        end = srt_time_to_seconds(end_str)
        text = " ".join(text_lines)

        segments.append({"start": round(start, 2), "end": round(end, 2), "text": text})

    if not segments:
        raise ValueError("SRT file parse nahi ho saki — format check karein.")

    return segments


def extract_raw_words(filename: str, raw_text: str):
    """
    Agar file word-level JSON hai, to raw {word, start, end} list deta hai
    (Scene-Mapping feature ke liye zaroori — SRT files mein ye granularity
    nahi hoti, isliye SRT ke liye None deta hai).
    """
    if not filename.lower().endswith(".json"):
        # Try karte hain — shayad extension na ho lekin content JSON ho
        try:
            data = json.loads(raw_text)
        except Exception:
            return None
    else:
        data = json.loads(raw_text)

    if isinstance(data, dict) and "words" in data:
        data = data["words"]

    if not isinstance(data, list) or not data:
        return None

    raw_words = []
    for item in data:
        word = item.get("word") or item.get("text") or ""
        if not word:
            continue
        start = float(item.get("start", 0))
        end = float(item.get("end", start))
        raw_words.append({"word": word, "start": round(start, 3), "end": round(end, 3)})

    return raw_words if raw_words else None


# --------------------------- multilingual sentence engine ---------------------------
# Har tarah ki language ke sentence-end nishaan (sirf English . ! ? nahi):
#   Latin/Cyrillic/Greek: . ! ? …   |  Arabic/Urdu/Farsi: ۔ ؟ ! ٫
#   CJK (Chinese/Japanese/Korean): 。 ！ ？ ｡ ． ‥ …
#   Devanagari/Bengali: । ॥        |  Armenian: ։ ՞ ՜  |  Ethiopic: ። ፧ ፨
SENTENCE_ENDERS = ".!?…‽"          # . ! ? … ‽
SENTENCE_ENDERS += "۔؟؛"                      # ۔ ؟ ؛  (Urdu/Arabic)
SENTENCE_ENDERS += "。！？｡．‥"    # 。！？｡．‥ (CJK)
SENTENCE_ENDERS += "।॥"                            # । ॥ (Devanagari/Bengali)
SENTENCE_ENDERS += "։՜՞"                      # ։ ՜ ՞ (Armenian)
SENTENCE_ENDERS += "።፧፨"                      # ። ፧ ፨ (Ethiopic)
SENTENCE_ENDERS += "។ฯ၊။"                # ។ ฯ ။ (Khmer/Thai/Burmese)

# Sentence ke baad aane wale closing nishaan (quote/bracket) — inko sentence
# ka hissa maante hain, naya sentence yahan se shuru nahi hota
CLOSERS = "\"'’”』」）)]}»›〉】"

# Jab script mein koi punctuation hi na ho (kuch ASR outputs, ya bina
# punctuation wali languages), tab KHAMOSHI (pause) se sentence todte hain
PAUSE_GAP = 0.45          # itni khamoshi = sentence boundary
MIN_SENTENCE_SEC = 1.2    # is se chhoti "sentence" nahi banati (over-split se bachao)

# Wo scripts jo words ke darmiyan space nahi lagati — text jodte waqt space nahi dalna
_NO_SPACE_RANGES = (
    (0x3040, 0x30ff),   # Hiragana + Katakana
    (0x3400, 0x4dbf),   # CJK ext A
    (0x4e00, 0x9fff),   # CJK unified
    (0xf900, 0xfaff),   # CJK compat
    (0xac00, 0xd7af),   # Hangul syllables (Korean me space hota hai, neeche handle)
    (0x0e00, 0x0e7f),   # Thai
    (0x1780, 0x17ff),   # Khmer
)


def _is_no_space_char(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _NO_SPACE_RANGES)


def _needs_space(text: str) -> bool:
    """CJK/Thai/Khmer jaisi script ho to words ko bina space jodte hain."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return True
    no_space = sum(1 for c in letters if _is_no_space_char(c) and not (0xac00 <= ord(c) <= 0xd7af))
    return (no_space / len(letters)) < 0.5


def join_words(words: list) -> str:
    """Word list ko us language ke hisaab se text banata hai."""
    raw = "".join(w["word"] for w in words)
    if not _needs_space(raw):
        return "".join(w["word"] for w in words).strip()
    return " ".join(w["word"] for w in words).strip()


def _split_token_on_enders(token: dict) -> list:
    """
    Ek token ke ANDAR agar sentence-end nishaan hai (jaise Japanese/Chinese
    mein poora "これは私の話です。次の話。" ek hi token ho sakta hai), to usko
    chhote hisson mein todta hai aur time ko character-count ke hisaab se
    proportionally baant deta hai. Har hissa {word, start, end, ends} deta hai.
    """
    text = token["word"]
    start, end = float(token["start"]), float(token["end"])
    pieces, buf = [], ""
    i = 0
    while i < len(text):
        ch = text[i]
        buf += ch
        i += 1
        if ch in SENTENCE_ENDERS:
            # sentence ke baad ke closing quotes/brackets bhi isi hisse mein
            while i < len(text) and text[i] in CLOSERS:
                buf += text[i]
                i += 1
            pieces.append((buf, True))
            buf = ""
    if buf:
        pieces.append((buf, False))
    # Sirf ek hissa, ya koi split nahi — token waisa hi
    if len(pieces) <= 1:
        ends = bool(pieces) and pieces[0][1]
        return [{"word": text, "start": start, "end": end, "ends": ends}]

    # Time ko characters ke hisaab se baant do (last piece ka end = token ka end)
    total_chars = sum(len(p[0]) for p in pieces) or 1
    out, cursor, used = [], start, 0
    span = max(end - start, 0.0)
    for i, (piece_text, ends) in enumerate(pieces):
        used += len(piece_text)
        piece_end = end if i == len(pieces) - 1 else round(start + span * (used / total_chars), 3)
        out.append({"word": piece_text, "start": round(cursor, 3),
                    "end": max(piece_end, round(cursor, 3)), "ends": ends})
        cursor = piece_end
    return out


def split_sentences(raw_words: list) -> list:
    """
    Word-level list ko sentences (list of word-lists) mein todta hai —
    HAR language ke liye. Teen tareeqe, isi tarteeb se:
      1. Sentence-end punctuation (kisi bhi script ka)
      2. Token ke andar ka punctuation (space-less CJK ke liye char-level split)
      3. Agar punctuation hi na mile — khamoshi (pause) se boundary
    """
    if not raw_words:
        return []

    tokens = []
    for w in raw_words:
        word = str(w.get("word", ""))
        if not word.strip():
            continue
        tokens.extend(_split_token_on_enders(
            {"word": word, "start": float(w.get("start", 0)), "end": float(w.get("end", w.get("start", 0)))}
        ))

    if not tokens:
        return []

    sentences, current = [], []
    for tk in tokens:
        current.append({"word": tk["word"], "start": tk["start"], "end": tk["end"]})
        if tk["ends"]:
            sentences.append(current)
            current = []
    if current:
        sentences.append(current)

    # Punctuation se kuch na mila (sab ek hi sentence) — pause se todte hain
    if len(sentences) <= 1 and len(tokens) > 3:
        sentences, current = [], []
        for i, tk in enumerate(tokens):
            current.append({"word": tk["word"], "start": tk["start"], "end": tk["end"]})
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            if nxt is None:
                continue
            gap = nxt["start"] - tk["end"]
            long_enough = (tk["end"] - current[0]["start"]) >= MIN_SENTENCE_SEC
            if gap >= PAUSE_GAP and long_enough:
                sentences.append(current)
                current = []
        if current:
            sentences.append(current)

    return [s for s in sentences if s]


def group_words_by_sentences(raw_words: list, sentences_per_group: int = 1):
    """
    Raw words ko sentences mein todta hai (har language — punctuation ya pause
    se, dekhein split_sentences) aur phir N sentences = 1 scene ke hisaab se
    segments banata hai. Scene count is option ke sath khud kam/zyada hota hai.
    """
    sentences = split_sentences(raw_words)
    if not sentences:
        return []

    step = max(int(sentences_per_group or 1), 1)
    segments = []
    for i in range(0, len(sentences), step):
        words = [w for sent in sentences[i:i + step] for w in sent]
        if not words:
            continue
        segments.append({
            "start": round(words[0]["start"], 2),
            "end": round(words[-1]["end"], 2),
            "text": join_words(words),
        })
    return segments


def count_sentences(raw_words: list) -> int:
    """UI ko batane ke liye: is voice/script mein kitne sentences bane."""
    return len(split_sentences(raw_words))


def parse_timestamp_file(filename: str, raw_text: str):
    """File extension dekh kar sahi parser use karta hai."""
    if filename.lower().endswith(".srt"):
        return parse_srt(raw_text)
    elif filename.lower().endswith(".json"):
        return parse_word_json(raw_text)
    else:
        # Try JSON first, warna SRT try karo
        try:
            return parse_word_json(raw_text)
        except Exception:
            return parse_srt(raw_text)
