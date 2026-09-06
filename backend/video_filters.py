"""
Video Filters/Color-Grading Module.

Har preset ek FFmpeg video-filter string return karta hai jo poori video
(ya kisi specific segment) pe apply ho sakta hai.
"""

FILTER_PRESETS = {
    "none": "",

    # 4K/HD jaisa sharp, crisp, enhanced look — asal resolution nahi badalta,
    # bas clarity/detail zyada crisp dikhati hai (sharpening + halka contrast boost)
    "hd_enhance": "unsharp=5:5:1.0:5:5:0.0,eq=contrast=1.08:saturation=1.05",

    "black_white": "hue=s=0",

    "vintage": "curves=vintage,colorbalance=rs=0.15:gs=0.05:bs=-0.15,eq=saturation=0.85",

    "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",

    "cinematic": "eq=contrast=1.15:saturation=1.1:brightness=-0.02,curves=preset=darker",

    "warm": "colorbalance=rs=0.2:gs=0.05:bs=-0.15",

    "cool": "colorbalance=rs=-0.15:gs=0.0:bs=0.2",

    "vignette": "vignette=PI/4",

    "vibrant": "eq=saturation=1.4:contrast=1.1",

    "muted": "eq=saturation=0.6:contrast=0.95",

    "high_contrast": "eq=contrast=1.35",

    "faded": "eq=contrast=0.85:brightness=0.05:saturation=0.7",
}

FILTER_LABELS = {
    "none": "Koi Filter Nahi",
    "hd_enhance": "HD/4K Enhance (Sharp & Crisp)",
    "black_white": "Black & White",
    "vintage": "Vintage",
    "sepia": "Sepia",
    "cinematic": "Cinematic",
    "warm": "Warm Tone",
    "cool": "Cool Tone",
    "vignette": "Vignette",
    "vibrant": "Vibrant",
    "muted": "Muted",
    "high_contrast": "High Contrast",
    "faded": "Faded",
}


def get_filter_string(preset_name: str) -> str:
    """Preset ka naam leke uska FFmpeg filter-string deta hai. Unknown ho to khali string."""
    return FILTER_PRESETS.get(preset_name, "")
