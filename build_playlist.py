#!/usr/bin/env python3
"""Build full M3U playlist from Archive.org account (videos + audio) - includes ALL media files."""

import json
import re
import urllib.parse
import urllib.request
import time

UPLOADER = "ouadoudifouad334@gmail.com"
OUTPUT = "playlist.m3u"

# كل الصيغ المدعومة (يمكنك إضافة المزيد بسهولة)
VIDEO_EXTS = (
    ".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v", ".ts", ".flv",
    ".wmv", ".mpg", ".mpeg", ".m2ts", ".vob", ".3gp", ".ogv", ".ia.mp4"
)
AUDIO_EXTS = (
    ".mp3", ".m4a", ".ogg", ".flac", ".wav", ".aac", ".opus",
    ".wma", ".aiff", ".ape", ".alac", ".ac3", ".dts"
)

def clean_name(filename):
    name = re.sub(
        r"\.(mp4|mkv|webm|avi|mov|m4v|ts|flv|wmv|mpg|mpeg|m2ts|vob|3gp|ogv|ia\.mp4|"
        r"mp3|m4a|ogg|flac|wav|aac|opus|wma|aiff|ape|alac|ac3|dts)$",
        "", filename, flags=re.I
    )
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

def get_files(meta):
    """إرجاع كل ملفات الفيديو والصوت بدون أي استبعاد أو تفضيل"""
    files = meta.get("files", [])
    result = []

    for f in files:
        name = f.get("name", "")
        lower = name.lower()

        # تجاهل فقط الصور والثمبنيلز وملفات الميتاداتا والترجمة
        if any(x in lower for x in [
            "thumb", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
            ".xml", ".json", ".txt", ".nfo", ".srt", ".vtt", ".ass", ".ssa",
            ".zip", ".rar", ".7z", ".torrent", ".md5", ".sfv"
        ]):
            continue
        if "/thumbs/" in lower or lower.endswith("/"):
            continue

        is_video = any(lower.endswith(ext) for ext in VIDEO_EXTS)
        is_audio = any(lower.endswith(ext) for ext in AUDIO_EXTS)

        if is_video or is_audio:
            result.append(f)

    return result

def main():
    print("Fetching items list...")
    all_items = []
    page = 1
    rows = 200

    while True:
        search_url = (
            "https://archive.org/advancedsearch.php?"
            + urllib.parse.urlencode({
                "q": f'uploader:"{UPLOADER}" AND (mediatype:movies OR mediatype:audio)',
                "fl[]": ["identifier", "title", "mediatype"],
                "rows": rows,
                "page": page,
                "output": "json",
                "sort[]": "publicdate desc",
            }, doseq=True)
        )

        with urllib.request.urlopen(search_url, timeout=60) as r:
            data = json.load(r)

        items = data.get("response", {}).get("docs", [])
        if not items:
            break

        all_items.extend(items)
        print(f"  Page {page}: {len(items)} items")
        page += 1
        time.sleep(0.5)

        # حماية من الحلقة اللانهائية
        if page > 50:
            break

    print(f"Total items found: {len(all_items)}")

    lines = ["#EXTM3U"]
    total = 0
    groups = 0

    for item in all_items:
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

        files.sort(key=lambda x: x["name"].lower())
        groups += 1
        print(f"    → {len(files)} files")

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
