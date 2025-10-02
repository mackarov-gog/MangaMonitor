import os
import requests

URL = "https://mangalib.me/ru/1773--wind-breaker/read/v5/c115"
OUTPUT_DIR = "mangalib_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://mangalib.me/"
}

def get_slug_vol_num(url: str):
    parts = url.split("/")
    slug = parts[4]  # "1773--wind-breaker"
    volume, number = None, None
    for p in parts:
        if p.startswith("v") and p[1:].isdigit():
            volume = p[1:]
        if p.startswith("c") and p[1:].isdigit():
            number = p[1:]
    return slug, volume, number

def fetch_pages(slug: str, volume: str, number: str):
    api_url = f"https://api.cdnlibs.org/api/manga/{slug}/chapter?number={number}&volume={volume}"
    r = requests.get(api_url, headers=HEADERS)
    r.raise_for_status()
    data = r.json()

    pages = []
    if "data" in data and "pages" in data["data"]:
        for p in data["data"]["pages"]:
            url = p.get("url")
            if url:
                if url.startswith("//manga/"):
                    url = "https://img3.mixlib.me" + url[1:]  # убрать одну косую
                elif url.startswith("/"):
                    url = "https://img3.mixlib.me" + url
                elif url.startswith("//"):
                    url = "https:" + url
                pages.append(url)
    return pages


def download(url, path):
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)

def main():
    slug, volume, number = get_slug_vol_num(URL)
    print(f"[INFO] slug={slug}, том={volume}, глава={number}")

    pages = fetch_pages(slug, volume, number)
    print(f"[INFO] Найдено {len(pages)} страниц")

    for i, link in enumerate(pages, 1):
        ext = os.path.splitext(link.split("?")[0])[-1] or ".jpg"
        filename = os.path.join(OUTPUT_DIR, f"{number}_{i:03}{ext}")
        print(f"[DL] {i}: {link}")
        download(link, filename)

    print("[DONE] Скачано в:", OUTPUT_DIR)

if __name__ == "__main__":
    main()
