#!/usr/bin/env python3
"""Build full M3U playlist from Archive.org - keep only highest quality version."""

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

    # خصم كبير للجودات المنخفضة
    if any(x in name for x in ["512kb", "256kb", "128kb", "64kb", "low", "small"]):
        score -= 10_000_000_000
    if name.endswith(".ia.mp4"):
        score -= 5_000_000_000

    # تفضيل الملفات الأصلية
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
