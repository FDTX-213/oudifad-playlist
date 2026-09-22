#!/usr/bin/env python3
"""Build full M3U playlist from Archive.org account."""

import json
import re
import urllib.parse
import urllib.request
import time

UPLOADER = "ouadoudifouad334@gmail.com"
OUTPUT = "playlist.m3u"

def clean_name(filename):
    name = filename.rsplit(".mp4", 1)[0] if filename.lower().endswith(".mp4") else filename
    name = re.sub(r"^\d+[\.\-]?\s*", "", name)
    name = re.sub(r"^HE-\d+-", "", name)
    name = re.sub(r"^\d{5,}-", "", name)
    name = re.sub(r"\s*\d{3,4}p\b", "", name, flags=re.I)
    name = re.sub(r"\s*WEB-?DL\b", "", name, flags=re.I)
    name = re.sub(r"\s*\(\d+\)\s*$", "", name)
    name = re.sub(r"\s+\d{4}\s*$", "", name)
    name = re.sub(r"\s+\d+$", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"[_\-\s]+$", "", name)
    return name or filename

def main():
    print("Fetching items list...")
    search_url = (
        "https://archive.org/advancedsearch.php?"
        + urllib.parse.urlencode({
            "q": f'uploader:"{UPLOADER}"',
            "fl[]": ["identifier", "title", "mediatype"],
            "rows": 200,
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
        print(f"  Processing: {title[:50]}...")

        try:
            meta_url = f"https://archive.org/metadata/{ident}"
            with urllib.request.urlopen(meta_url, timeout=30) as r:
                meta = json.load(r)
        except Exception as e:
            print(f"    SKIP: {e}")
            continue

        files = [
            f for f in meta.get("files", [])
            if f.get("name", "").lower().endswith(".mp4")
            and not f["name"].endswith(".ia.mp4")
            and f.get("source") in ("original", None)
        ]

        if not files:
            continue

        files.sort(key=lambda x: x["name"])
        groups += 1

        for f in files:
            fname = f["name"]
            ep = clean_name(fname)
            logo = (
                f"https://archive.org/download/{ident}/{ident}.thumbs/"
                + urllib.parse.quote(fname.rsplit(".mp4", 1)[0] + "_000001.jpg")
            )
            url = f"https://archive.org/download/{ident}/" + urllib.parse.quote(fname)

            lines.append(
                f'#EXTINF:-1 tvg-name="{ep}" tvg-logo="{logo}" group-title="{title}",{ep}'
            )
            lines.append(url)
            total += 1

        time.sleep(0.2)

    content = "\n".join(lines) + "\n"
    with open(OUTPUT, "w", encoding="utf-8") as out:
        out.write(content)

    print(f"\nDone: {groups} groups, {total} videos → {OUTPUT}")

if __name__ == "__main__":
    main()
