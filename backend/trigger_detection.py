"""
Smart Trigger Detection Module.

Voice ke transcript (raw_words) mein agar "subscribe", "like", "bell" jaise
trigger words bole gaye hon, to automatically us exact waqt par matching
sticker place kar deta hai — user ko manually kuch nahi karna padta.
"""

import re

# Trigger word -> sticker key
TRIGGER_WORD_MAP = {
    "subscribe": "youtube_subscribe",
    "subscribed": "youtube_subscribe",
    "subscribing": "youtube_subscribe",
    "like": "thumbsup",
    "liked": "thumbsup",
    "bell": "bell",
    "notification": "bell",
    "notifications": "bell",
    "follow": "youtube_subscribe",
    "following": "youtube_subscribe",
    "comment": "arrow_down",
    "comments": "arrow_down",
}


def _normalize(word: str) -> str:
    return re.sub(r"[^a-z]", "", word.lower())


def detect_sticker_triggers(raw_words: list, default_position: str = "bottom_center",
                             default_duration: float = 2.5, default_scale: float = 0.25) -> list:
    """
    raw_words: [{"word": "...", "start": float, "end": float}, ...]
    Returns: sticker config list (jaisa manual stickers ka format hota hai) —
    [{"sticker_key", "position", "scale", "times": [{"start", "duration"}]}]

    Agar same sticker multiple baar trigger ho (jaise "subscribe" 2 baar bola
    gaya), to unki saari times ek hi sticker-entry mein group ho jati hain.
    """
    if not raw_words:
        return []

    grouped = {}  # sticker_key -> list of {start, duration}

    for w in raw_words:
        normalized = _normalize(w.get("word", ""))
        sticker_key = TRIGGER_WORD_MAP.get(normalized)
        if sticker_key:
            grouped.setdefault(sticker_key, []).append({
                "start": round(w["start"], 2),
                "duration": default_duration,
            })

    stickers = []
    for sticker_key, times in grouped.items():
        stickers.append({
            "sticker_key": sticker_key,
            "position": default_position,
            "scale": default_scale,
            "times": times,
        })

    return stickers
