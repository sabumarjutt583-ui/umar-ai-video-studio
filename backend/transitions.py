"""
Transitions Module (Expanded Library).

FFmpeg ka built-in 'xfade' filter dozens of professional transitions deta hai.
Hum inme se best curate karte hain, aur "Auto" mode ke liye rotate karte hain.

ZAROORI (Duration-Safety):
xfade se do clips jodne par total duration thodi kam ho jati hai (overlap
consume hota hai). Isse voice-sync na toote, iske liye har clip (pehli
chhod kar) ko uske "assigned duration + transition_duration" tak thoda
LAMBA banate hain — taake overlap consume hone ke baad bhi total timeline
length EXACTLY utni hi rahe jitni segments ki asal durations ka sum hai.
"""

# Friendly label -> FFmpeg xfade transition name
XFADE_TRANSITIONS = {
    "dissolve": "dissolve",       # "Mix" — CapCut jaisa smooth blend
    "wipe_left": "wipeleft",
    "wipe_right": "wiperight",
    "wipe_up": "wipeup",
    "wipe_down": "wipedown",
    "slide_left": "slideleft",
    "slide_right": "slideright",
    "slide_up": "slideup",
    "slide_down": "slidedown",
    "zoom_in": "zoomin",
    "circle_open": "circleopen",
    "circle_close": "circleclose",
    "pixelize": "pixelize",
    "radial": "radial",
    "smooth_left": "smoothleft",
    "smooth_right": "smoothright",
    "diagonal_tl": "diagtl",
    "diagonal_br": "diagbr",
    "hblur": "hblur",
    "fade_black": "fadeblack",
    "fade_white": "fadewhite",
}

TRANSITION_LABELS = {
    "dissolve": "Mix / Dissolve",
    "wipe_left": "Wipe Left",
    "wipe_right": "Wipe Right",
    "wipe_up": "Wipe Up",
    "wipe_down": "Wipe Down",
    "slide_left": "Slide Left",
    "slide_right": "Slide Right",
    "slide_up": "Slide Up",
    "slide_down": "Slide Down",
    "zoom_in": "Zoom Transition",
    "circle_open": "Circle Open",
    "circle_close": "Circle Close",
    "pixelize": "Pixelize",
    "radial": "Radial Wipe",
    "smooth_left": "Smooth Left",
    "smooth_right": "Smooth Right",
    "diagonal_tl": "Diagonal (Top-Left)",
    "diagonal_br": "Diagonal (Bottom-Right)",
    "hblur": "Blur Transition",
    "fade_black": "Fade Through Black",
    "fade_white": "Fade Through White",
}

# "Auto" mode isi list mein se rotate karega (variety ke liye best-looking wale)
AUTO_ROTATE_TRANSITIONS = [
    "dissolve", "wipe_left", "slide_right", "zoom_in",
    "circle_open", "smooth_left", "wipe_up", "radial",
]

# Speed control -> transition duration (seconds). Chhota D = fast/quick transition,
# bada D = slow/lambi transition.
SPEED_TO_DURATION = {
    "fast": 0.3,
    "medium": 0.6,
    "slow": 1.0,
}


def get_xfade_name(transition_key: str) -> str:
    """Hamare friendly key se FFmpeg ka xfade transition-name deta hai."""
    return XFADE_TRANSITIONS.get(transition_key, "dissolve")


def get_transition_duration(speed: str) -> float:
    return SPEED_TO_DURATION.get(speed, 0.6)
