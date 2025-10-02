import aiohttp
import asyncio
import os
import re
from bs4 import BeautifulSoup

BASE_URL = "https://desu.city"
IMG_HOST = "https://img2.desu.city"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0 Safari/537.36"
}

async def fetch_html(session, url):
    async with session.get(url, headers=HEADERS) as r:
        r.raise_for_status()
        return await r.text()

async def fetch_bytes(session, url):
    async with session.get(url, headers=HEADERS) as r:
        r.raise_for_status()
        return await r.read()

def parse_from_preload(soup):
    preload_div = soup.find("div", {"id": "preload"})
    if not preload_div:
        return []
    imgs = []
    for img in preload_div.find_all("img"):
        src = img.get("src")
        if src:
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = IMG_HOST + src
            imgs.append(src)
    return imgs

def parse_from_reader_js(html):
    """
    Парсим кусок Reader.init({...})
    """
    m = re.search(r"Reader\.init\(\{(.+?)\}\);", html, re.S)
    if not m:
        return []
    block = m.group(1)

    # ищем dir
    dir_match = re.search(r'dir:\s*"([^"]+)"', block)
    if not dir_match:
        return []
    base_dir = dir_match.group(1)
    if base_dir.startswith("//"):
        base_dir = "https:" + base_dir

    # ищем список картинок
    images_block = re.search(r'images:\s*\[(.+?)\]', block, re.S)
    if not images_block:
        return []

    items = re.findall(r'"([^"]+\.webp\?[^"]*)"', images_block.group(1))
    return [f"{base_dir}{img}" for img in items]

async def parse_images(session, chapter_url):
    html = await fetch_html(session, chapter_url)
    soup = BeautifulSoup(html, "html.parser")

    imgs = parse_from_preload(soup)
    if not imgs:
        imgs = parse_from_reader_js(html)

    print(f"Found {len(imgs)} images")
    for i in imgs:
        print(i)
    return imgs

async def download_images(urls, outdir="downloads"):
    os.makedirs(outdir, exist_ok=True)
    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(urls, 1):
            try:
                data = await fetch_bytes(session, url)
                filename = os.path.join(outdir, f"{i:03d}.webp")
                with open(filename, "wb") as f:
                    f.write(data)
                print(f"[OK] {filename}")
            except Exception as e:
                print(f"[FAIL] {url} -> {e}")

async def main():
    chapter_url = "https://desu.city/manga/bad-born-blood.6732/vol1/ch49/rus"
    async with aiohttp.ClientSession() as session:
        imgs = await parse_images(session, chapter_url)
        if imgs:
            await download_images(imgs)

if __name__ == "__main__":
    asyncio.run(main())
