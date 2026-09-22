#!/usr/bin/env python3
"""Build full M3U playlist from Archive.org account (videos + audio)."""

import json
import re
import urllib.parse
import urllib.request
import time

UPLOADER = "ouadoudifouad334@gmail.com"
OUTPUT = "playlist.m3u"

# الصيغ المدعومة
VIDEO_EXTS = (".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v", ".ts", ".flv")
AUDIO_EXTS = (".mp3", ".m4a", ".ogg", ".flac", ".wav", ".aac", ".opus")

def clean_name(filename):
    # إزالة الامتداد
    name = re.sub(r"\.(mp4|mkv|webm|avi|mov|m4v|ts|flv|mp3|m4a|ogg|flac|wav|aac|opus|ia\.mp4)$", "", filename, flags=re.I)
    # إزالة الأرقام في البداية
    name = re.sub(r"^\d+[\.\-]?\s*", "", name)
    name = re.sub(r"^HE-\d+-", "", name)
    name = re.sub(r"^\d{4,}-", "", name)
    # إزالة الجودات
    name = re.sub(r"\s*\d{3,4}p\b", "", name, flags=re.I)
    name = re.sub(r"\s*(WEB-?DL|BluRay|BRRip|HDRip|x264|h264|AAC|HEVC)\b", "", name, flags=re.I)
    name = re.sub(r"\s*\(\d+\)\s*$", "", name)
    name = re.sub(r"\s+\d{4}\s*$", "", name)
    name = re.sub(r"\s+\d+$", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"[_\-\s\.]+$", "", name)
    return name or filename

def get_files(meta):
    """استخراج الملفات المناسبة مع تفضيل النسخ الأصلية"""
    files = meta.get("files", [])
    candidates = {}

    for f in files:
        name = f.get("name", "")
        lower = name.lower()

        # تجاهل الصور والمجلدات والملفات الصغيرة
        if any(x in lower for x in ["thumb", ".jpg", ".png", ".gif", ".xml", ".json", ".txt", ".srt", ".vtt"]):
            continue
        if "/thumbs/" in lower:
            continue

        # تحديد إذا كان فيديو أو صوت
        is_video = any(lower.endswith(ext) for ext in VIDEO_EXTS) or lower.endswith(".ia.mp4")
        is_audio = any(lower.endswith(ext) for ext in AUDIO_EXTS)

        if not (is_video or is_audio):
            continue

        # مفتاح بدون امتداد للمقارنة
        base = re.sub(r"(\.ia)?\.(mp4|mkv|webm|avi|mov|m4v|ts|flv|mp3|m4a|ogg|flac|wav|aac|opus)$", "", name, flags=re.I)

        # تفضيل الملف الأصلي على .ia.mp4
        if base in candidates:
            existing = candidates[base]["name"]
            # إذا الحالي أصلي والقديم ia → استبدل
            if existing.endswith(".ia.mp4") and not name.endswith(".ia.mp4"):
                candidates[base] = f
            # إذا كلاهما أصلي، خذ الأكبر حجمًا
            elif not name.endswith(".ia.mp4") and not existing.endswith(".ia.mp4"):
                if int(f.get("size", 0) or 0) > int(candidates[base].get("size", 0) or 0):
                    candidates[base] = f
        else:
            candidates[base] = f

    return list(candidates.values())

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

    lines = ["#EXTM3U"]
    total = 0
    groups = 0

    for item in items:
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

        files.sort(key=lambda x: x["name"])
        groups += 1
        print(f"    → {len(files)} files")

        # لوجو القائمة
        logo = f"https://archive.org/services/img/{ident}"

        for f in files:
            fname = f["name"]
            ep = clean_name(fname)
            url = f"https://archive.org/download/{ident}/" + urllib.parse.quote(fname)

            lines.append(
                f'#EXTINF:-1 tvg-name="{ep}" tvg-logo="{logo}" group-title="{title}",{ep}'
            )
            lines.append(url)
            total += 1

        time.sleep(0.3)

    content = "\n".join(lines) + "\n"
    with open(OUTPUT, "w", encoding="utf-8") as out:
        out.write(content)

    print(f"\nDone: {groups} groups, {total} items → {OUTPUT}")

if __name__ == "__main__":
    main()
