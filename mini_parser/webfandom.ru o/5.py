#!/usr/bin/env python3
"""
webfandom_parser.py

Парсер картинок главы webfandom:
- пытается извлечь прямые URL из HTML (встраиваемые JSON / inlined data)
- если находит пути вида /media/catalog/manga_content/... — нормализует до https://webfandom.ru/...
- скачивает все найденные картинки в папку output/<slug>/

Требования:
- aiohttp
- beautifulsoup4
- (опционально) playwright (если используешь fallback)
"""

import asyncio
import aiohttp
import os
import re
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

START_URL = "https://webfandom.ru/reader/manga/manga-podnyatie-urovnya-v-odinochku-v2-c200_0?page=1"
BASE_HOST = "https://webfandom.ru"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

# regexp patterns to catch image URLs or paths embedded in JS/HTML
PATTERNS = [
    re.compile(r"https?://[^'\"\s>]+/media/catalog/manga_content/[^'\"\s>]+", re.IGNORECASE),
    re.compile(r"(/media/catalog/manga_content/[^'\"\s>]+)", re.IGNORECASE),
    # fallback generic media
    re.compile(r"https?://[^'\"\s>]+/media/[^'\"\s>]+", re.IGNORECASE),
    re.compile(r"(/media/[^'\"\s>]+)", re.IGNORECASE),
]

async def fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, headers=HEADERS) as resp:
        print(f"[DEBUG] GET {url} -> {resp.status}")
        resp.raise_for_status()
        return await resp.text()

def extract_from_soup(html: str) -> list:
    """
    Попытка аккуратно вытащить картинки:
    1) ищем явные <img> (src, data-src, data-name...)
    2) ищем вхождения в скриптах / inlined json с путями /media/...
    """
    soup = BeautifulSoup(html, "html.parser")
    found = []

    # 1) все теги <img>
    for img in soup.find_all("img"):
        for attr in ("src", "data-src", "data-original", "data-name"):
            val = img.get(attr)
            if val and isinstance(val, str):
                found.append(val.strip())

    # 2) содержимое inline script / text — regexp по PATTERNS
    text_for_search = []
    # include script tags and whole html as fallback
    for s in soup.find_all("script"):
        if s.string:
            text_for_search.append(s.string)
        else:
            # sometimes scripts are with children/view
            text_for_search.append(s.get_text(separator=" ", strip=True))
    # also include the whole HTML as last resort
    text_for_search.append(html)

    for block in text_for_search:
        for pat in PATTERNS:
            for m in pat.findall(block):
                # m may be tuple if groups, ensure string:
                if isinstance(m, tuple):
                    m = next((x for x in m if x), None)
                if m:
                    found.append(m.strip())

    # normalize and filter
    normalized = []
    for u in found:
        if u.startswith("//"):
            u = "https:" + u
        if u.startswith("/"):
            u = urljoin(BASE_HOST, u)
        # if relative like "../media/..." then join with base
        if not urlparse(u).scheme:
            u = urljoin(BASE_HOST, u)
        # keep only media/catalog or media/ paths (avoid icons etc.)
        if "/media/catalog/manga_content/" in u or "/media/catalog/" in u or "/media/" in u:
            normalized.append(u)

    # preserve order, unique
    final = []
    seen = set()
    for u in normalized:
        if u not in seen:
            seen.add(u)
            final.append(u)
    return final

async def download_images(session: aiohttp.ClientSession, urls: list, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    for idx, url in enumerate(urls, start=1):
        try:
            async with session.get(url, headers=HEADERS) as r:
                if r.status == 200:
                    data = await r.read()
                    # try keep extension from url
                    p = urlparse(url).path
                    ext = os.path.splitext(p)[1] or ".jpg"
                    filename = os.path.join(out_dir, f"{idx:03d}{ext}")
                    with open(filename, "wb") as f:
                        f.write(data)
                    print(f"[OK] Saved {filename}")
                else:
                    print(f"[ERR] {url} -> {r.status}")
        except Exception as e:
            print(f"[ERR] Download failed {url}: {e}")

async def main(start_url=START_URL):
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, start_url)

        # 1) try direct extraction from HTML (works if server included JSON with /media/...)
        imgs = extract_from_soup(html)
        print(f"[INFO] Found {len(imgs)} image URLs via HTML extraction.")

        # 2) If none found, attempt to find page-by-page (page=1,2,3...) using same extraction:
        if not imgs:
            print("[INFO] No images found in page=1 HTML. Trying auto-increment pages (?page=2,3... up to 50).")
            # try next pages until none found (safety cap)
            page = 2
            cap = 50
            while page <= cap:
                url = start_url.split("?page=")[0] + f"?page={page}"
                try:
                    html2 = await fetch_html(session, url)
                except Exception as e:
                    print(f"[WARN] Failed to fetch {url}: {e}")
                    break
                new = extract_from_soup(html2)
                # append new images
                for u in new:
                    if u not in imgs:
                        imgs.append(u)
                if not new:
                    # stop when no images on this page
                    break
                print(f"[DEBUG] page {page} -> found {len(new)}")
                page += 1

        # 3) If still none, print hint and (optionally) fallback to Playwright
        if not imgs:
            print("[ERROR] Не найдено картинок в HTML. Сайт, вероятно, подгружает картинки только в браузере (JS).")
            print("Варианты:")
            print("1) запустить Playwright / Selenium (автоматически рендерит JS).")
            print("2) в DevTools -> Network -> XHR найти API-эндпоинт и использовать его напрямую (предпочтительно).")
            # (опционально) can integrate playwright here if user wants
            return

        # print found urls
        for i, u in enumerate(imgs, 1):
            print(f"{i:03d}: {u}")

        # prepare output dir: try to extract slug from URL path
        parsed = urlparse(start_url)
        slug = os.path.basename(parsed.path) or "chapter"
        out_dir = os.path.join("output", slug)
        await download_images(session, imgs, out_dir)
        print(f"[DONE] downloaded {len(imgs)} images to {out_dir}")

if __name__ == "__main__":
    # Allow passing URL via CLI
    url = sys.argv[1] if len(sys.argv) > 1 else START_URL
    asyncio.run(main(url))
