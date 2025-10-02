import os
import requests
from urllib.parse import urlparse
from PIL import Image
from io import BytesIO

CHAPTER_URL = "https://remanga.org/manga/who-do-you-like-with-that-face/1861366"
SAVE_DIR = "remanga_output"
os.makedirs(SAVE_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_chapter_id(url: str) -> str:
    path = urlparse(url).path.strip("/")
    return path.split("/")[-1]

def fetch_chapter_images(chapter_id: str):
    api_url = f"https://api.remanga.org/api/titles/chapters/{chapter_id}/"
    r = requests.get(api_url, headers=HEADERS)
    r.raise_for_status()
    data = r.json()

    content = data.get("content", {})
    pages_nested = content.get("pages", [])

    links = []
    for group in pages_nested:          # pages — это список списков
        for p in group:                 # каждый p — это словарь
            img = p.get("link")
            if img:
                links.append(img)
    return links

def download_and_save(url: str, path: str):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://remanga.org/",   # добавляем реферер
    }
    r = requests.get(url, headers=headers)
    r.raise_for_status()

    img = Image.open(BytesIO(r.content)).convert("RGB")
    img.save(path, "JPEG", quality=95)


if __name__ == "__main__":
    chapter_id = get_chapter_id(CHAPTER_URL)
    print("[INFO] Chapter ID:", chapter_id)

    images = fetch_chapter_images(chapter_id)
    print(f"[INFO] Найдено {len(images)} страниц")

    for i, url in enumerate(images, 1):
        filename = os.path.join(SAVE_DIR, f"{i:03}.jpg")
        print(f"[DOWNLOAD] {i}: {url}")
        download_and_save(url, filename)

    print("[DONE] Все картинки сохранены в папку:", SAVE_DIR)
