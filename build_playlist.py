#!/usr/bin/env python3
"""Build M3U playlist - each video gets its own thumbnail when available."""

import json
import re
import urllib.parse
import urllib.request
import time

UPLOADER = "ouadoudifouad334@gmail.com"
OUTPUT = "playlist.m3u"

VIDEO_EXTS = (".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v", ".ts", ".flv")
AUDIO_EXTS = (".mp3", ".m4a", ".ogg", ".flac", ".wav", ".aac", ".opus")

def clean_name(filename):
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
    images = {}  # لحفظ الصور الموجودة

    for f in files:
        name = f.get("name", "")
        lower = name.lower()

        # جمع الصور لاستخدامها كأيقونات
        if lower.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")) and "thumb" not in lower:
            base_img = re.sub(r"\.(jpg|jpeg|png|gif|webp)$", "", name, flags=re.I)
            images[base_img.lower()] = name

        if any(x in lower for x in ["thumb", ".xml", ".json", ".txt", ".srt", ".vtt"]):
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
    return result, images

def find_logo(ident, fname, images, default_logo):
    """محاولة إيجاد أيقونة خاصة بالملف"""
    base = re.sub(r"(\.ia)?\.(mp4|mkv|webm|avi|mov|m4v|ts|flv|mp3|m4a|ogg|flac|wav|aac|opus)$", "", fname, flags=re.I)
    base_lower = base.lower()

    # 1. صورة بنفس اسم الملف
    if base_lower in images:
        return f"https://archive.org/download/{ident}/" + urllib.parse.quote(images[base_lower])

    # 2. صورة تحتوي على اسم الملف
    for img_base, img_name in images.items():
        if base_lower in img_base or img_base in base_lower:
            return f"https://archive.org/download/{ident}/" + urllib.parse.quote(img_name)

    # 3. العودة للأيقونة العامة
    return default_logo

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

        files, images = get_files(meta)
        if not files:
            print(f"    → no media files")
            continue

        files.sort(key=lambda x: x["name"])
        groups += 1
        print(f"    → {len(files)} files")

        default_logo = f"https://archive.org/services/img/{ident}"

        for f in files:
            fname = f["name"]
            ep = clean_name(fname)
            url = f"https://archive.org/download/{ident}/" + urllib.parse.quote(fname)
            logo = find_logo(ident, fname, images, default_logo)

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
