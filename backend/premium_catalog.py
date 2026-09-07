"""
Premium Studio Voices Catalog.
Routes each language to the highest quality engine:
- English (US & UK), Japanese, Chinese, French, Spanish: Kokoro-82M Studio HD (24kHz CD Audio)
- Urdu (Pakistan): Master Broadcast Neural HD (Asad & Uzma)
- Arabic (Saudi & UAE): Master Studio HD (Hamed, Zariyah, Hamdan)
- Korean: Master Studio HD (Hyunsu Multilingual - FameSpeak Hero, SunHi)
- Hindi & Indian English: Kokoro-82M + Master Neural
- German, Turkish, Russian: Master Studio HD
"""

PREMIUM_LANGUAGES = [
    {
        "id": "en",
        "name": "English (US & UK)",
        "flag": "🇺🇸/🇬🇧",
        "engine_label": "Kokoro-82M 24kHz HD",
        "badge": "CD Audio",
        "accent": "American & British Studio",
        "count": 14
    },
    {
        "id": "ur",
        "name": "Urdu (Pakistan)",
        "flag": "🇵🇰",
        "engine_label": "Master Broadcast HD",
        "badge": "Deep Bayan & Story",
        "accent": "Pakistani Urdu",
        "count": 2
    },
    {
        "id": "ar",
        "name": "Arabic (Saudi & UAE)",
        "flag": "🇸🇦",
        "engine_label": "Master Studio HD",
        "badge": "Classical & Khutbah",
        "accent": "Saudi, UAE & Egypt",
        "count": 4
    },
    {
        "id": "hi",
        "name": "Hindi / Indian",
        "flag": "🇮🇳",
        "engine_label": "Kokoro + Master HD",
        "badge": "Expressive Tone",
        "accent": "Indian Hindi & English",
        "count": 4
    },
    {
        "id": "ko",
        "name": "Korean (K-Drama)",
        "flag": "🇰🇷",
        "engine_label": "Master Studio HD",
        "badge": "FameSpeak Hero",
        "accent": "Seoul Korean",
        "count": 3
    },
    {
        "id": "es",
        "name": "Spanish (Español)",
        "flag": "🇪🇸",
        "engine_label": "Kokoro + Master HD",
        "badge": "Cinematic Story",
        "accent": "Castilian & Latin",
        "count": 4
    },
    {
        "id": "ja",
        "name": "Japanese (日本語)",
        "flag": "🇯🇵",
        "engine_label": "Kokoro Studio HD",
        "badge": "Anime & Docu",
        "accent": "Tokyo Japanese",
        "count": 4
    },
    {
        "id": "zh",
        "name": "Chinese (Mandarin)",
        "flag": "🇨🇳",
        "engine_label": "Kokoro Studio HD",
        "badge": "Broadcast Master",
        "accent": "Standard Mandarin",
        "count": 4
    },
    {
        "id": "tr",
        "name": "Turkish (Türkçe)",
        "flag": "🇹🇷",
        "engine_label": "Master Studio HD",
        "badge": "Drama & History",
        "accent": "Istanbul Turkish",
        "count": 2
    },
    {
        "id": "de",
        "name": "German (Deutsch)",
        "flag": "🇩🇪",
        "engine_label": "Master Studio HD",
        "badge": "Crisp Narration",
        "accent": "Standard German",
        "count": 2
    },
    {
        "id": "fr",
        "name": "French (Français)",
        "flag": "🇫🇷",
        "engine_label": "Kokoro + Master HD",
        "badge": "Smooth Articulate",
        "accent": "Parisian French",
        "count": 2
    },
    {
        "id": "ru",
        "name": "Russian (Русский)",
        "flag": "🇷🇺",
        "engine_label": "Master Studio HD",
        "badge": "Deep Baritone",
        "accent": "Standard Russian",
        "count": 2
    }
]

PREMIUM_VOICES = [
    # --- English (US & UK) [Kokoro-82M 24kHz CD Quality] ---
    {
        "id": "am_adam",
        "name": "Adam (Studio)",
        "gender": "Male",
        "language_id": "en",
        "flag": "🇺🇸",
        "accent": "American (US)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Deep Narration / Documentary",
        "sample": "In the depths of space, celestial bodies dance in an eternal cosmic ballet."
    },
    {
        "id": "am_michael",
        "name": "Michael (Studio)",
        "gender": "Male",
        "language_id": "en",
        "flag": "🇺🇸",
        "accent": "American (US)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Warm Explainer / YouTube",
        "sample": "Welcome back! Today we are examining how artificial intelligence is changing video creation."
    },
    {
        "id": "af_bella",
        "name": "Bella (Studio)",
        "gender": "Female",
        "language_id": "en",
        "flag": "🇺🇸",
        "accent": "American (US)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Expressive / Cinematic Story",
        "sample": "The silence in the grand library was broken only by the gentle turning of ancient pages."
    },
    {
        "id": "af_nicole",
        "name": "Nicole (Studio)",
        "gender": "Female",
        "language_id": "en",
        "flag": "🇺🇸",
        "accent": "American (US)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Commercial & Storyteller",
        "sample": "Imagine producing studio quality videos in seconds with zero recurring fees."
    },
    {
        "id": "af_heart",
        "name": "Heart (Studio)",
        "gender": "Female",
        "language_id": "en",
        "flag": "🇺🇸",
        "accent": "American (US)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Ultra Smooth & Natural",
        "sample": "True tranquility begins the moment you embrace the present moment."
    },
    {
        "id": "af_sarah",
        "name": "Sarah (Studio)",
        "gender": "Female",
        "language_id": "en",
        "flag": "🇺🇸",
        "accent": "American (US)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "News Anchor / Business",
        "sample": "Financial markets saw unprecedented technological growth throughout the past fiscal quarter."
    },
    {
        "id": "af_sky",
        "name": "Sky (Studio)",
        "gender": "Female",
        "language_id": "en",
        "flag": "🇺🇸",
        "accent": "American (US)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Youthful / Upbeat Shorts",
        "sample": "Check this out! You won't believe what happens when you try this simple productivity hack."
    },
    {
        "id": "am_liam",
        "name": "Liam (Studio)",
        "gender": "Male",
        "language_id": "en",
        "flag": "🇺🇸",
        "accent": "American (US)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Modern Podcast / Conversational",
        "sample": "Have you ever wondered why certain stories resonate with us for an entire lifetime?"
    },
    {
        "id": "am_eric",
        "name": "Eric (Studio)",
        "gender": "Male",
        "language_id": "en",
        "flag": "🇺🇸",
        "accent": "American (US)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Resonant Baritone / Audiobooks",
        "sample": "The traveler paused at the crossroad, knowing full well that each path led to a different fate."
    },
    {
        "id": "bm_george",
        "name": "George (Studio)",
        "gender": "Male",
        "language_id": "en",
        "flag": "🇬🇧",
        "accent": "British (UK)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "BBC Documentary / History",
        "sample": "Across the mist-covered moors, the ancient stone castle stood as a monument to resilience."
    },
    {
        "id": "bm_lewis",
        "name": "Lewis (Studio)",
        "gender": "Male",
        "language_id": "en",
        "flag": "🇬🇧",
        "accent": "British (UK)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "British Dynamic / Explainer",
        "sample": "Let us take a closer look at the intricate mechanics that power modern quantum computers."
    },
    {
        "id": "bf_emma",
        "name": "Emma (Studio)",
        "gender": "Female",
        "language_id": "en",
        "flag": "🇬🇧",
        "accent": "British (UK)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "British Articulate / Drama",
        "sample": "Sometimes the greatest truths are discovered in the quietest of moments."
    },
    {
        "id": "bf_isabella",
        "name": "Isabella (Studio)",
        "gender": "Female",
        "language_id": "en",
        "flag": "🇬🇧",
        "accent": "British (UK)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Sophisticated / Literature",
        "sample": "The morning sun poured gentle golden light over the garden pathways."
    },
    {
        "id": "bf_alice",
        "name": "Alice (Studio)",
        "gender": "Female",
        "language_id": "en",
        "flag": "🇬🇧",
        "accent": "British (UK)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Warm Storytelling / Fairy Tale",
        "sample": "Once upon a time in a secluded valley, a hidden kingdom flourished beneath the emerald trees."
    },

    # --- Urdu (Pakistan) [Master Broadcast Neural HD] ---
    {
        "id": "ur-PK-AsadNeural",
        "name": "Asad (اسد)",
        "gender": "Male",
        "language_id": "ur",
        "flag": "🇵🇰",
        "accent": "Pakistani Urdu",
        "engine": "master_neural",
        "engine_badge": "Master Broadcast HD",
        "category": "Deep Narration / Bayan / Documentary",
        "sample": "زندگی میں کامیابی کا راز مستقل مزاجی اور محنت میں پوشیدہ ہے۔"
    },
    {
        "id": "ur-PK-UzmaNeural",
        "name": "Uzma (عظمیٰ)",
        "gender": "Female",
        "language_id": "ur",
        "flag": "🇵🇰",
        "accent": "Pakistani Urdu",
        "engine": "master_neural",
        "engine_badge": "Master Broadcast HD",
        "category": "Cinematic Story / Commercial / Poetry",
        "sample": "ہر نیا دن اپنے ساتھ نئی امیدیں اور نئے خواب لے کر طلوع ہوتا ہے۔"
    },

    # --- Arabic (Saudi Arabia & UAE) [Master Studio HD] ---
    {
        "id": "ar-SA-HamedNeural",
        "name": "Hamed (حامد)",
        "gender": "Male",
        "language_id": "ar",
        "flag": "🇸🇦",
        "accent": "Saudi Arabia",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Deep Khutbah / Documentary / Quranic",
        "sample": "العلم نور يهدي الإنسان إلى طريق النجاح والفلاح في كل زمان ومكان."
    },
    {
        "id": "ar-SA-ZariyahNeural",
        "name": "Zariyah (زارية)",
        "gender": "Female",
        "language_id": "ar",
        "flag": "🇸🇦",
        "accent": "Saudi Arabia",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Articulate / Formal Documentary",
        "sample": "تاريخ الحضارات مليء بالإنجازات العظيمة التي بنيت بفضل العزيمة والإرادة."
    },
    {
        "id": "ar-AE-HamdanNeural",
        "name": "Hamdan (حمدان)",
        "gender": "Male",
        "language_id": "ar",
        "flag": "🇦🇪",
        "accent": "United Arab Emirates",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "UAE Modern / Commercial",
        "sample": "مرحباً بكم في عصر الابتكار والذكاء الاصطناعي الذي يغير مستقبل الأعمال."
    },
    {
        "id": "ar-EG-SalmaNeural",
        "name": "Salma (سلمى)",
        "gender": "Female",
        "language_id": "ar",
        "flag": "🇪🇬",
        "accent": "Egypt",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Egyptian / Story & Media",
        "sample": "القصص التاريخية تعيد إحياء المشاعر الإنسانية عبر الأجيال."
    },

    # --- Hindi & Indian English [Kokoro + Master HD] ---
    {
        "id": "hf_alpha",
        "name": "Alpha (Studio Hindi)",
        "gender": "Female",
        "language_id": "hi",
        "flag": "🇮🇳",
        "accent": "Indian Hindi",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Emotional Story / Audiobooks",
        "sample": "सपनों को सच करने के लिए सिर्फ सोचने से नहीं, बल्कि लगातार मेहनत करने से मंजिल मिलती है।"
    },
    {
        "id": "hm_omega",
        "name": "Omega (Studio Hindi)",
        "gender": "Male",
        "language_id": "hi",
        "flag": "🇮🇳",
        "accent": "Indian Hindi",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Deep Motivational / YouTube",
        "sample": "अगर आप जीवन में कुछ नया हासिल करना चाहते हैं, तो आपको उन रास्तों पर चलना होगा जो किसी ने नहीं चुने।"
    },
    {
        "id": "hi-IN-MadhurNeural",
        "name": "Madhur (मधुर)",
        "gender": "Male",
        "language_id": "hi",
        "flag": "🇮🇳",
        "accent": "Indian Hindi",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Explainer / YouTube Documentaries",
        "sample": "आज हम एक ऐसी ऐतिहासिक घटना के बारे में जानेंगे जिसने पूरी दुनिया का रुख बदल दिया।"
    },
    {
        "id": "hi-IN-SwaraNeural",
        "name": "Swara (स्वरा)",
        "gender": "Female",
        "language_id": "hi",
        "flag": "🇮🇳",
        "accent": "Indian Hindi",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Sweet / Dramatic Narration",
        "sample": "हर सुबह एक नया अवसर लेकर आती है, अपनी ऊर्जा को सही दिशा में लगाइए।"
    },

    # --- Korean [Master Studio HD / FameSpeak Hero] ---
    {
        "id": "ko-KR-HyunsuMultilingualNeural",
        "name": "Hyunsu (현수 - FameSpeak Hero)",
        "gender": "Male",
        "language_id": "ko",
        "flag": "🇰🇷",
        "accent": "Korean (Seoul)",
        "engine": "master_neural",
        "engine_badge": "FameSpeak Hero HD",
        "category": "K-Drama Narrator / Cinematic",
        "sample": "진정한 용기란 두려움이 없는 것이 아니라, 두려움 속에서도 한 걸음 더 나아가는 것입니다."
    },
    {
        "id": "ko-KR-SunHiNeural",
        "name": "Sun-Hi (선희)",
        "gender": "Female",
        "language_id": "ko",
        "flag": "🇰🇷",
        "accent": "Korean (Seoul)",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Emotional Story / K-Pop Vibe",
        "sample": "오늘 하루도 최선을 다한 당신에게 따뜻한 위로와 응원을 보냅니다."
    },
    {
        "id": "ko-KR-InJoonNeural",
        "name": "In-Joon (인준)",
        "gender": "Male",
        "language_id": "ko",
        "flag": "🇰🇷",
        "accent": "Korean (Seoul)",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Warm Documentary / News",
        "sample": "우리가 마주하는 모든 변화는 더 넓은 세상으로 나아가기 위한 디딤돌입니다."
    },

    # --- Spanish (Español) [Kokoro-82M + Master HD] ---
    {
        "id": "ef_dora",
        "name": "Dora (Studio)",
        "gender": "Female",
        "language_id": "es",
        "flag": "🇪🇸",
        "accent": "Spanish (Castilian)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Expressive / Audiobooks",
        "sample": "En un rincón del viejo castillo, un antiguo manuscrito guardaba los secretos del reino."
    },
    {
        "id": "em_alex",
        "name": "Alex (Studio)",
        "gender": "Male",
        "language_id": "es",
        "flag": "🇪🇸",
        "accent": "Spanish (Castilian)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Documentary / Explainer",
        "sample": "El universo continúa expandiéndose hacia fronteras que la mente humana apenas comienza a comprender."
    },
    {
        "id": "es-ES-AlvaroNeural",
        "name": "Alvaro (Álvaro)",
        "gender": "Male",
        "language_id": "es",
        "flag": "🇪🇸",
        "accent": "Spanish (Castilian)",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Deep Narration / Commercial",
        "sample": "Descubre una nueva forma de crear vídeos con inteligencia artificial de última generación."
    },
    {
        "id": "es-ES-ElviraNeural",
        "name": "Elvira (Elvira)",
        "gender": "Female",
        "language_id": "es",
        "flag": "🇪🇸",
        "accent": "Spanish (Castilian)",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Cinematic Storyteller",
        "sample": "Cada viaje comienza con un simple paso y la determinación de seguir adelante."
    },

    # --- Japanese (日本語) [Kokoro Studio HD] ---
    {
        "id": "jf_alpha",
        "name": "Alpha (Studio Nihongo)",
        "gender": "Female",
        "language_id": "ja",
        "flag": "🇯🇵",
        "accent": "Japanese (Tokyo)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Anime Story / Sweet Tone",
        "sample": "静かな森の中で、木々の間から差し込む光が美しい道を作っていました。"
    },
    {
        "id": "jf_gongitsune",
        "name": "Gongitsune (Studio)",
        "gender": "Female",
        "language_id": "ja",
        "flag": "🇯🇵",
        "accent": "Japanese (Tokyo)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Traditional Tale / Fairy Tale",
        "sample": "昔々あるところに、心優しい小さな狐が住んでおりました。"
    },
    {
        "id": "jm_kumo",
        "name": "Kumo (Studio)",
        "gender": "Male",
        "language_id": "ja",
        "flag": "🇯🇵",
        "accent": "Japanese (Tokyo)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Deep Documentary / Explainer",
        "sample": "最先端のテクノロジーは、私たちが未来を想像する方法そのものを変えつつあります。"
    },
    {
        "id": "ja-JP-NanamiNeural",
        "name": "Nanami (七海)",
        "gender": "Female",
        "language_id": "ja",
        "flag": "🇯🇵",
        "accent": "Japanese (Tokyo)",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Professional Broadcast / News",
        "sample": "本日のニュースをお伝えします。世界各地で新しい技術革新が進められています。"
    },

    # --- Chinese Mandarin [Kokoro Studio HD] ---
    {
        "id": "zf_xiaobei",
        "name": "Xiaobei (小贝)",
        "gender": "Female",
        "language_id": "zh",
        "flag": "🇨🇳",
        "accent": "Mandarin Chinese",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Warm Story / Audiobooks",
        "sample": "夜幕降临，繁华的城市逐渐安静下来，唯有路灯散发着温暖的光芒。"
    },
    {
        "id": "zf_xiaoxiao",
        "name": "Xiaoxiao (小小)",
        "gender": "Female",
        "language_id": "zh",
        "flag": "🇨🇳",
        "accent": "Mandarin Chinese",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Broadcast Anchor",
        "sample": "欢迎收看今天的科技前沿动态，人工智能正在引领新一轮创新浪潮。"
    },
    {
        "id": "zm_yunjian",
        "name": "Yunjian (云健)",
        "gender": "Male",
        "language_id": "zh",
        "flag": "🇨🇳",
        "accent": "Mandarin Chinese",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Deep Documentary",
        "sample": "探索浩瀚宇宙的奥秘，见证自然界中不可思议的奇迹。"
    },
    {
        "id": "zm_yunyang",
        "name": "Yunyang (云扬)",
        "gender": "Male",
        "language_id": "zh",
        "flag": "🇨🇳",
        "accent": "Mandarin Chinese",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Commercial & Explainer",
        "sample": "用科技改变生活，让每一个创作者都能轻松制作出高质量的视频内容。"
    },

    # --- Turkish (Türkçe) [Master Studio HD] ---
    {
        "id": "tr-TR-AhmetNeural",
        "name": "Ahmet (Studio)",
        "gender": "Male",
        "language_id": "tr",
        "flag": "🇹🇷",
        "accent": "Turkish (Istanbul)",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Historical Documentary / Drama",
        "sample": "Tarihin derinliklerinde gizlenen medeniyetler, günümüze ilham vermeye devam ediyor."
    },
    {
        "id": "tr-TR-EmelNeural",
        "name": "Emel (Studio)",
        "gender": "Female",
        "language_id": "tr",
        "flag": "🇹🇷",
        "accent": "Turkish (Istanbul)",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Expressive Story / Commercial",
        "sample": "Yeni bir güne başlarken, hayallerinize giden yolda emin adımlarla ilerleyin."
    },

    # --- German (Deutsch) [Master Studio HD] ---
    {
        "id": "de-DE-KillianNeural",
        "name": "Killian (Studio)",
        "gender": "Male",
        "language_id": "de",
        "flag": "🇩🇪",
        "accent": "Standard German",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Crisp Documentary / Tech",
        "sample": "Die fortschreitende Digitalisierung eröffnet neue Horizonte für kreative Köpfe weltweit."
    },
    {
        "id": "de-DE-KatjaNeural",
        "name": "Katja (Studio)",
        "gender": "Female",
        "language_id": "de",
        "flag": "🇩🇪",
        "accent": "Standard German",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Warm Audiobooks / Narration",
        "sample": "In der Ruhe liegt die Kraft, um große Herausforderungen mit Gelassenheit zu meistern."
    },

    # --- French (Français) [Kokoro + Master HD] ---
    {
        "id": "ff_siwis",
        "name": "Siwis (Studio)",
        "gender": "Female",
        "language_id": "fr",
        "flag": "🇫🇷",
        "accent": "French (Paris)",
        "engine": "kokoro",
        "engine_badge": "Kokoro-82M 24kHz",
        "category": "Articulate / Literature",
        "sample": "Le secret du bonheur réside dans la capacité à apprécier chaque instant précieux."
    },
    {
        "id": "fr-FR-HenriNeural",
        "name": "Henri (Studio)",
        "gender": "Male",
        "language_id": "fr",
        "flag": "🇫🇷",
        "accent": "French (Paris)",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Cinematic Story / Documentary",
        "sample": "À travers les siècles, la quête de la connaissance a toujours éclairé la voie de l'humanité."
    },

    # --- Russian (Русский) [Master Studio HD] ---
    {
        "id": "ru-RU-DmitryNeural",
        "name": "Dmitry (Дмитрий)",
        "gender": "Male",
        "language_id": "ru",
        "flag": "🇷🇺",
        "accent": "Standard Russian",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Deep Baritone / Epic Narration",
        "sample": "Великие открытия начинаются с простого желания заглянуть за горизонт неизведанного."
    },
    {
        "id": "ru-RU-SvetlanaNeural",
        "name": "Svetlana (Светлана)",
        "gender": "Female",
        "language_id": "ru",
        "flag": "🇷🇺",
        "accent": "Standard Russian",
        "engine": "master_neural",
        "engine_badge": "Master Studio HD",
        "category": "Expressive Drama / Poetry",
        "sample": "Каждый рассвет приносит с собой возможность начать всё сначала и создать нечто прекрасное."
    }
]


def get_all_languages():
    """Returns all 12 language category boxes."""
    # Recalculate voice counts dynamically
    counts = {}
    for v in PREMIUM_VOICES:
        lid = v["language_id"]
        counts[lid] = counts.get(lid, 0) + 1
    
    result = []
    for lang in PREMIUM_LANGUAGES:
        c = lang.copy()
        c["count"] = counts.get(lang["id"], c.get("count", 0))
        result.append(c)
    return result


def get_voices_for_language(lang_id: str):
    """Returns all curated voices for a specific language ID."""
    return [v for v in PREMIUM_VOICES if v["language_id"] == lang_id]


def find_premium_voice(voice_id: str):
    """Finds voice metadata by ID."""
    for v in PREMIUM_VOICES:
        if v["id"] == voice_id:
            return v
    return None
