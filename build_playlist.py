#!/usr/bin/env python3
"""Build M3U playlist with multiple custom ordered groups."""
import json
import re
import urllib.parse
import urllib.request
import time

UPLOADER = "ouadoudifouad334@gmail.com"
OUTPUT = "playlist.m3u"

SPECIAL_SERIES = {"20260925_20260925_1745"}

# سلاسل نرتب حلقاتها حسب الرقم بدون إظهار الرقم الأصلي
SPECIAL_TITLES = {
    "بلوي رسوم متحركة للأطفال",
    "السنافر الجديدة",
    "الماسة الزرقاء",
}

# المجموعة 1: الحياة الطبيعية والاجتماعية
NATURE_ORDER = [
    "الألعاب الأولمبية والرياضية",
    "تداريب كرة اليد",
    "BIBI",
    "BXL",
    "علوم الحياة والأرض",
    "حيوانات الطبيعة",
    "التكنولوجيا البدائية",
    "التكنولوجيا المستقبلية",
    "طائرات وآلات السفر",
    "تجديد الأجهزة",
    "李子柒 Liziqi",
    "التخييم",
    "أماكن مع صوت المطر",
    "أمطار وعواصف رعدية",
]

# المجموعة 2: التاريخ والثقافة والفكر
HISTORY_ORDER = [
    "تعلم الرسم - بوب روس",
    "تعلم باحتراف الشطرنج مع لعبة الشطرنج ثلاثية الأبعاد",
    "المصباح العلمي دروس في الرياضيات والفيزياء والعلوم",
    "مسرحيات صوتية عالمية",
    "الأغاني للأصفهاني دراما الإذاعة المصرية",
    "سعد الله آغا القلعة حياة وفن عبد الوهاب وفريد وأسمهان",
    "مسلسل طاش ما طاش",
    "مسلسل الأغاني لأبي الفرج الأصفهاني",
    "مسلسل مجالس العرب من مجالس هارون الرشيد",
    "مسلسل ابن خلدون تمثيل نور الشريف",
    "مسلسل على هامش السيرة د طه حسين",
    "مسلسل كان ياما كان الجزء الأول",
    "أفلام ومسرحيات عادل إمام",
    "أفلام عربية وغربية خاصة بـ فؤاد الودودي",
    "أفلام إسلامية فارسية مدبلجة",
    "سلسلة عظماء الإسلام",
    "العلم والايمان - مصطفى محمود",
    "مكتبة الفلسفة وعلم النفس والإجتماع المرئية الخاصة بفؤاد الودودي",
    "تاريخ الإختراعات",
    "تأريخ القصص الدينية",
    "تاريخ الأمم",
    "بين الأسطورة والمعلومة",
    "الأنوناكي حقيقة العبودية والتلاعب بمورثاتنا الجينية",
    "التاريخ الفرعوني المعارف الضائعة مع أحمد عدلي",
    "ثقافة عامة علمية مع معتز محسن",
    "وثائق مرئية إسلامية تعليق سلامة محاسنة",
    "الحضارة الإسلامية",
    "الخلافة الإسلامية في ألف عام",
    "الفكر الإسلامي المعاصر",
]

# المجموعة 3: المحتوى المغربي
MOROCCAN_ORDER = [
    "التصوف العرفاني",
    "أغاني دينية شيعية للرادود باسم الكربلائي",
    "ذاكرة المدن - تاريخ مدينة فاس وسلا ومكناس والرباط ومراكش",
    "أحمد عصيد تحليل الشأن الإجتماعي المغربي",
    "روحانيات ومنوعات مغربية",
    "مراكش وفاس زمان لقطات قديمة",
    "تاريخ ملوك المغرب العلويين",
    "أفلام ومسرحيات مغربية",
]

# المجموعة 4: المحتوى الإسرائيلي والعبري
ISRAELI_ORDER = [
    "تعلم العبرية مع داوود",
    "المنتخب الإسرائيلي النسوي لكرة اليد",
    "المسلسل الإسرائيلي نخب الحب",
    "موسيقى وأغاني إسرائيلية",
    "أغاني عبرية تعليمية للأطفال",
    "مرئيات إسرائيلية للأطفال",
    "حلقات من مسلسلات إسرائيلية لليافعين",
    "حلقات مجمعة من مسلسلات إسرائيلية لليافعين",
    "مقاطع من سلسلة اليهود قادمون",
    "المرئيات السياسية لدولة إسرائيل",
    "أناشيد وأغاني دينية يهودية ليهود متدينين",
    "تعريف بأهل الكتاب من طرف الحاخام إلحانان ميلر",
    "دروس حاخامات موقع صندوق التوراة",
    "قراءة المزامير لأيام الأسبوع بالعبرية",
    "التوراة أسفار موسى الخمسة بالعبرية",
    "الكتاب المقدس - العهد القديم بالعربية",
    "الكتاب المقدس - العهد الجديد",
]

# المجموعة 5: الأغاني والأفلام
MIDDLE_ORDER = [
    "قداسة البابا تواضروس الثاني",
    "سفر المزامير وسفر يشوع بن سيراخ",
    "ترانيم مسيحية أرثوذكسية",
    "أغاني وموسيقى صوفية",
    "أغاني روسية وفرنسية وكردية للأطفال",
    "أغاني جام بيتس خاصة بفؤاد الودودي",
    "أغاني بالذكاء الإصطناعي",
    "TOP stef",
    "أغاني فرنسية صوتية لـ إنريكو ماسياس",
    "أغاني أوروبية خاصة بفؤاد",
    "أغاني وموسيقى أفغانية",
    "أغاني هندية خاصة بفؤاد",
    "أغاني روسية خاصة بفؤاد الودودي",
    "أغاني عربية خاصة بفؤاد الودودي",
]

# المجموعة 6: الرسوم المتحركة
CARTOON_ORDER = [
    "مخلص صديق الحيوان",
    "ملحمة جلجامش",
    "بانشو الظريف",
    "كرتون روسي قديم",
    "توم وجيري",
    "أفلام ميكي ماوس",
    "العصر الذهبي لديزني",
    "بينكي وبرين",
    "ينابيع المعرفة",
    "اسألوا لبيبة",
    "كان يا ما كان",
    "قصص القرآن يحيى الفخراني",
    "من قصص القرآن والأنبياء بالصلصال",
    "السنافر حلقات كلاسيكية",
    "السنافر حلقات جديدة",
    "بلوي",
    "الخروف شون",
    "المحقق كونان",
    "كرم المخترع الصغير",
    "الماسة الزرقاء",
    "الأحلام الذهبية",
    "حكايات ما أحلاها",
    "حكايات عالمية",
    "أغاني رسوم متحركة كلاسيكية",
    "الحلقة الأولى من رسوم متحركة كلاسيكية",
]

# المجموعة 7: القرآن الكريم (الأخيرة)
QURAN_ORDER = [
    "القرآن الكريم القارئ علي صلاح عمر",
    "القرآن الكريم مقاطع",
    "مرئيات الشيخ عبد الباسط عبد الصمد",
    "مرئيات الشيخ محمود خليل الحصري",
    "مصحف الشيخ محمود خليل الحصري رحمه الله برواية حفص عن عاصم",
    "ختمة الأجزاء الشيخ محمود خليل الحصري رحمه الله برواية حفص عن عاصم",
    "أسطوانات الشيخ محمود خليل الحصري رحمه الله",
    "فؤاد الودودي",
]

VIDEO_EXTS = (".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v", ".ts", ".flv")
AUDIO_EXTS = (".mp3", ".m4a", ".ogg", ".flac", ".wav", ".aac", ".opus")


def get_episode_number(filename):
    """
    استخراج رقم الحلقة بذكاء:
    - يفضّل صيغة E100 / EP100 / Episode 100
    - ثم الرقم في بداية الاسم (1. 2. 10.)
    - ثم أكبر رقم يظهر
    """
    name = re.sub(r"\.(mp4|mkv|webm|avi|mov|m4v|ts|flv|mp3|m4a|ogg|flac|wav|aac|opus|ia\.mp4)$", "", filename, flags=re.I)
    name = name.strip()
    # 1) صيغة E100 أو EP100 أو Episode 100 أو Ep 100
    match = re.search(r'(?:EP?|Episode)\s*0*(\d+)', name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    # 2) رقم في بداية الاسم مثل: 1. أو 10- أو 001_
    match = re.match(r'^(\d+)[\.\-\s_]*', name)
    if match:
        return int(match.group(1))
    # 3) أي رقم آخر (نأخذ الأكبر عادةً يكون رقم الحلقة)
    numbers = re.findall(r'\d+', name)
    if numbers:
        return max(int(n) for n in numbers)
    return 0


def is_special_item(ident, title):
    """سلاسل نرتب حلقاتها حسب الرقم"""
    if ident in SPECIAL_SERIES:
        return True
    t = (title or "").lower()
    for key in SPECIAL_TITLES:
        if key.lower() in t:
            return True
    return False


def has_trailing_paren_number(files):
    """يتحقق إذا كانت أغلب الملفات تنتهي برقم بين قوسين مثل (1) أو (28)"""
    if not files:
        return False
    count = 0
    for f in files:
        name = f.get("name", "")
        base = re.sub(r"\.(mp4|mkv|webm|avi|mov|m4v|ts|flv|mp3|m4a|ogg|flac|wav|aac|opus|ia\.mp4)$", "", name, flags=re.I)
        if re.search(r'\(\d+\)\s*$', base):
            count += 1
    # إذا كان نصف الملفات أو أكثر يحتوي على الرقم بين قوسين
    return count >= max(1, len(files) * 0.5)


def natural_key(s):
    """ترتيب طبيعي: الأرقام تُعامل كأرقام وليس كنص"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]


def clean_name_normal(filename):
    name = re.sub(r"\.(mp4|mkv|webm|avi|mov|m4v|ts|flv|mp3|m4a|ogg|flac|wav|aac|opus|ia\.mp4)$", "", filename, flags=re.I)
    name = re.sub(r"^\d+[\.\-]?\s*", "", name)
    name = re.sub(r"^HE-\d+-", "", name)
    name = re.sub(r"^\d{4,}-", "", name)
    name = re.sub(r"\s*\d{3,4}p\b", "", name, flags=re.I)
    name = re.sub(r"\s*(WEB-?DL|BluRay|BRRip|HDRip|x264|h264|AAC|HEVC)\b", "", name, flags=re.I)
    name = re.sub(r"\s*\(\d+\)\s*$", "", name)
    name = re.sub(r"\s+\d{4}\s*$", "", name)
    name = re.sub(r"\s+\d+$", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"[_\-\s\.]+$", "", name)
    return name or filename


def clean_name_special(filename):
    name = re.sub(r"\.(mp4|mkv|webm|avi|mov|m4v|ts|flv|mp3|m4a|ogg|flac|wav|aac|opus|ia\.mp4)$", "", filename, flags=re.I)
    ep_num = get_episode_number(name)
    name = re.sub(r"^\d+[\.\-]?\s*", "", name)
    name = re.sub(r"^HE-\d+-", "", name)
    name = re.sub(r"^\d{4,}-", "", name)
    name = re.sub(r"\s*\d{3,4}p\b", "", name, flags=re.I)
    name = re.sub(r"\s*(WEB-?DL|BluRay|BRRip|HDRip|x264|h264|AAC|HEVC|HD)\b", "", name, flags=re.I)
    name = re.sub(r"\s*\(\d+\)\s*$", "", name)
    name = re.sub(r"\s+\d{4}\s*$", "", name)
    name = re.sub(r"\s+\d+$", "", name)
    name = re.sub(r"\s*פרק\s*$", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"[_\-\s\.]+$", "", name)
    if ep_num > 0:
        return f"{ep_num:03d} - {name}" if name else f"{ep_num:03d}"
    return name or filename


def clean_name_keep(filename):
    """تنظيف خفيف مع الإبقاء على الرقم بين قوسين في النهاية"""
    name = re.sub(r"\.(mp4|mkv|webm|avi|mov|m4v|ts|flv|mp3|m4a|ogg|flac|wav|aac|opus|ia\.mp4)$", "", filename, flags=re.I)
    name = re.sub(r"^\d+[\.\-]?\s*", "", name)
    name = re.sub(r"^HE-\d+-", "", name)
    name = re.sub(r"^\d{4,}-", "", name)
    name = re.sub(r"\s*\d{3,4}p\b", "", name, flags=re.I)
    name = re.sub(r"\s*(WEB-?DL|BluRay|BRRip|HDRip|x264|h264|AAC|HEVC|HD)\b", "", name, flags=re.I)
    # لا نحذف (رقم) ولا الرقم في النهاية
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"[_\-\s\.]+$", "", name)
    return name or filename


def get_list_type(title):
    t = title.lower()
    # نفحص المجموعات الأخرى أولاً حتى لا يسرق "فؤاد الودودي" العناوين
    for key in NATURE_ORDER:
        if key.lower() in t:
            return "nature"
    for key in HISTORY_ORDER:
        if key.lower() in t:
            return "history"
    for key in MOROCCAN_ORDER:
        if key.lower() in t:
            return "moroccan"
    for key in ISRAELI_ORDER:
        if key.lower() in t:
            return "israeli"
    for key in MIDDLE_ORDER:
        if key.lower() in t:
            return "middle"
    if "رسوم متحركة للأطفال" in t:
        return "cartoon"
    for key in CARTOON_ORDER:
        if key.lower() in t:
            return "cartoon"
    # القرآن في الأخير (حتى لا يلتقط العناوين التي تحتوي "فؤاد الودودي")
    for key in QURAN_ORDER:
        if key.lower() in t:
            return "quran"
    return "normal"


def get_order(title, order_list):
    t = title.lower()
    for i, key in enumerate(order_list):
        if key.lower() in t:
            return i
    return 999


def get_quality_score(f):
    name = f.get("name", "").lower()
    size = int(f.get("size", 0) or 0)
    score = size
    if any(x in name for x in ["512kb", "256kb", "128kb", "64kb", "low", "small"]):
        score -= 10_000_000_000
    if name.endswith(".ia.mp4"):
        score -= 5_000_000_000
    if not name.endswith(".ia.mp4") and "512kb" not in name:
        score += 1_000_000_000
    return score


def get_files(meta):
    files = meta.get("files", [])
    candidates = {}
    for f in files:
        name = f.get("name", "")
        lower = name.lower()
        if any(x in lower for x in ["thumb", ".jpg", ".png", ".gif", ".xml", ".json", ".txt", ".srt", ".vtt"]):
            continue
        if "/thumbs/" in lower:
            continue
        is_video = any(lower.endswith(ext) for ext in VIDEO_EXTS) or lower.endswith(".ia.mp4")
        is_audio = any(lower.endswith(ext) for ext in AUDIO_EXTS)
        if not (is_video or is_audio):
            continue
        base = re.sub(r"(\.ia)?\.(mp4|mkv|webm|avi|mov|m4v|ts|flv|mp3|m4a|ogg|flac|wav|aac|opus)$", "", name, flags=re.I)
        score = get_quality_score(f)
        if base not in candidates or score > candidates[base].get("_score", -1):
            f["_score"] = score
            candidates[base] = f
    result = []
    for f in candidates.values():
        f.pop("_score", None)
        result.append(f)
    return result


def main():
    print("Fetching items list...")
    search_url = (
        "https://archive.org/advancedsearch.php?"
        + urllib.parse.urlencode({
            "q": f'uploader:"{UPLOADER}" AND (mediatype:movies OR mediatype:audio)',
            "fl[]": ["identifier", "title", "mediatype"],
            "rows": 300,
            "page": 1,
            "output": "json",
            "sort[]": "publicdate desc",
        }, doseq=True)
    )
    with urllib.request.urlopen(search_url, timeout=60) as r:
        data = json.load(r)
    items = data.get("response", {}).get("docs", [])
    print(f"Found {len(items)} items")

    normal_items = []
    quran_items = []
    nature_items = []
    history_items = []
    moroccan_items = []
    israeli_items = []
    middle_items = []
    cartoon_items = []

    for item in items:
        title = item.get("title") or item["identifier"]
        list_type = get_list_type(title)
        if list_type == "quran":
            quran_items.append(item)
        elif list_type == "nature":
            nature_items.append(item)
        elif list_type == "history":
            history_items.append(item)
        elif list_type == "moroccan":
            moroccan_items.append(item)
        elif list_type == "israeli":
            israeli_items.append(item)
        elif list_type == "middle":
            middle_items.append(item)
        elif list_type == "cartoon":
            cartoon_items.append(item)
        else:
            normal_items.append(item)

    quran_items.sort(key=lambda x: get_order(x.get("title", ""), QURAN_ORDER))
    nature_items.sort(key=lambda x: get_order(x.get("title", ""), NATURE_ORDER))
    history_items.sort(key=lambda x: get_order(x.get("title", ""), HISTORY_ORDER))
    moroccan_items.sort(key=lambda x: get_order(x.get("title", ""), MOROCCAN_ORDER))
    israeli_items.sort(key=lambda x: get_order(x.get("title", ""), ISRAELI_ORDER))
    middle_items.sort(key=lambda x: get_order(x.get("title", ""), MIDDLE_ORDER))
    cartoon_items.sort(key=lambda x: get_order(x.get("title", ""), CARTOON_ORDER))

    # الترتيب النهائي: عادي → حياة طبيعية → تاريخ → مغربي → إسرائيلي → وسط → رسوم متحركة → قرآن (الأخيرة)
    final_items = normal_items + nature_items + history_items + moroccan_items + israeli_items + middle_items + cartoon_items + quran_items

    lines = ["#EXTM3U"]
    total = 0
    groups = 0

    for item in final_items:
        ident = item["identifier"]
        title = (item.get("title") or ident).replace('"', "'")
        print(f"  Processing: {title[:60]}...")
        try:
            meta_url = f"https://archive.org/metadata/{ident}"
            with urllib.request.urlopen(meta_url, timeout=45) as r:
                meta = json.load(r)
        except Exception as e:
            print(f"    SKIP: {e}")
            continue

        files = get_files(meta)
        if not files:
            print(f"    → no media files")
            continue

        is_special = is_special_item(ident, title)
        is_keep = (not is_special) and has_trailing_paren_number(files)

        if is_special:
            files.sort(key=lambda x: (get_episode_number(x["name"]), x["name"].lower()))
        elif is_keep:
            # ترتيب طبيعي + الإبقاء على الرقم بين قوسين
            files.sort(key=lambda x: natural_key(x["name"]))
        else:
            files.sort(key=lambda x: x["name"])

        groups += 1
        list_type = get_list_type(title)
        keep_flag = "KEEP" if is_keep else list_type.upper()
        print(f"    → {len(files)} files [{keep_flag}]")
        logo = f"https://archive.org/services/img/{ident}"
        for f in files:
            fname = f["name"]
            if is_special:
                ep = clean_name_special(fname)
            elif is_keep:
                ep = clean_name_keep(fname)
            else:
                ep = clean_name_normal(fname)
            url = f"https://archive.org/download/{ident}/" + urllib.parse.quote(fname)
            lines.append(f'#EXTINF:-1 tvg-name="{ep}" tvg-logo="{logo}" group-title="{title}",{ep}')
            lines.append(url)
            total += 1
        time.sleep(0.3)

    content = "\n".join(lines) + "\n"
    with open(OUTPUT, "w", encoding="utf-8") as out:
        out.write(content)
    print(f"\nDone: {groups} groups, {total} items → {OUTPUT}")


if __name__ == "__main__":
    main()
