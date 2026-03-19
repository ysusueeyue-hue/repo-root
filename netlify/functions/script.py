import requests
import re
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse

def is_xhamster(url):
    domain = urlparse(url).netloc.lower()
    return "xhamster" in domain

# =====================================
# 🔥 MAIN FUNCTION
# =====================================
def extract_video_links(url):

    if is_xhamster(url):
        return extract_xhamster(url)
    else:
        return extract_other(url)

# =====================================
# 🔥 THUMBNAIL EXTRACTOR (COMMON)
# =====================================
def extract_thumbnail(html):
    thumb = None

    match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    if match:
        thumb = match.group(1)

    if not thumb:
        match = re.search(r'<meta name="twitter:image" content="([^"]+)"', html)
        if match:
            thumb = match.group(1)

    return thumb

# =====================================
# 🔥 XHAMSTER (UNCHANGED + THUMB)
# =====================================
def extract_xhamster(url):

    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://xhamster.com/"
    }

    try:
        print("[+] Fetching xHamster...")

        for i in range(3):
            try:
                r = session.get(url, headers=headers, timeout=20)
                html = r.text
                break
            except:
                time.sleep(2)
        else:
            print("❌ Failed")
            return

        thumb = extract_thumbnail(html)
        if thumb:
            print("\n🖼️ THUMBNAIL:\n")
            print(thumb)

        links = set()

        links.update(re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html))

        json_links = re.findall(r'"url":"(https:[^"]+)"', html)
        for link in json_links:
            link = link.replace("\\/", "/")
            if ".m3u8" in link:
                links.add(link)

        if not links:
            mp4_links = re.findall(r'https?://[^\s"\']+\.mp4[^\s"\']*', html)
            mp4_links = list(set(mp4_links))

            if mp4_links:
                print("\n🎯 MP4 LINK:\n")
                print(mp4_links[0])
                return

        if not links:
            print("❌ No link")
            return

        link = list(links)[0]

        m3u8_data = session.get(link, headers=headers, timeout=20).text
        base = link.split("/key=")[0]

        qualities = ["144p", "240p", "480p", "720p", "1080p", "2160p"]

        found = {}

        for q in qualities:
            match = re.search(rf'(/key=.*{q}.*\.m3u8)', m3u8_data)
            if match:
                full_link = base + match.group(1)
                found[q] = full_link

        if not found:
            print("❌ No quality found")
            return

        if "720p" in found:
            final_link = found["720p"]
        elif "480p" in found:
            final_link = found["480p"]
        elif "240p" in found:
            final_link = found["240p"]
        elif "144p" in found:
            final_link = found["144p"]
        else:
            final_link = list(found.values())[0]

        print("\n🎯 FINAL LINK:\n")
        print(final_link)

    except Exception as e:
        print("❌ Error:", str(e))


# =====================================
# 🔥 OTHER DOMAIN (UNCHANGED + THUMB)
# =====================================
def extract_other(url):

    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://xhamster.com/"
    }

    try:
        print("[+] Fetching Other Site...")

        for _ in range(3):
            try:
                r = session.get(url, headers=headers, timeout=20)
                html = r.text
                break
            except:
                time.sleep(2)
        else:
            print("❌ Failed")
            return

        thumb = extract_thumbnail(html)
        if thumb:
            print("\n🖼️ THUMBNAIL:\n")
            print(thumb)

        mp4_links = re.findall(r'https?://[^\s"\']+\.mp4[^\s"\']*', html)
        mp4_links = list(set(mp4_links))

        if mp4_links:
            def get_quality(link):
                match = re.search(r'(\d{3,4})p', link)
                return int(match.group(1)) if match else 0

            mp4_links.sort(key=get_quality, reverse=True)

            print("\n🎯 MP4 LINK:\n")
            print(mp4_links[0])
            return

        links = set()

        links.update(re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html))

        json_links = re.findall(r'"url":"(https:[^"]+)"', html)
        for link in json_links:
            link = link.replace("\\/", "/")
            if ".m3u8" in link:
                links.add(link)

        if not links:
            print("❌ No video link found!")
            return

        link = list(links)[0]

        if "multi=" in link:
            qualities = re.findall(r'(\d{3,4})p', link)
            qualities = sorted(set(qualities), key=lambda x: int(x), reverse=True)

            if qualities:
                max_q = int(qualities[0])
                target = min(max_q, 720)

                for q in qualities:
                    if int(q) <= target:
                        final_link = link.replace("_TPL_", f"{q}p")

                        print("\n🎯 M3U8 LINK:\n")
                        print(final_link)
                        return

        if "_TPL_" in link:
            for q in ["720p", "480p", "360p", "240p", "144p"]:
                test_link = link.replace("_TPL_", q)
                test = session.get(test_link, headers=headers)

                if test.status_code == 200:
                    print("\n🎯 M3U8 LINK:\n")
                    print(test_link)
                    return

        print("\n🎯 RAW LINK:\n")
        print(link)

    except:
        print("❌ Error")


# =====================================
# 🚀 NETLIFY OUTPUT WRAPPER (ONLY ADD)
# =====================================
if __name__ == "__main__":
    import sys
    import json
    import io
    import contextlib

    url = sys.argv[1]

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        extract_video_links(url)

    output = f.getvalue()

    thumb = None
    video = None

    thumb_match = re.search(r'(https?://[^\s]+\.jpg)', output)
    if thumb_match:
        thumb = thumb_match.group(1)

    video_match = re.search(r'(https?://[^\s]+(\.m3u8|\.mp4)[^\s]*)', output)
    if video_match:
        video = video_match.group(1)

    print(json.dumps({
        "thumbnail": thumb,
        "video": video,
        "raw": output
    }))
