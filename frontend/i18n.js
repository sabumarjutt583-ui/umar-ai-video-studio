/* ===========================================================
   i18n — 12 languages, compact table form.
   Each key maps to an array positioned like LANGS below,
   so adding a language = adding one value per row.
   Missing / empty values fall back to English automatically.
   =========================================================== */

const LANGS = ["en", "ur", "hi", "ar", "es", "fr", "pt", "id", "zh", "ru", "tr", "bn"];

const LANG_META = {
  en: { name: "English",    dir: "ltr" },
  ur: { name: "اردو",        dir: "rtl" },
  hi: { name: "हिन्दी",       dir: "ltr" },
  ar: { name: "العربية",     dir: "rtl" },
  es: { name: "Español",    dir: "ltr" },
  fr: { name: "Français",   dir: "ltr" },
  pt: { name: "Português",  dir: "ltr" },
  id: { name: "Indonesia",  dir: "ltr" },
  zh: { name: "中文",        dir: "ltr" },
  ru: { name: "Русский",    dir: "ltr" },
  tr: { name: "Türkçe",     dir: "ltr" },
  bn: { name: "বাংলা",       dir: "ltr" },
};

/* eslint-disable max-len */
const T = {
// ---------------------------------------------------------------- shell
app_title:      ["Video Editing Bot","ویڈیو ایڈیٹنگ بوٹ","वीडियो एडिटिंग बॉट","بوت تحرير الفيديو","Bot de edición de vídeo","Bot de montage vidéo","Bot de edição de vídeo","Bot Edit Video","视频剪辑机器人","Видеомонтажный бот","Video Kurgu Botu","ভিডিও এডিটিং বট"],
app_tagline:    ["Voice + timing + your media → finished video","آواز + ٹائمنگ + آپ کی میڈیا → مکمل ویڈیو","आवाज़ + टाइमिंग + आपकी मीडिया → तैयार वीडियो","الصوت + التوقيت + وسائطك → فيديو جاهز","Voz + tiempos + tus medios → vídeo final","Voix + minutage + vos médias → vidéo finale","Voz + tempos + suas mídias → vídeo final","Suara + waktu + media Anda → video jadi","语音 + 时间轴 + 素材 → 成品视频","Голос + тайминг + медиа → готовое видео","Ses + zamanlama + medyanız → hazır video","ভয়েস + টাইমিং + আপনার মিডিয়া → সম্পূর্ণ ভিডিও"],
projects:       ["Projects","پروجیکٹس","प्रोजेक्ट","المشاريع","Proyectos","Projets","Projetos","Proyek","项目","Проекты","Projeler","প্রজেক্ট"],
project_name:   ["Project name","پروجیکٹ کا نام","प्रोजेक्ट नाम","اسم المشروع","Nombre del proyecto","Nom du projet","Nome do projeto","Nama proyek","项目名称","Название проекта","Proje adı","প্রজেক্টের নাম"],
save:           ["Save","محفوظ کریں","सेव","حفظ","Guardar","Enregistrer","Salvar","Simpan","保存","Сохранить","Kaydet","সেভ"],
load:           ["Load","لوڈ","लोड","تحميل","Cargar","Charger","Carregar","Muat","加载","Загрузить","Yükle","লোড"],
del:            ["Delete","ڈیلیٹ","हटाएँ","حذف","Eliminar","Supprimer","Excluir","Hapus","删除","Удалить","Sil","মুছুন"],
apply:          ["Apply","لاگو کریں","लागू करें","تطبيق","Aplicar","Appliquer","Aplicar","Terapkan","应用","Применить","Uygula","প্রয়োগ"],
add:            ["Add","شامل کریں","जोड़ें","إضافة","Añadir","Ajouter","Adicionar","Tambah","添加","Добавить","Ekle","যোগ"],
remove:         ["Remove","ہٹا دیں","हटाएँ","إزالة","Quitar","Retirer","Remover","Hapus","移除","Убрать","Kaldır","সরান"],
not_set:        ["not set","سیٹ نہیں","सेट नहीं","غير محدد","sin definir","non défini","não definido","belum diatur","未设置","не задано","ayarlanmadı","সেট নেই"],
enabled:        ["Enabled","آن","चालू","مُمكَّن","Activado","Activé","Ativado","Aktif","启用","Включено","Açık","চালু"],

// ---------------------------------------------------------------- step 1: voice
step_voice:     ["Voice / Narration","آواز / نریشن","आवाज़ / नैरेशन","الصوت / التعليق","Voz / narración","Voix / narration","Voz / narração","Suara / narasi","配音 / 旁白","Голос / озвучка","Ses / anlatım","ভয়েস / ন্যারেশন"],
voice_single:   ["Single file","ایک فائل","एक फ़ाइल","ملف واحد","Un archivo","Fichier unique","Arquivo único","Satu file","单个文件","Один файл","Tek dosya","একটি ফাইল"],
voice_multi:    ["Multi-part","کئی حصے","कई भाग","عدة أجزاء","Varias partes","Plusieurs parties","Várias partes","Beberapa bagian","多段文件","Несколько частей","Çok parçalı","একাধিক অংশ"],
drop_voice:     ["Drop your voice file here or click to choose","آواز کی فائل یہاں ڈالیں یا کلک کریں","आवाज़ फ़ाइल यहाँ डालें या क्लिक करें","أفلت ملف الصوت هنا أو انقر للاختيار","Suelta tu archivo de voz o haz clic","Déposez votre fichier voix ou cliquez","Solte seu arquivo de voz ou clique","Letakkan file suara di sini atau klik","将配音文件拖到此处或点击选择","Перетащите файл голоса или нажмите","Ses dosyanızı bırakın veya seçin","ভয়েস ফাইল এখানে দিন বা ক্লিক করুন"],
hint_voice:     ["mp3, wav, m4a, aac — video files also work","mp3, wav, m4a, aac — ویڈیو فائل بھی چلے گی","mp3, wav, m4a, aac — वीडियो भी चलेगा","mp3, wav, m4a, aac — الفيديو مقبول أيضاً","mp3, wav, m4a, aac — también vídeo","mp3, wav, m4a, aac — vidéo acceptée","mp3, wav, m4a, aac — vídeo também","mp3, wav, m4a, aac — video juga bisa","mp3、wav、m4a、aac — 视频文件亦可","mp3, wav, m4a, aac — видео тоже","mp3, wav, m4a, aac — video de olur","mp3, wav, m4a, aac — ভিডিও ফাইলও চলবে"],
drop_voice_parts:["Choose all parts together (part1, part2, …)","تمام حصے ایک ساتھ منتخب کریں (part1, part2, …)","सभी भाग एक साथ चुनें (part1, part2, …)","اختر كل الأجزاء معاً (part1, part2, …)","Elige todas las partes juntas","Choisissez toutes les parties","Escolha todas as partes juntas","Pilih semua bagian sekaligus","一次选择所有分段（part1、part2…）","Выберите все части сразу","Tüm parçaları birlikte seçin","সব অংশ একসাথে বাছুন"],
hint_voice_parts:["They are joined in natural order automatically","یہ خود بخود صحیح ترتیب میں جُڑ جائیں گے","ये स्वयं सही क्रम में जुड़ जाएँगे","سيتم دمجها تلقائياً بالترتيب الصحيح","Se unen en orden natural","Assemblées dans l'ordre naturel","Unidas na ordem natural","Digabung otomatis sesuai urutan","将按自然顺序自动拼接","Склеиваются в естественном порядке","Doğal sırayla birleştirilir","স্বয়ংক্রিয়ভাবে সঠিক ক্রমে জোড়া লাগবে"],
gap_seconds:    ["Gap between parts (sec)","حصوں کے درمیان وقفہ (سیکنڈ)","भागों के बीच अंतर (सेकंड)","الفاصل بين الأجزاء (ثانية)","Pausa entre partes (s)","Écart entre parties (s)","Intervalo entre partes (s)","Jeda antar bagian (detik)","分段间隔（秒）","Пауза между частями (с)","Parçalar arası boşluk (sn)","অংশের মাঝে বিরতি (সেকেন্ড)"],
part_order:     ["Order","ترتیب","क्रम","الترتيب","Orden","Ordre","Ordem","Urutan","顺序","Порядок","Sıra","ক্রম"],
order_natural:  ["Natural (part2 before part10)","قدرتی (part2 پہلے، part10 بعد)","स्वाभाविक (part2 पहले)","طبيعي (part2 قبل part10)","Natural (part2 antes de part10)","Naturel (part2 avant part10)","Natural (part2 antes de part10)","Alami (part2 sebelum part10)","自然顺序（part2 在 part10 前）","Естественный (part2 перед part10)","Doğal (part2, part10'dan önce)","স্বাভাবিক (part2 আগে)"],
order_uploaded: ["As uploaded","جیسے اپلوڈ کیا","जैसे अपलोड किया","كما تم الرفع","Como se subió","Ordre d'envoi","Como enviado","Sesuai unggahan","按上传顺序","Как загружено","Yüklendiği gibi","যেমন আপলোড হয়েছে"],
voice_ready:    ["voice ready","آواز تیار","आवाज़ तैयार","الصوت جاهز","voz lista","voix prête","voz pronta","suara siap","配音就绪","голос готов","ses hazır","ভয়েস প্রস্তুত"],

// ---------------------------------------------------------------- step 2: timing
step_timing:    ["Timing / Segments","ٹائمنگ / سیگمنٹس","टाइमिंग / सेगमेंट","التوقيت / المقاطع","Tiempos / segmentos","Minutage / segments","Tempos / segmentos","Waktu / segmen","时间轴 / 片段","Тайминг / сегменты","Zamanlama / bölümler","টাইমিং / সেগমেন্ট"],
timing_file:    ["Upload file","فائل اپلوڈ","फ़ाइल अपलोड","رفع ملف","Subir archivo","Envoyer un fichier","Enviar arquivo","Unggah file","上传文件","Загрузить файл","Dosya yükle","ফাইল আপলোড"],
timing_paste:   ["Paste box","پیسٹ باکس","पेस्ट बॉक्स","لصق النص","Pegar texto","Coller","Colar","Tempel","粘贴文本","Вставить текст","Yapıştır","পেস্ট বক্স"],
timing_manual:  ["Manual table","دستی ٹیبل","मैनुअल टेबल","جدول يدوي","Tabla manual","Tableau manuel","Tabela manual","Tabel manual","手动表格","Ручная таблица","Elle tablo","ম্যানুয়াল টেবিল"],
timing_group:   ["Sentence grouping","جملوں کی گروپنگ","वाक्य समूहन","تجميع الجُمل","Agrupar frases","Groupement de phrases","Agrupar frases","Kelompok kalimat","按句分组","Группировка фраз","Cümle gruplama","বাক্য গ্রুপিং"],
timing_scene:   ["Scene map","سین میپ","सीन मैप","خريطة المشاهد","Mapa de escenas","Plan de scènes","Mapa de cenas","Peta scene","场景映射","Карта сцен","Sahne haritası","সিন ম্যাপ"],
timing_table:   ["Scene time table","سین ٹائم ٹیبل","सीन टाइम टेबल","جدول أوقات المشاهد","Tabla de tiempos","Table des temps","Tabela de tempos","Tabel waktu scene","场景时间表","Таблица времени сцен","Sahne zaman tablosu","সিন টাইম টেবিল"],
scene_table_paste:["Paste scene table (scene, start, end)","سین ٹیبل پیسٹ کریں (سین، شروع، اختتام)","सीन टेबल पेस्ट करें (सीन, स्टार्ट, एंड)","الصق جدول المشاهد (مشهد، بداية، نهاية)","Pega la tabla (escena, inicio, fin)","Collez la table (scène, début, fin)","Cole a tabela (cena, início, fim)","Tempel tabel (scene, mulai, akhir)","粘贴场景表（场景、开始、结束）","Вставьте таблицу (сцена, начало, конец)","Tabloyu yapıştır (sahne, başlangıç, bitiş)","সিন টেবিল পেস্ট করুন (সিন, শুরু, শেষ)"],
upload_scene_table:["Upload .csv / .tsv / .txt","‏.csv / .tsv / .txt اپلوڈ کریں","‎.csv / .tsv / .txt अपलोड करें","تحميل .csv / .tsv / .txt","Subir .csv / .tsv / .txt","Importer .csv / .tsv / .txt","Enviar .csv / .tsv / .txt","Unggah .csv / .tsv / .txt","上传 .csv / .tsv / .txt","Загрузить .csv / .tsv / .txt",".csv / .tsv / .txt yükle",".csv / .tsv / .txt আপলোড করুন"],
hint_scene_table:["Fastest for 200–300 scenes: copy scene number, start and end straight from Excel/Sheets. Tab, comma, semicolon or pipe all work; time can be 12.5 or 00:04.5 or 00:01:20.5. Word-level JSON is NOT needed here.","200–300 سین کے لیے سب سے تیز: ایکسل/شیٹس سے سین نمبر، اسٹارٹ اور اینڈ سیدھا کاپی کر کے پیسٹ کریں۔ ٹیب، کوما، سیمی کولن یا پائپ — سب چلیں گے؛ وقت 12.5 یا 00:04.5 یا 00:01:20.5 ہو سکتا ہے۔ یہاں word-level JSON کی ضرورت نہیں۔","200–300 सीन के लिए सबसे तेज़: Excel/Sheets से सीन नंबर, स्टार्ट, एंड सीधा पेस्ट करें। टैब, कॉमा, सेमीकोलन या पाइप — सब चलेंगे; समय 12.5 या 00:04.5 या 00:01:20.5। यहाँ word-level JSON ज़रूरी नहीं।","الأسرع لـ 200–300 مشهد: انسخ رقم المشهد والبداية والنهاية من Excel/Sheets. الفاصل: تاب أو فاصلة أو فاصلة منقوطة أو |؛ الوقت 12.5 أو 00:04.5 أو 00:01:20.5. لا حاجة إلى JSON على مستوى الكلمة.","Lo más rápido para 200–300 escenas: copia escena, inicio y fin desde Excel/Sheets. Tab, coma, punto y coma o barra; tiempo 12.5 o 00:04.5 o 00:01:20.5. No necesita JSON por palabra.","Le plus rapide pour 200–300 scènes : copiez scène, début et fin depuis Excel/Sheets. Tab, virgule, point-virgule ou barre ; temps 12.5 ou 00:04.5 ou 00:01:20.5. Pas besoin de JSON mot à mot.","O mais rápido para 200–300 cenas: copie cena, início e fim do Excel/Sheets. Tab, vírgula, ponto e vírgula ou barra; tempo 12.5 ou 00:04.5 ou 00:01:20.5. Não precisa de JSON por palavra.","Tercepat untuk 200–300 scene: salin nomor scene, mulai, akhir dari Excel/Sheets. Tab, koma, titik koma, atau pipa; waktu 12.5 atau 00:04.5 atau 00:01:20.5. Tidak perlu JSON per kata.","200–300 个场景最快的方式：从 Excel/Sheets 直接复制场景号、开始、结束。制表符、逗号、分号或竖线均可；时间可写 12.5、00:04.5 或 00:01:20.5。此处不需要逐词 JSON。","Самый быстрый путь для 200–300 сцен: скопируйте номер сцены, начало и конец из Excel/Sheets. Таб, запятая, точка с запятой или |; время 12.5, 00:04.5 или 00:01:20.5. JSON по словам не нужен.","200–300 sahne için en hızlısı: Excel/Sheets'ten sahne no, başlangıç ve bitişi kopyalayın. Tab, virgül, noktalı virgül veya | çalışır; süre 12.5, 00:04.5 ya da 00:01:20.5. Kelime düzeyinde JSON gerekmez.","২০০–৩০০ সিনের জন্য দ্রুততম: Excel/Sheets থেকে সিন নম্বর, শুরু ও শেষ সরাসরি পেস্ট করুন। ট্যাব, কমা, সেমিকোলন বা পাইপ — সব চলবে; সময় 12.5 বা 00:04.5 বা 00:01:20.5। এখানে word-level JSON লাগবে না।"],
hint_scene_any_lang:["Works in any language. The header can be “Scene 1”, “シーン1”, “Сцена 1”, “سین 1” or just “1”.","ہر زبان میں چلتا ہے۔ ہیڈر “Scene 1”، “シーン1”، “Сцена 1”، “سین 1” یا صرف “1” ہو سکتا ہے۔","हर भाषा में चलता है। हेडर “Scene 1”, “シーン1”, “Сцена 1”, “सीन 1” या सिर्फ़ “1”।","يعمل بأي لغة. يمكن أن يكون العنوان “Scene 1” أو “シーン1” أو “Сцена 1” أو “منظر 1” أو “1”.","Funciona en cualquier idioma. El encabezado puede ser “Scene 1”, “シーン1”, “Сцена 1” o solo “1”.","Fonctionne dans toutes les langues. L'en-tête peut être « Scene 1 », « シーン1 », « Сцена 1 » ou juste « 1 ».","Funciona em qualquer idioma. O cabeçalho pode ser “Scene 1”, “シーン1”, “Сцена 1” ou só “1”.","Bekerja di semua bahasa. Header bisa “Scene 1”, “シーン1”, “Сцена 1”, atau hanya “1”.","支持任何语言。标题可以是 “Scene 1”、“シーン1”、“场景1” 或只写 “1”。","Работает на любом языке. Заголовок может быть «Scene 1», «シーン1», «Сцена 1» или просто «1».","Her dilde çalışır. Başlık “Scene 1”, “シーン1”, “Сцена 1” veya sadece “1” olabilir.","যেকোনো ভাষায় কাজ করে। হেডার “Scene 1”, “シーン1”, “Сцена 1” বা শুধু “1” হতে পারে।"],
sentences_found:["sentences","جملے","वाक्य","جمل","frases","phrases","frases","kalimat","句","предложений","cümle","বাক্য"],
scenes_word:    ["scenes","سین","सीन","مشاهد","escenas","scènes","cenas","scene","场景","сцен","sahne","সিন"],
rows_skipped:   ["rows skipped","قطاریں چھوڑ دی گئیں","पंक्तियाँ छोड़ी गईं","صفوف تم تخطيها","filas omitidas","lignes ignorées","linhas ignoradas","baris dilewati","已跳过行","строк пропущено","satır atlandı","সারি বাদ পড়েছে"],
paste_empty:    ["Paste box is empty.","پیسٹ باکس خالی ہے۔","पेस्ट बॉक्स खाली है।","صندوق اللصق فارغ.","La caja está vacía.","La zone est vide.","A caixa está vazia.","Kotak tempel kosong.","粘贴框为空。","Поле вставки пусто.","Yapıştırma alanı boş.","পেস্ট বক্স খালি।"],
voice:          ["voice","آواز","आवाज़","الصوت","voz","voix","voz","suara","配音","голос","ses","ভয়েস"],
drop_ts:        ["Drop SRT or word-level JSON","SRT یا word-level JSON ڈالیں","SRT या word-level JSON डालें","أفلت ملف SRT أو JSON","Suelta SRT o JSON","Déposez SRT ou JSON","Solte SRT ou JSON","Letakkan SRT atau JSON","拖入 SRT 或逐词 JSON","Перетащите SRT или JSON","SRT veya JSON bırakın","SRT বা word-level JSON দিন"],
hint_ts:        ["JSON gives word-by-word captions + sentence grouping","JSON سے لفظ بہ لفظ کیپشن اور گروپنگ ملتی ہے","JSON से शब्द-दर-शब्द कैप्शन मिलते हैं","JSON يمنح ترجمة كلمة بكلمة","JSON permite subtítulos palabra por palabra","JSON permet des sous-titres mot à mot","JSON permite legendas palavra por palavra","JSON memberi teks per kata","JSON 支持逐词字幕与分句","JSON даёт субтитры по словам","JSON kelime kelime altyazı verir","JSON দিলে শব্দে-শব্দে ক্যাপশন হয়"],
paste_label:    ["Paste SRT or JSON here","SRT یا JSON یہاں پیسٹ کریں","SRT या JSON यहाँ पेस्ट करें","الصق SRT أو JSON هنا","Pega SRT o JSON aquí","Collez SRT ou JSON ici","Cole SRT ou JSON aqui","Tempel SRT atau JSON di sini","在此粘贴 SRT 或 JSON","Вставьте SRT или JSON","SRT veya JSON'u yapıştırın","SRT বা JSON এখানে পেস্ট করুন"],
format:         ["Format","فارمیٹ","फ़ॉर्मेट","الصيغة","Formato","Format","Formato","Format","格式","Формат","Biçim","ফরম্যাট"],
fmt_auto:       ["Auto-detect","خود پہچانو","स्वतः पहचान","كشف تلقائي","Detección automática","Détection auto","Detecção automática","Deteksi otomatis","自动识别","Автоопределение","Otomatik algıla","স্বয়ংক্রিয় শনাক্ত"],
manual_mode:    ["Mode","موڈ","मोड","الوضع","Modo","Mode","Modo","Mode","模式","Режим","Mod","মোড"],
mode_duration:  ["Duration only (easiest)","صرف دورانیہ (سب سے آسان)","केवल अवधि (सबसे आसान)","المدة فقط (الأسهل)","Solo duración (más fácil)","Durée seule (le plus simple)","Só duração (mais fácil)","Hanya durasi (termudah)","仅时长（最简单）","Только длительность (проще)","Sadece süre (en kolay)","শুধু সময়কাল (সবচেয়ে সহজ)"],
mode_startend:  ["Start + End","شروع + اختتام","आरंभ + अंत","البداية + النهاية","Inicio + fin","Début + fin","Início + fim","Mulai + selesai","开始 + 结束","Начало + конец","Başlangıç + bitiş","শুরু + শেষ"],
add_row:        ["+ Add row","+ نئی رو","+ नई पंक्ति","+ صف جديد","+ Añadir fila","+ Ajouter une ligne","+ Adicionar linha","+ Tambah baris","+ 添加行","+ Добавить строку","+ Satır ekle","+ নতুন সারি"],
load_current:   ["Load current segments","موجودہ سیگمنٹس لوڈ کریں","वर्तमान सेगमेंट लोड करें","تحميل المقاطع الحالية","Cargar segmentos actuales","Charger les segments actuels","Carregar segmentos atuais","Muat segmen saat ini","载入现有片段","Загрузить текущие сегменты","Mevcut bölümleri yükle","বর্তমান সেগমেন্ট লোড করুন"],
apply_table:    ["Apply table","ٹیبل لاگو کریں","टेबल लागू करें","تطبيق الجدول","Aplicar tabla","Appliquer le tableau","Aplicar tabela","Terapkan tabel","应用表格","Применить таблицу","Tabloyu uygula","টেবিল প্রয়োগ"],
start:          ["Start","شروع","आरंभ","البداية","Inicio","Début","Início","Mulai","开始","Начало","Başlangıç","শুরু"],
end:            ["End","اختتام","अंत","النهاية","Fin","Fin","Fim","Selesai","结束","Конец","Bitiş","শেষ"],
duration:       ["Duration","دورانیہ","अवधि","المدة","Duración","Durée","Duração","Durasi","时长","Длительность","Süre","সময়কাল"],
text:           ["Text","متن","टेक्स्ट","النص","Texto","Texte","Texto","Teks","文字","Текст","Metin","টেক্সট"],
sentences_per_clip:["Sentences per clip","فی کلپ جملے","प्रति क्लिप वाक्य","جُمل لكل مقطع","Frases por clip","Phrases par clip","Frases por clipe","Kalimat per klip","每段句数","Фраз на клип","Klip başına cümle","প্রতি ক্লিপে বাক্য"],
regroup:        ["Regroup","دوبارہ گروپ","फिर समूह","إعادة التجميع","Reagrupar","Regrouper","Reagrupar","Kelompokkan ulang","重新分组","Перегруппировать","Yeniden grupla","পুনরায় গ্রুপ"],
hint_group:     ["Needs word-level JSON timestamps.","اس کے لیے word-level JSON ضروری ہے۔","इसके लिए word-level JSON ज़रूरी है।","يتطلب JSON على مستوى الكلمة.","Requiere JSON por palabra.","Nécessite un JSON mot à mot.","Requer JSON por palavra.","Perlu JSON per kata.","需要逐词 JSON 时间轴。","Нужен JSON по словам.","Kelime düzeyinde JSON gerekir.","word-level JSON প্রয়োজন।"],
drop_scene:     ["Drop your scene-map / script file","سین میپ / اسکرپٹ فائل ڈالیں","सीन-मैप / स्क्रिप्ट फ़ाइल डालें","أفلت ملف المشاهد / النص","Suelta el guion o mapa de escenas","Déposez le script / plan de scènes","Solte o roteiro / mapa de cenas","Letakkan file scene / skrip","拖入场景映射 / 脚本文件","Перетащите сценарий / карту сцен","Sahne haritası / senaryo bırakın","সিন-ম্যাপ / স্ক্রিপ্ট ফাইল দিন"],
scene_paste:    ["…or paste it","…یا پیسٹ کر دیں","…या पेस्ट करें","…أو الصقه","…o pégalo","…ou collez-le","…ou cole aqui","…atau tempel","…或直接粘贴","…или вставьте","…ya da yapıştırın","…অথবা পেস্ট করুন"],

// ---------------------------------------------------------------- step 3: media
step_media:     ["Your media","آپ کی میڈیا","आपकी मीडिया","وسائطك","Tus medios","Vos médias","Suas mídias","Media Anda","你的素材","Ваши медиа","Medyanız","আপনার মিডিয়া"],
upload_media:   ["＋ Upload images / videos","＋ تصاویر / ویڈیوز اپلوڈ کریں","＋ इमेज / वीडियो अपलोड","＋ ارفع صوراً / فيديوهات","＋ Subir imágenes / vídeos","＋ Envoyer images / vidéos","＋ Enviar imagens / vídeos","＋ Unggah gambar / video","＋ 上传图片 / 视频","＋ Загрузить фото / видео","＋ Resim / video yükle","＋ ছবি / ভিডিও আপলোড"],
import_zip:    ["🗜 Import ZIP","🗜 ZIP امپورٹ","🗜 ZIP इम्पोर्ट","🗜 استيراد ZIP","🗜 Importar ZIP","🗜 Importer ZIP","🗜 Importar ZIP","🗜 Impor ZIP","🗜 导入 ZIP","🗜 Импорт ZIP","🗜 ZIP içe aktar","🗜 ZIP ইমপোর্ট"],
hint_media:     ["Filenames with numbers (1_beach.jpg, scene3.mp4) auto-assign.","نام میں نمبر ہو (1_beach.jpg, scene3.mp4) تو خود اسائن ہو جاتی ہے۔","नाम में नंबर हो तो स्वतः असाइन हो जाती है।","الأسماء التي تحتوي أرقاماً تُعيَّن تلقائياً.","Los nombres con números se asignan solos.","Les noms numérotés sont assignés seuls.","Nomes com números são atribuídos sozinhos.","Nama berangka otomatis ditetapkan.","文件名带数字会自动分配到片段。","Имена с числами назначаются автоматически.","Numaralı adlar otomatik atanır.","নামে নম্বর থাকলে স্বয়ংক্রিয় অ্যাসাইন হয়।"],
assign:         ["Assign","اسائن","असाइन","تعيين","Asignar","Assigner","Atribuir","Tetapkan","分配","Назначить","Ata","অ্যাসাইন"],
unassigned:     ["— none —","— کوئی نہیں —","— कोई नहीं —","— لا شيء —","— ninguno —","— aucun —","— nenhum —","— tidak ada —","— 无 —","— нет —","— yok —","— কিছু নেই —"],
segments_count: ["segments","سیگمنٹس","सेगमेंट","مقاطع","segmentos","segments","segmentos","segmen","片段","сегментов","bölüm","সেগমেন্ট"],
with_media:     ["with media","میڈیا کے ساتھ","मीडिया सहित","بوسائط","con medios","avec médias","com mídia","dengan media","已配素材","с медиа","medyalı","মিডিয়াসহ"],
timeline:       ["timeline","ٹائم لائن","टाइमलाइन","الخط الزمني","línea de tiempo","chronologie","linha do tempo","garis waktu","时间轴","таймлайн","zaman çizelgesi","টাইমলাইন"],

// ---------------------------------------------------------------- step 4: look
step_look:      ["Look & motion","لُک اور موشن","लुक और मोशन","المظهر والحركة","Aspecto y movimiento","Style & mouvement","Aparência e movimento","Tampilan & gerak","画面与运动","Вид и движение","Görünüm ve hareket","লুক ও মোশন"],
effect:         ["Motion effect","موشن ایفیکٹ","मोशन इफ़ेक्ट","تأثير الحركة","Efecto de movimiento","Effet de mouvement","Efeito de movimento","Efek gerak","运动效果","Эффект движения","Hareket efekti","মোশন ইফেক্ট"],
transition:     ["Transition","ٹرانزیشن","ट्रांज़िशन","الانتقال","Transición","Transition","Transição","Transisi","转场","Переход","Geçiş","ট্রানজিশন"],
trans_speed:    ["Transition speed","ٹرانزیشن اسپیڈ","ट्रांज़िशन गति","سرعة الانتقال","Velocidad de transición","Vitesse de transition","Velocidade da transição","Kecepatan transisi","转场速度","Скорость перехода","Geçiş hızı","ট্রানজিশন গতি"],
color_filter:   ["Color filter","کلر فلٹر","कलर फ़िल्टर","مرشّح اللون","Filtro de color","Filtre couleur","Filtro de cor","Filter warna","色彩滤镜","Цветовой фильтр","Renk filtresi","কালার ফিল্টার"],
aspect:         ["Aspect ratio","ایسپیکٹ ریشو","आस्पेक्ट रेशियो","نسبة العرض","Relación de aspecto","Format d'image","Proporção","Rasio aspek","画面比例","Соотношение сторон","En-boy oranı","অ্যাসপেক্ট রেশিও"],
resolution:     ["Resolution","ریزولوشن","रेज़ोल्यूशन","الدقة","Resolución","Résolution","Resolução","Resolusi","分辨率","Разрешение","Çözünürlük","রেজোলিউশন"],

// ---------------------------------------------------------------- step 5: captions
step_captions:  ["Captions","کیپشنز","कैप्शन","الترجمة","Subtítulos","Sous-titres","Legendas","Teks","字幕","Субтитры","Altyazı","ক্যাপশন"],
preset:         ["Preset","پریسیٹ","प्रीसेट","نمط جاهز","Preajuste","Préréglage","Predefinição","Preset","预设","Пресет","Hazır ayar","প্রিসেট"],
cap_mode:       ["Mode","موڈ","मोड","الوضع","Modo","Mode","Modo","Mode","模式","Режим","Mod","মোড"],
cap_script:     ["Script / language","رسم الخط / زبان","स्क्रिप्ट / भाषा","النص / اللغة","Escritura / idioma","Écriture / langue","Escrita / idioma","Aksara / bahasa","文字 / 语言","Письмо / язык","Yazı / dil","লিপি / ভাষা"],
font:           ["Font","فونٹ","फ़ॉन्ट","الخط","Fuente","Police","Fonte","Font","字体","Шрифт","Yazı tipi","ফন্ট"],
font_size:      ["Font size","فونٹ سائز","फ़ॉन्ट आकार","حجم الخط","Tamaño de fuente","Taille de police","Tamanho da fonte","Ukuran font","字号","Размер шрифта","Yazı boyutu","ফন্ট সাইজ"],
color:          ["Text color","متن کا رنگ","टेक्स्ट रंग","لون النص","Color del texto","Couleur du texte","Cor do texto","Warna teks","文字颜色","Цвет текста","Metin rengi","টেক্সট রং"],
highlight:      ["Karaoke highlight","کراوکی ہائی لائٹ","कराओके हाइलाइट","تمييز الكاريوكي","Resalte karaoke","Surbrillance karaoké","Destaque karaokê","Sorotan karaoke","卡拉OK高亮","Подсветка караоке","Karaoke vurgusu","কারাওকে হাইলাইট"],
position:       ["Position","پوزیشن","स्थिति","الموضع","Posición","Position","Posição","Posisi","位置","Позиция","Konum","পজিশন"],
pos_bottom:     ["Bottom","نیچے","नीचे","أسفل","Abajo","Bas","Inferior","Bawah","底部","Снизу","Alt","নিচে"],
pos_middle:     ["Middle","درمیان","मध्य","الوسط","Centro","Milieu","Meio","Tengah","中间","По центру","Orta","মাঝে"],
pos_top:        ["Top","اوپر","ऊपर","أعلى","Arriba","Haut","Superior","Atas","顶部","Сверху","Üst","উপরে"],
animation:      ["Animation","اینیمیشن","एनिमेशन","الحركة","Animación","Animation","Animação","Animasi","动画","Анимация","Animasyon","অ্যানিমেশন"],
margin_v:       ["Vertical margin","عمودی مارجن","वर्टिकल मार्जिन","الهامش الرأسي","Margen vertical","Marge verticale","Margem vertical","Margin vertikal","垂直边距","Верт. отступ","Dikey kenar","ভার্টিক্যাল মার্জিন"],
max_chars:      ["Max chars per line","فی لائن زیادہ سے زیادہ حروف","प्रति पंक्ति अधिकतम अक्षर","أقصى حروف بالسطر","Máx. caracteres por línea","Caractères max/ligne","Máx. caracteres por linha","Maks karakter per baris","每行最多字符","Макс. символов в строке","Satır başına maks karakter","প্রতি লাইনে সর্বোচ্চ অক্ষর"],
outline:        ["Outline","آؤٹ لائن","आउटलाइन","حدود","Contorno","Contour","Contorno","Garis luar","描边","Обводка","Kenarlık","আউটলাইন"],
box:            ["Background box","بیک گراؤنڈ باکس","बैकग्राउंड बॉक्स","خلفية ملونة","Caja de fondo","Fond coloré","Caixa de fundo","Kotak latar","背景框","Фон-плашка","Arka plan kutusu","ব্যাকগ্রাউন্ড বক্স"],
bold:           ["Bold","بولڈ","बोल्ड","عريض","Negrita","Gras","Negrito","Tebal","加粗","Жирный","Kalın","বোল্ড"],
all_caps:       ["ALL CAPS","بڑے حروف","बड़े अक्षर","أحرف كبيرة","MAYÚSCULAS","MAJUSCULES","MAIÚSCULAS","HURUF BESAR","全部大写","ЗАГЛАВНЫЕ","BÜYÜK HARF","বড় হাতের অক্ষর"],
custom_font:    ["Custom font file (optional)","اپنی فونٹ فائل (اختیاری)","कस्टम फ़ॉन्ट फ़ाइल (वैकल्पिक)","ملف خط مخصص (اختياري)","Fuente propia (opcional)","Police personnalisée (option)","Fonte própria (opcional)","File font sendiri (opsional)","自定义字体（可选）","Свой шрифт (необязательно)","Özel yazı tipi (isteğe bağlı)","কাস্টম ফন্ট ফাইল (ঐচ্ছিক)"],

// ---------------------------------------------------------------- step 6: audio
step_audio:     ["Audio","آڈیو","ऑडियो","الصوت","Audio","Audio","Áudio","Audio","音频","Аудио","Ses","অডিও"],
no_music:       ["no music","میوزک نہیں","म्यूज़िक नहीं","لا موسيقى","sin música","pas de musique","sem música","tanpa musik","无音乐","без музыки","müzik yok","মিউজিক নেই"],
upload_music:   ["🎵 Background music","🎵 بیک گراؤنڈ میوزک","🎵 बैकग्राउंड म्यूज़िक","🎵 موسيقى خلفية","🎵 Música de fondo","🎵 Musique de fond","🎵 Música de fundo","🎵 Musik latar","🎵 背景音乐","🎵 Фоновая музыка","🎵 Arka plan müziği","🎵 ব্যাকগ্রাউন্ড মিউজিক"],
music_volume:   ["Music volume","میوزک والیوم","म्यूज़िक वॉल्यूम","مستوى الموسيقى","Volumen de música","Volume musique","Volume da música","Volume musik","音乐音量","Громкость музыки","Müzik sesi","মিউজিক ভলিউম"],
video_audio_mode:["Original video audio","ویڈیو کی اصل آواز","वीडियो की मूल आवाज़","صوت الفيديو الأصلي","Audio original del vídeo","Son original de la vidéo","Áudio original do vídeo","Audio asli video","视频原声","Оригинальный звук видео","Videonun özgün sesi","ভিডিওর মূল অডিও"],
mute:           ["Mute","خاموش","म्यूट","كتم","Silenciar","Muet","Silenciar","Bisukan","静音","Без звука","Sessiz","মিউট"],
mix:            ["Mix with voice","آواز کے ساتھ ملائیں","आवाज़ के साथ मिलाएँ","دمج مع الصوت","Mezclar con la voz","Mixer avec la voix","Misturar com a voz","Campur dengan suara","与配音混合","Смешать с голосом","Sesle karıştır","ভয়েসের সাথে মিশাও"],
video_audio_volume:["Video audio volume","ویڈیو آڈیو والیوم","वीडियो ऑडियो वॉल्यूम","مستوى صوت الفيديو","Volumen del vídeo","Volume vidéo","Volume do vídeo","Volume audio video","视频音量","Громкость видео","Video ses düzeyi","ভিডিও অডিও ভলিউম"],
video_trim_mode:["Long video: which part to cut","لمبی ویڈیو: کہاں سے کاٹیں","लंबा वीडियो: कहाँ से काटें","الفيديو الطويل: أي جزء يُقتطع","Vídeo largo: qué parte cortar","Vidéo longue : quelle partie couper","Vídeo longo: qual parte cortar","Video panjang: bagian mana dipotong","长视频：裁剪哪部分","Длинное видео: что обрезать","Uzun video: neresi kesilsin","লম্বা ভিডিও: কোথা থেকে কাটবে"],
trim_end:       ["Cut the end (keep beginning)","آخر سے کاٹیں (شروع رکھیں)","अंत काटें (शुरुआत रखें)","اقتطاع النهاية (إبقاء البداية)","Cortar el final","Couper la fin","Cortar o fim","Potong akhir","裁掉末尾（保留开头）","Обрезать конец","Sonu kes (başı tut)","শেষ কাটো (শুরু রাখো)"],
trim_start:     ["Cut the beginning (keep end)","شروع سے کاٹیں (آخر رکھیں)","शुरुआत काटें (अंत रखें)","اقتطاع البداية (إبقاء النهاية)","Cortar el inicio","Couper le début","Cortar o início","Potong awal","裁掉开头（保留末尾）","Обрезать начало","Başı kes (sonu tut)","শুরু কাটো (শেষ রাখো)"],
trim_middle:    ["Keep the middle","درمیانی حصہ رکھیں","बीच का हिस्सा रखें","إبقاء الوسط","Conservar el medio","Garder le milieu","Manter o meio","Simpan bagian tengah","保留中间","Оставить середину","Ortayı tut","মাঝের অংশ রাখো"],
fit_hint:       ["Short video: slowed smoothly → repeated up to 2× → and if still short, its last frame becomes a zooming image. The picture never freezes.","چھوٹی ویڈیو: پہلے سلو → پھر 2 بار تک ریپیٹ → پھر بھی کم ہو تو آخری فریم کی زوم ہوتی امیج۔ ویڈیو کہیں نہیں رکتی۔","छोटा वीडियो: पहले स्लो → 2× तक रिपीट → फिर भी कम हो तो आख़िरी फ़्रेम की ज़ूम इमेज। तस्वीर कभी नहीं रुकती।","فيديو قصير: تبطيء → تكرار حتى مرتين → ثم صورة الإطار الأخير مع تكبير. لا تتجمد الصورة أبداً.","Vídeo corto: se ralentiza → se repite hasta 2× → y si falta, el último fotograma se usa como imagen con zoom. Nunca se congela.","Vidéo courte : ralentie → répétée jusqu'à 2× → puis la dernière image avec zoom. L'image ne se fige jamais.","Vídeo curto: desacelerado → repetido até 2× → depois o último frame como imagem com zoom. Nunca congela.","Video pendek: diperlambat → diulang hingga 2× → lalu frame terakhir jadi gambar dengan zoom. Gambar tidak pernah membeku.","短视频：先放慢 → 最多重复 2 次 → 仍不足则用末帧缩放图片补足，画面绝不静止。","Короткое видео: замедление → повтор до 2× → затем последний кадр как картинка с зумом. Картинка не застывает.","Kısa video: yavaşlatılır → en fazla 2× tekrarlanır → yine kısaysa son kare yakınlaşan görsel olur. Görüntü asla donmaz.","ছোট ভিডিও: স্লো → সর্বোচ্চ ২× রিপিট → তারপরও কম হলে শেষ ফ্রেমের জুম ইমেজ। ছবি কখনো থামে না।"],
ducking:        ["Auto-duck music under voice","آواز کے وقت میوزک خود کم ہو","आवाज़ पर म्यूज़िक स्वतः कम","خفض الموسيقى تلقائياً عند الكلام","Bajar música bajo la voz","Baisser la musique sous la voix","Abaixar música sob a voz","Kecilkan musik saat suara","语音时自动压低音乐","Приглушать музыку под голос","Konuşurken müziği kıs","ভয়েসের সময় মিউজিক কমাও"],
music_fade:     ["Music fade in/out","میوزک فیڈ ان/آؤٹ","म्यूज़िक फ़ेड इन/आउट","تلاشي الموسيقى","Fundido de música","Fondu musique","Fade da música","Fade musik","音乐淡入淡出","Плавное появление музыки","Müzik fade in/out","মিউজিক ফেড ইন/আউট"],
sound_effects:  ["Sound effects","ساؤنڈ ایفیکٹس","साउंड इफ़ेक्ट","المؤثرات الصوتية","Efectos de sonido","Effets sonores","Efeitos sonoros","Efek suara","音效","Звуковые эффекты","Ses efektleri","সাউন্ড ইফেক্ট"],
sfx:            ["Effect","ایفیکٹ","इफ़ेक्ट","المؤثر","Efecto","Effet","Efeito","Efek","效果","Эффект","Efekt","ইফেক্ট"],
at_second:      ["At second","کس سیکنڈ پر","किस सेकंड पर","عند الثانية","En el segundo","À la seconde","No segundo","Pada detik","在第几秒","На секунде","Saniyede","কোন সেকেন্ডে"],
volume:         ["Volume","والیوم","वॉल्यूम","المستوى","Volumen","Volume","Volume","Volume","音量","Громкость","Ses","ভলিউম"],

// ---------------------------------------------------------------- step 7: overlays
step_overlays:  ["Stickers & text","اسٹیکرز اور متن","स्टिकर और टेक्स्ट","الملصقات والنص","Pegatinas y texto","Stickers & texte","Adesivos e texto","Stiker & teks","贴纸与文字","Стикеры и текст","Çıkartma ve metin","স্টিকার ও টেক্সট"],
sticker:        ["Sticker","اسٹیکر","स्टिकर","ملصق","Pegatina","Sticker","Adesivo","Stiker","贴纸","Стикер","Çıkartma","স্টিকার"],
scale:          ["Size","سائز","आकार","الحجم","Tamaño","Taille","Tamanho","Ukuran","大小","Размер","Boyut","আকার"],
opacity:        ["Opacity","شفافیت","पारदर्शिता","الشفافية","Opacidad","Opacité","Opacidade","Opasitas","不透明度","Прозрачность","Saydamlık","অপাসিটি"],
whole_video:    ["Whole video (watermark)","پوری ویڈیو (واٹر مارک)","पूरा वीडियो (वॉटरमार्क)","الفيديو كله (علامة مائية)","Todo el vídeo (marca de agua)","Toute la vidéo (filigrane)","Vídeo inteiro (marca d'água)","Seluruh video (watermark)","整段视频（水印）","Всё видео (водяной знак)","Tüm video (filigran)","পুরো ভিডিও (ওয়াটারমার্ক)"],
upload_logo:    ["🖼 Upload own logo / PNG","🖼 اپنا لوگو / PNG اپلوڈ کریں","🖼 अपना लोगो / PNG अपलोड","🖼 ارفع شعارك / PNG","🖼 Subir logo / PNG","🖼 Envoyer logo / PNG","🖼 Enviar logo / PNG","🖼 Unggah logo / PNG","🖼 上传自己的 Logo / PNG","🖼 Загрузить логотип / PNG","🖼 Kendi logonuzu yükleyin","🖼 নিজের লোগো / PNG আপলোড"],
custom_text:    ["Custom text","اپنا متن","कस्टम टेक्स्ट","نص مخصص","Texto propio","Texte personnalisé","Texto próprio","Teks sendiri","自定义文字","Свой текст","Özel metin","কাস্টম টেক্সট"],

// ---------------------------------------------------------------- step 8: render
step_render:    ["Check & render","چیک اور رینڈر","जाँच और रेंडर","التحقق والتصدير","Comprobar y renderizar","Vérifier & rendre","Verificar e renderizar","Periksa & render","检查并渲染","Проверка и рендер","Kontrol ve render","চেক ও রেন্ডার"],
smart_triggers: ["Smart sticker triggers","اسمارٹ اسٹیکر ٹرگرز","स्मार्ट स्टिकर ट्रिगर","مشغلات ملصقات ذكية","Disparadores inteligentes","Déclencheurs intelligents","Disparadores inteligentes","Pemicu stiker pintar","智能贴纸触发","Умные триггеры стикеров","Akıllı çıkartma tetikleri","স্মার্ট স্টিকার ট্রিগার"],
validate:       ["Check media","میڈیا چیک کریں","मीडिया जाँचें","تحقق من الوسائط","Comprobar medios","Vérifier les médias","Verificar mídias","Periksa media","检查素材","Проверить медиа","Medyayı kontrol et","মিডিয়া চেক করুন"],
skip_validation:["Render anyway (skip checks)","پھر بھی رینڈر کریں (چیک چھوڑ دیں)","फिर भी रेंडर करें","تجاهل التحقق وابدأ","Renderizar sin comprobar","Rendre sans vérifier","Renderizar sem verificar","Render tanpa periksa","跳过检查直接渲染","Рендер без проверки","Kontrolsüz render","চেক ছাড়াই রেন্ডার"],
render_dashboard:["Render dashboard","رینڈر ڈیش بورڈ","रेंडर डैशबोर्ड","لوحة التصدير","Panel de render","Tableau de rendu","Painel de render","Dasbor render","渲染面板","Панель рендера","Render panosu","রেন্ডার ড্যাশবোর্ড"],
render_now:     ["Render video","ویڈیو بنائیں","वीडियो बनाएँ","صدّر الفيديو","Renderizar vídeo","Lancer le rendu","Renderizar vídeo","Render video","开始渲染","Создать видео","Videoyu oluştur","ভিডিও রেন্ডার করুন"],
cancel:         ["Cancel","منسوخ","रद्द","إلغاء","Cancelar","Annuler","Cancelar","Batal","取消","Отмена","İptal","বাতিল"],
live_log:       ["Live log","لائیو لاگ","लाइव लॉग","سجل مباشر","Registro en vivo","Journal en direct","Log ao vivo","Log langsung","实时日志","Живой лог","Canlı kayıt","লাইভ লগ"],
idle:           ["idle","فارغ","निष्क्रिय","خامل","inactivo","inactif","inativo","siaga","空闲","ожидание","boşta","নিষ্ক্রিয়"],
not_started:    ["Not started yet.","ابھی شروع نہیں ہوا۔","अभी शुरू नहीं हुआ।","لم يبدأ بعد.","Aún no ha empezado.","Pas encore démarré.","Ainda não começou.","Belum dimulai.","尚未开始。","Ещё не начато.","Henüz başlamadı.","এখনো শুরু হয়নি।"],
result:         ["Result","نتیجہ","परिणाम","النتيجة","Resultado","Résultat","Resultado","Hasil","结果","Результат","Sonuç","ফলাফল"],
download:       ["Download","ڈاؤن لوڈ","डाउनलोड","تنزيل","Descargar","Télécharger","Baixar","Unduh","下载","Скачать","İndir","ডাউনলোড"],
quick_export:   ["Quick re-export","فوری دوبارہ ایکسپورٹ","तेज़ री-एक्सपोर्ट","تصدير سريع","Reexportar rápido","Réexport rapide","Reexportar rápido","Ekspor cepat","快速重新导出","Быстрый реэкспорт","Hızlı yeniden aktar","দ্রুত রি-এক্সপোর্ট"],
fit_mode:       ["Fit","فٹ","फ़िट","الملاءمة","Ajuste","Ajustement","Ajuste","Sesuai","适配","Вписать","Sığdır","ফিট"],
fit_crop:       ["Crop (fill frame)","کراپ (فریم بھر جائے)","क्रॉप (फ़्रेम भरे)","قص (يملأ الإطار)","Recortar (llenar)","Rogner (remplir)","Cortar (preencher)","Potong (isi penuh)","裁剪（填满画面）","Обрезать (заполнить)","Kırp (çerçeveyi doldur)","ক্রপ (ফ্রেম ভরাও)"],
fit_pad:        ["Pad (black bars)","پیڈ (کالی پٹیاں)","पैड (काली पट्टियाँ)","إضافة أشرطة سوداء","Barras negras","Bandes noires","Barras negras","Bilah hitam","加黑边","Чёрные полосы","Siyah çubuk ekle","প্যাড (কালো বার)"],
export:         ["Export","ایکسپورٹ","एक्सपोर्ट","تصدير","Exportar","Exporter","Exportar","Ekspor","导出","Экспорт","Aktar","এক্সপোর্ট"],

// ---------------------------------------------------------------- stages
stage_clips:    ["Clips","کلپس","क्लिप","المقاطع","Clips","Clips","Clipes","Klip","片段","Клипы","Klipler","ক্লিপ"],
stage_join:     ["Join + transitions","جوڑنا + ٹرانزیشن","जोड़ + ट्रांज़िशन","الدمج + الانتقالات","Unir + transiciones","Assemblage + transitions","Unir + transições","Gabung + transisi","拼接 + 转场","Склейка + переходы","Birleştir + geçiş","জোড়া + ট্রানজিশন"],
stage_filter:   ["Color filter","کلر فلٹر","कलर फ़िल्टर","مرشّح اللون","Filtro de color","Filtre couleur","Filtro de cor","Filter warna","色彩滤镜","Цветофильтр","Renk filtresi","কালার ফিল্টার"],
stage_captions: ["Captions","کیپشنز","कैप्शन","الترجمة","Subtítulos","Sous-titres","Legendas","Teks","字幕","Субтитры","Altyazı","ক্যাপশন"],
stage_overlays: ["Stickers & text","اسٹیکرز اور متن","स्टिकर व टेक्स्ट","الملصقات والنص","Pegatinas y texto","Stickers & texte","Adesivos e texto","Stiker & teks","贴纸与文字","Стикеры и текст","Çıkartma ve metin","স্টিকার ও টেক্সট"],
stage_voice:    ["Voice sync","آواز سنک","आवाज़ सिंक","مزامنة الصوت","Sincronizar voz","Sync voix","Sincronizar voz","Sinkron suara","配音同步","Синхр. голоса","Ses eşitleme","ভয়েস সিঙ্ক"],
stage_music:    ["Music","میوزک","म्यूज़िक","الموسيقى","Música","Musique","Música","Musik","音乐","Музыка","Müzik","মিউজিক"],
stage_sfx:      ["Sound effects","ساؤنڈ ایفیکٹس","साउंड इफ़ेक्ट","المؤثرات","Efectos","Effets","Efeitos","Efek suara","音效","Эффекты","Ses efektleri","সাউন্ড ইফেক্ট"],
stage_finalize: ["Finalizing","حتمی مرحلہ","अंतिम चरण","اللمسات الأخيرة","Finalizando","Finalisation","Finalizando","Finalisasi","收尾","Финализация","Sonlandırma","চূড়ান্তকরণ"],

// ---------------------------------------------------------------- statuses
st_processing:  ["rendering","بن رہی ہے","बन रहा है","قيد التصدير","renderizando","rendu en cours","renderizando","merender","渲染中","рендеринг","render ediliyor","রেন্ডার হচ্ছে"],
st_done:        ["done","مکمل","पूर्ण","تم","listo","terminé","concluído","selesai","完成","готово","tamam","সম্পন্ন"],
st_error:       ["error","خرابی","त्रुटि","خطأ","error","erreur","erro","galat","错误","ошибка","hata","ত্রুটি"],
st_cancelled:   ["cancelled","منسوخ","रद्द","ملغى","cancelado","annulé","cancelado","dibatalkan","已取消","отменено","iptal","বাতিল"],
elapsed:        ["elapsed","گزرا وقت","बीता समय","الوقت المنقضي","transcurrido","écoulé","decorrido","berlalu","已用","прошло","geçen","অতিবাহিত"],
eta:            ["left","باقی","शेष","المتبقي","restante","restant","restante","tersisa","剩余","осталось","kalan","বাকি"],

// ---------------------------------------------------------------- validation
v_ready:        ["Ready to render","رینڈر کے لیے تیار","रेंडर के लिए तैयार","جاهز للتصدير","Listo para renderizar","Prêt pour le rendu","Pronto para renderizar","Siap dirender","可以渲染","Готово к рендеру","Render'a hazır","রেন্ডারের জন্য প্রস্তুত"],
v_not_ready:    ["Fix the errors first","پہلے خرابیاں دور کریں","पहले त्रुटियाँ ठीक करें","أصلح الأخطاء أولاً","Corrige los errores","Corrigez les erreurs","Corrija os erros","Perbaiki galat dulu","请先修复错误","Сначала исправьте ошибки","Önce hataları giderin","আগে ত্রুটি ঠিক করুন"],
v_errors:       ["errors","خرابیاں","त्रुटियाँ","أخطاء","errores","erreurs","erros","galat","错误","ошибок","hata","ত্রুটি"],
v_warnings:     ["warnings","انتباہ","चेतावनियाँ","تحذيرات","avisos","avertissements","avisos","peringatan","警告","предупр.","uyarı","সতর্কতা"],
v_zero_duration:["Segment has no duration","سیگمنٹ کا دورانیہ صفر ہے","सेगमेंट की अवधि शून्य","مدة المقطع صفر","Segmento sin duración","Segment sans durée","Segmento sem duração","Segmen tanpa durasi","片段时长为零","Нулевая длительность","Bölüm süresi sıfır","সেগমেন্টের সময়কাল শূন্য"],
v_very_short_segment:["Very short segment","بہت مختصر سیگمنٹ","बहुत छोटा सेगमेंट","مقطع قصير جداً","Segmento muy corto","Segment très court","Segmento muito curto","Segmen sangat pendek","片段过短","Очень короткий сегмент","Çok kısa bölüm","খুব ছোট সেগমেন্ট"],
v_no_media:     ["No media assigned","کوئی میڈیا اسائن نہیں","कोई मीडिया असाइन नहीं","لا وسائط معيَّنة","Sin medio asignado","Aucun média assigné","Sem mídia atribuída","Belum ada media","未分配素材","Медиа не назначено","Medya atanmadı","কোনো মিডিয়া নেই"],
v_duplicate_media:["Same media used again","یہی میڈیا دوبارہ استعمال ہوئی","यही मीडिया दोबारा","تكرار نفس الوسيط","Medio repetido","Média répété","Mídia repetida","Media terpakai ulang","素材重复使用","Медиа повторяется","Aynı medya yine","একই মিডিয়া পুনরায়"],
v_file_missing: ["File not found on disk","فائل ڈسک پر نہیں ملی","फ़ाइल डिस्क पर नहीं","الملف غير موجود","Archivo no encontrado","Fichier introuvable","Arquivo não encontrado","File tidak ditemukan","磁盘上找不到文件","Файл не найден","Dosya bulunamadı","ফাইল ডিস্কে নেই"],
v_unreadable_media:["File cannot be read","فائل پڑھی نہیں جا سکی","फ़ाइल पढ़ी नहीं जा सकी","لا يمكن قراءة الملف","No se puede leer","Fichier illisible","Não é possível ler","File tak terbaca","文件无法读取","Файл не читается","Dosya okunamıyor","ফাইল পড়া যাচ্ছে না"],
v_video_too_short:["Video shorter than segment (will be slowed + repeated)","ویڈیو سیگمنٹ سے چھوٹی ہے (سلو + ریپیٹ ہوگی)","वीडियो सेगमेंट से छोटा (स्लो + रिपीट)","الفيديو أقصر (سيُبطأ ويُعاد)","Vídeo más corto (lento + repetido)","Vidéo trop courte (ralentie + répétée)","Vídeo mais curto (lento + repetido)","Video lebih pendek (diperlambat + diulang)","视频短于片段（将放慢并重复）","Видео короче (замедление + повтор)","Video kısa (yavaşlatılıp tekrarlanacak)","ভিডিও ছোট (স্লো + রিপিট হবে)"],
v_video_needs_image_fill:["Video very short — last frame image will fill the rest","ویڈیو بہت چھوٹی — باقی وقت آخری فریم کی امیج سے پورا ہوگا","वीडियो बहुत छोटा — बाकी समय आख़िरी फ़्रेम की इमेज से","الفيديو قصير جدًا — ستُكمل صورة الإطار الأخير","Vídeo muy corto — imagen del último fotograma completará","Vidéo très courte — image de la dernière frame en complément","Vídeo muito curto — imagem do último frame completa","Video sangat pendek — gambar frame terakhir mengisi sisanya","视频过短 — 将用末帧图片补足","Видео очень короткое — остаток заполнит кадр-картинка","Video çok kısa — kalanı son kare görseli tamamlar","ভিডিও খুব ছোট — বাকিটা শেষ ফ্রেমের ইমেজে পূর্ণ হবে"],
v_video_much_longer:["Video much longer (end will be cut)","ویڈیو بہت لمبی (آخر سے کٹے گی)","वीडियो बहुत लंबा (अंत से कटेगा)","الفيديو أطول بكثير (سيُقتطع من النهاية)","Vídeo mucho más largo (se corta el final)","Vidéo bien plus longue (fin coupée)","Vídeo muito mais longo (fim cortado)","Video jauh lebih panjang (akhir dipotong)","视频过长（将裁掉末尾）","Видео намного длиннее (конец обрежется)","Video çok uzun (sonu kesilecek)","ভিডিও অনেক লম্বা (শেষ থেকে কাটা হবে)"],
v_low_resolution:["Low resolution media","کم ریزولوشن میڈیا","कम रेज़ोल्यूशन","دقة منخفضة","Baja resolución","Faible résolution","Baixa resolução","Resolusi rendah","分辨率偏低","Низкий FPS","Düşük çözünürlük","কম রেজোলিউশন"],
v_aspect_mismatch:["Different aspect ratio","ایسپیکٹ ریشو مختلف ہے","आस्पेक्ट रेशियो भिन्न","نسبة عرض مختلفة","Relación distinta","Format différent","Proporção diferente","Rasio berbeda","画面比例不同","Другое соотношение","Farklı en-boy oranı","অ্যাসপেক্ট রেশিও ভিন্ন"],
v_low_fps:      ["Low frame rate","کم فریم ریٹ","कम फ़्रेम रेट","معدل إطارات منخفض","FPS bajo","Faible FPS","FPS baixo","FPS rendah","帧率偏低","Низкий FPS","Düşük FPS","কম ফ্রেম রেট"],
v_timeline_voice_mismatch:["Timeline length ≠ voice length","ٹائم لائن اور آواز کی لمبائی مختلف","टाइमलाइन ≠ आवाज़ की लंबाई","طول الخط الزمني ≠ الصوت","Duración ≠ voz","Durée ≠ voix","Duração ≠ voz","Durasi ≠ suara","时间轴与配音时长不符","Длина ≠ голос","Süre ≠ ses","টাইমলাইন ≠ ভয়েস দৈর্ঘ্য"],
v_timeline_voice_matched: ["Timeline matched to voice duration","ٹائم لائن اور آواز کی لمبائی برابر ہو گئی","टाइमलाइन और आवाज़ की लंबाई बराबर हो गई","تمت مطابقة طول الخط الزمني مع الصوت","Línea de tiempo ajustada a la voz","Minutage ajusté à la voix","Linha do tempo ajustada à voz","Timeline sesuai dengan durasi suara","时间轴已与配音时长对齐","Таймлайн выровнен по длительности голоса","Zamanlama ses süresiyle eşleşti","টাইমলাইন এবং ভয়েস দৈর্ঘ্য মিলে গেছে"],
v_no_caption_text:   ["Segments have no text (captions will be skipped)","سیگمنٹس میں کوئی ٹیکسٹ نہیں ہے (کیپشنز نہیں بنیں گے)","सेगमेंट में कोई टेक्स्ट नहीं (कैप्शन छूट जाएँगे)","المقاطع لا تحتوي على نص","Los segmentos no tienen texto","Les segments n'ont pas de texte","Segmentos sem texto","Segmen tidak ada teks","片段中没有文本（将跳过字幕）","В сегментах нет текста (субтитры будут пропущены)","Bölümlerde metin yok (altyazı atlanacak)","সেগমেন্টে কোনো টেক্সট নেই"],

// ---------------------------------------------------------------- messages
msg_need_voice: ["Upload a voice file first.","پہلے آواز کی فائل اپلوڈ کریں۔","पहले आवाज़ फ़ाइल अपलोड करें।","ارفع ملف الصوت أولاً.","Sube primero la voz.","Envoyez d'abord la voix.","Envie a voz primeiro.","Unggah suara dulu.","请先上传配音。","Сначала загрузите голос.","Önce ses dosyası yükleyin.","আগে ভয়েস ফাইল আপলোড করুন।"],
msg_need_timing:["Set the timing first.","پہلے ٹائمنگ سیٹ کریں۔","पहले टाइमिंग सेट करें।","حدّد التوقيت أولاً.","Define primero los tiempos.","Définissez d'abord le minutage.","Defina os tempos primeiro.","Atur waktu dulu.","请先设置时间轴。","Сначала задайте тайминг.","Önce zamanlamayı ayarlayın.","আগে টাইমিং সেট করুন।"],
msg_saved:      ["Saved.","محفوظ ہو گیا۔","सेव हो गया।","تم الحفظ.","Guardado.","Enregistré.","Salvo.","Tersimpan.","已保存。","Сохранено.","Kaydedildi.","সেভ হয়েছে।"],
msg_loaded:     ["Loaded.","لوڈ ہو گیا۔","लोड हो गया।","تم التحميل.","Cargado.","Chargé.","Carregado.","Dimuat.","已加载。","Загружено.","Yüklendi.","লোড হয়েছে।"],
msg_deleted:    ["Deleted.","ڈیلیٹ ہو گیا۔","हट गया।","تم الحذف.","Eliminado.","Supprimé.","Excluído.","Terhapus.","已删除。","Удалено.","Silindi.","মুছে গেছে।"],
msg_render_done:["Video is ready!","ویڈیو تیار ہے!","वीडियो तैयार है!","الفيديو جاهز!","¡Vídeo listo!","Vidéo prête !","Vídeo pronto!","Video siap!","视频已完成！","Видео готово!","Video hazır!","ভিডিও তৈরি!"],
msg_blocked:    ["Render blocked — fix the errors below.","رینڈر رک گئی — نیچے کی خرابیاں دور کریں۔","रेंडर रुका — नीचे की त्रुटियाँ ठीक करें।","تم إيقاف التصدير — أصلح الأخطاء.","Render bloqueado: corrige los errores.","Rendu bloqué : corrigez les erreurs.","Render bloqueado: corrija os erros.","Render dihentikan — perbaiki galat.","渲染已阻止 — 请修复错误。","Рендер остановлен — исправьте ошибки.","Render engellendi — hataları giderin.","রেন্ডার আটকেছে — ত্রুটি ঠিক করুন।"],
msg_auto_assigned:["auto-assigned","خود اسائن ہوئیں","स्वतः असाइन","تم التعيين تلقائياً","asignados solos","assignés auto","atribuídos auto","otomatis ditetapkan","已自动分配","назначено авто","otomatik atandı","স্বয়ংক্রিয় অ্যাসাইন"],
msg_overlap:    ["Overlapping rows:","اوورلیپ ہونے والی رَوز:","ओवरलैप पंक्तियाँ:","صفوف متداخلة:","Filas solapadas:","Lignes qui se chevauchent :","Linhas sobrepostas:","Baris tumpang tindih:","重叠的行：","Пересекающиеся строки:","Çakışan satırlar:","ওভারল্যাপ সারি:"],
msg_voice_mismatch:["Timeline does not match voice length.","ٹائم لائن آواز کی لمبائی سے میل نہیں کھاتی۔","टाइमलाइन आवाज़ से मेल नहीं खाती।","الخط الزمني لا يطابق طول الصوت.","La duración no coincide con la voz.","La durée ne correspond pas à la voix.","A duração não bate com a voz.","Durasi tak cocok dengan suara.","时间轴与配音时长不匹配。","Длительность не совпадает с голосом.","Süre ses ile uyuşmuyor.","টাইমলাইন ভয়েসের সাথে মিলছে না।"],
match_voice:    ["Match to voice","آواز سے ملائیں","आवाज़ से मिलाएँ","مطابقة مع الصوت","Ajustar a la voz","Ajuster à la voix","Ajustar à voz","Sesuaikan dg suara","匹配配音时长","Выровнять по голосу","Sese uyarla","ভয়েসের সাথে মেলান"],
msg_voice_matched:["Timeline matched to voice duration! ✅","ٹائم لائن آواز کی لمبائی سے مل گئی! ✅","टाइमलाइन आवाज़ की लंबाई से मिल गई! ✅","تم ضبط الخط الزمني مع الصوت! ✅","¡Línea de tiempo ajustada a la voz! ✅","Minutage ajusté à la voix ! ✅","Timeline ajustada à voz! ✅","Timeline disesuaikan dg suara! ✅","时间轴已匹配配音时长！✅","Длина видео выровнена по голосу! ✅","Zamanlama ses süresine eşitlendi! ✅","টাইমলাইন ভয়েস দৈর্ঘ্যের সাথে মিলেছে! ✅"],
msg_no_projects:["No saved projects yet.","ابھی کوئی محفوظ پروجیکٹ نہیں۔","अभी कोई सेव प्रोजेक्ट नहीं।","لا مشاريع محفوظة بعد.","Aún no hay proyectos.","Aucun projet enregistré.","Nenhum projeto salvo.","Belum ada proyek.","还没有已保存项目。","Сохранённых проектов нет.","Kayıtlı proje yok.","এখনো কোনো সেভ প্রজেক্ট নেই।"],
msg_confirm_delete:["Delete this project?","یہ پروجیکٹ ڈیلیٹ کریں؟","यह प्रोजेक्ट हटाएँ?","حذف هذا المشروع؟","¿Eliminar este proyecto?","Supprimer ce projet ?","Excluir este projeto?","Hapus proyek ini?","删除该项目？","Удалить проект?","Bu proje silinsin mi?","এই প্রজেক্ট মুছবেন?"],
msg_missing_files:["Some files are missing — upload them again.","کچھ فائلیں غائب ہیں — دوبارہ اپلوڈ کریں۔","कुछ फ़ाइलें गायब — फिर अपलोड करें।","بعض الملفات مفقودة — أعد رفعها.","Faltan archivos: vuelve a subirlos.","Fichiers manquants : renvoyez-les.","Arquivos faltando: envie de novo.","Ada file hilang — unggah lagi.","部分文件缺失 — 请重新上传。","Некоторые файлы отсутствуют.","Bazı dosyalar eksik — yeniden yükleyin.","কিছু ফাইল নেই — আবার আপলোড করুন।"],
msg_ffmpeg_missing:["FFmpeg not found — rendering will fail.","FFmpeg نہیں ملا — رینڈر ناکام ہوگی۔","FFmpeg नहीं मिला — रेंडर विफल होगा।","FFmpeg غير موجود — سيفشل التصدير.","FFmpeg no encontrado.","FFmpeg introuvable.","FFmpeg não encontrado.","FFmpeg tidak ditemukan.","未找到 FFmpeg — 渲染会失败。","FFmpeg не найден — рендер не пройдёт.","FFmpeg bulunamadı.","FFmpeg পাওয়া যায়নি — রেন্ডার ব্যর্থ হবে।"],
msg_server_down:["Cannot reach the server.","سرور سے رابطہ نہیں ہو رہا۔","सर्वर से संपर्क नहीं।","لا يمكن الوصول للخادم.","No se puede conectar al servidor.","Serveur inaccessible.","Servidor inacessível.","Server tak terjangkau.","无法连接服务器。","Сервер недоступен.","Sunucuya erişilemiyor.","সার্ভারে সংযোগ নেই।"],
ready:["ready","تیار","तैयार","جاهز","listo","prêt","pronto","siap","已就绪","готово","hazır","প্রস্তুত"],
preview_sample:["Your caption looks like this","آپ کا کیپشن ایسا نظر آئے گا","आपका कैप्शन ऐसा दिखेगा","سيظهر التعليق بهذا الشكل","Tu subtítulo se ve así","Votre sous-titre ressemble à ceci","Sua legenda fica assim","Teks Anda tampak seperti ini","你的字幕是这样的","Ваши субтитры выглядят так","Altyazınız böyle görünür","আপনার ক্যাপশন এমন দেখাবে"],
captions_off:["Captions are off","کیپشن بند ہیں","कैप्शन बंद हैं","التعليقات مغلقة","Subtítulos desactivados","Sous-titres désactivés","Legendas desativadas","Teks dimatikan","字幕已关闭","Субтитры выключены","Altyazılar kapalı","ক্যাপশন বন্ধ"],
msg_uploaded:["Uploaded.","اپلوڈ ہو گیا۔","अपलोड हो गया।","تم الرفع.","Subido.","Envoyé.","Enviado.","Terunggah.","已上传。","Загружено.","Yüklendi.","আপলোড হয়েছে।"],
msg_applied:["Applied.","لاگو ہو گیا۔","लागू हो गया।","تم التطبيق.","Aplicado.","Appliqué.","Aplicado.","Diterapkan.","已应用。","Применено.","Uygulandı.","প্রয়োগ হয়েছে।"],
msg_cancelling:["Cancelling…","منسوخ ہو رہی ہے…","रद्द हो रहा है…","جارٍ الإلغاء…","Cancelando…","Annulation…","Cancelando…","Membatalkan…","正在取消…","Отмена…","İptal ediliyor…","বাতিল হচ্ছে…"],
msg_exported:["Export ready.","ایکسپورٹ تیار ہے۔","एक्सपोर्ट तैयार。","التصدير جاهز.","Exportación lista.","Export prêt.","Exportação pronta.","Ekspor siap.","导出完成。","Экспорт готов.","Dışa aktarma hazır.","এক্সপোর্ট প্রস্তুত。"],
msg_need_media:["Upload your media first.","پہلے اپنی میڈیا اپلوڈ کریں۔","पहले मीडिया अपलोड करें。","ارفع الوسائط أولاً.","Sube primero tus medios.","Importez d'abord vos médias.","Envie suas mídias primeiro.","Unggah media dulu.","请先上传素材。","Сначала загрузите медиа.","Önce medya yükleyin.","আগে মিডিয়া আপলোড করুন。"],
msg_font_loaded:["Custom font loaded.","کسٹم فونٹ لوڈ ہو گیا۔","कस्टम फ़ॉन्ट लोड हुआ。","تم تحميل الخط.","Fuente cargada.","Police chargée.","Fonte carregada.","Font dimuat.","字体已加载。","Шрифт загружен.","Yazı tipi yüklendi.","ফন্ট লোড হয়েছে。"],
msg_render_running:["A render is already running.","ایک رینڈر پہلے سے چل رہی ہے۔","एक रेंडर पहले से चल रहा है。","هناك تصدير جارٍ بالفعل.","Ya hay un render en curso.","Un rendu est déjà en cours.","Já existe um render em andamento.","Render sedang berjalan.","已有渲染在进行中。","Рендер уже выполняется.","Zaten bir render çalışıyor.","একটি রেন্ডার চলছে。"],
no_segments:["No segments yet — set timing first.","ابھی کوئی سیگمنٹ نہیں — پہلے ٹائمنگ دیں۔","अभी कोई सेगमेंट नहीं — पहले टाइमिंग दें。","لا مقاطع بعد — حدّد التوقيت أولاً.","Sin segmentos — define el tiempo.","Aucun segment — définissez le minutage.","Sem segmentos — defina o tempo.","Belum ada segmen — atur waktu dulu.","还没有片段 — 请先设置时间。","Сегментов нет — задайте тайминг.","Segment yok — önce zamanlama.","কোনো সেগমেন্ট নেই — আগে টাইমিং দিন。"],
view_workflow: ["Workflow","ورک فلو","वर्कफ़्लो","سير العمل","Flujo","Flux","Fluxo","Alur Kerja","工作流","Процесс","İş akışı","ওয়ার্কফ্লো"],
view_editor: ["Editing Panel","ایڈیٹنگ پینل","एडिटिंग पैनल","لوحة التحرير","Panel de edición","Panneau d'édition","Painel de edição","Panel Pengeditan","剪辑面板","Панель монтажа","Kurgu Paneli","এডিটিং প্যানেল"],
admin_tools: ["Admin & Tools","ایڈمن اور ٹولز","एडमिन और टूल्स","الأدوات والإدارة","Admin y herramientas","Admin et outils","Admin e ferramentas","Admin & Alat","管理与工具","Инструменты админа","Yönetici ve Araçlar","অ্যাডমিন ও টুলস"],
logout: ["Logout","لاگ آؤٹ","लॉग आउट","تسجيل خروج","Cerrar sesión","Déconnexion","Sair","Keluar","退出登录","Выйти","Çıkış Yap","লগআউট"],
interactive_editing_panel: ["Timeline Editing Workbench","ٹائم لائن ایڈیٹنگ ورک بینچ","टाइमलाइन एडिटिंग वर्कबेंच","منصة تحرير الخط الزمني","Mesa de edición de línea de tiempo","Table de montage chronologique","Mesa de edição da timeline","Meja Edit Timeline","时间轴剪辑工作台","Монтажный стол таймлайна","Zaman Çizelgesi Kurgu Masası","টাইমলাইন এডিটিং ওয়ার্কবেঞ্চ"],
play_preview: ["Play Audio","آواز سنیں","ऑडियो चलाएँ","تشغيل الصوت","Reproducir audio","Lire l'audio","Tocar áudio","Putar audio","播放音频","Воспроизвести аудио","Sesi Oynat","অডিও চালান"],
back_to_workflow: ["Back to Steps","واپس مراحل پر","चरणों पर वापस","العودة للخطوات","Volver a pasos","Retour aux étapes","Voltar às etapas","Kembali ke langkah","返回步骤","Назад к шагам","Adımlara dön","পদক্ষেপে ফিরুন"],
track_media: ["Media Clips","میڈیا کلپس","मीडिया क्लिप्स","مقاطع الوسائط","Clips multimedia","Clips média","Clips de mídia","Klip Media","媒体片段","Медиа клипы","Medya Klipleri","মিডিয়া ক্লিপ"],
track_captions: ["Captions","کیپشنز","कैप्शन","الترجمة","Subtítulos","Sous-titres","Legendas","Teks Takarir","字幕","Субтитры","Altyazılar","ক্যাপশন"],
track_voice: ["Voice Audio","آواز","आवाज़","صوت التعليق","Voz de audio","Voix audio","Áudio da voz","Audio Suara","配音音频","Аудио озвучки","Ses Kaydı","ভয়েস অডিও"],
track_music: ["Music & SFX","میوزک اور ساؤنڈز","म्यूज़िक और प्रभाव","الموسيقى والمؤثرات","Música y efectos","Musique et effets","Música e efeitos","Musik & SFX","背景音乐与音效","Музыка и эффекты","Müzik ve Efektler","মিউজিক ও প্রভাব"],
admin_panel_title: ["Control Center & Diagnostics","کنٹرول سینٹر اور ڈائیگنوسٹکس","कंट्रोल सेंटर और डायग्नोस्टिक्स","مركز التحكم والتشخيص","Centro de control y diagnóstico","Centre de contrôle et diagnostic","Centro de controle e diagnóstico","Pusat Kontrol & Diagnostik","控制中心与诊断","Центр управления и диагностики","Kontrol Merkezi ve Teşhis","কন্ট্রোল সেন্টার ও ডায়াগনস্টিক"],
};


/* ================= runtime ================= */

let CURRENT = "en";

function detectLang() {
  const saved = localStorage.getItem("veb_lang");
  if (saved && LANGS.includes(saved)) return saved;
  const nav = (navigator.languages || [navigator.language || "en"]).map((l) => String(l).toLowerCase());
  for (const tag of nav) {
    const base = tag.split("-")[0];
    if (LANGS.includes(base)) return base;
  }
  return "en";
}

function t(key, fallback) {
  const row = T[key];
  if (!row) return fallback !== undefined ? fallback : key;
  const idx = LANGS.indexOf(CURRENT);
  return (idx >= 0 && row[idx]) || row[0] || key;
}

function currentLang() { return CURRENT; }
function isRTL() { return (LANG_META[CURRENT] || {}).dir === "rtl"; }

function applyI18n(root) {
  (root || document).querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    const val = t(key, null);
    if (val !== null) el.textContent = val;
  });
  (root || document).querySelectorAll("[data-i18n-ph]").forEach((el) => {
    const val = t(el.getAttribute("data-i18n-ph"), null);
    if (val !== null) el.placeholder = val;
  });
}

function setLang(code, onChange) {
  if (!LANGS.includes(code)) code = "en";
  CURRENT = code;
  localStorage.setItem("veb_lang", code);
  const meta = LANG_META[code];
  document.documentElement.lang = code;
  document.documentElement.dir = meta.dir;
  applyI18n(document);
  if (typeof onChange === "function") onChange(code);
}

function buildLangSelect(select, onChange) {
  select.textContent = "";
  LANGS.forEach((code) => {
    const opt = document.createElement("option");
    opt.value = code;
    opt.textContent = LANG_META[code].name;
    select.appendChild(opt);
  });
  select.value = CURRENT;
  select.addEventListener("change", () => setLang(select.value, onChange));
}

window.I18N = { LANGS, LANG_META, t, setLang, applyI18n, detectLang, currentLang, isRTL, buildLangSelect };
