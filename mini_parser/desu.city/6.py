import aiohttp
import asyncio
import os
import re

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


def parse_from_reader_js(html):
    # Находим блок Reader.init
    m = re.search(r"Reader\.init\(\{(.+?)\}\);", html, re.S)
    if not m:
        return []
    block = m.group(1)

    # Директория с картинками
    dir_match = re.search(r'dir:\s*"([^"]+)"', block)
    if not dir_match:
        return []
    base_dir = dir_match.group(1)
    if base_dir.startswith("//"):
        base_dir = "https:" + base_dir

    # Все картинки из images: [...]
    # Теперь берём ВСЕ webp внутри
    items = re.findall(r'"([^"]+\.webp\?[^"]*)"', block)
    urls = [f"{base_dir}{img}" for img in items]

    return urls


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
        html = await fetch_html(session, chapter_url)
        imgs = parse_from_reader_js(html)
        print(f"Total images found: {len(imgs)}")
        for img in imgs:
            print(img)
        if imgs:
            await download_images(imgs, outdir="downloads/ch49")


if __name__ == "__main__":
    asyncio.run(main())
