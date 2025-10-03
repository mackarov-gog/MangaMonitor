# src/app/chapter_parser.py
import re
import aiohttp
import asyncio
import os

async def fetch(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            return await resp.text()

async def get_chapter_images(chapter_url: str):
    html = await fetch(chapter_url)
    matches = re.findall(r"\['(https://[^']+)','',\"([^\"]+)\"", html)

    image_urls = []
    for base, path in matches:
        full_url = base + path
        clean_url = full_url.split("?")[0]  # убираем query string
        image_urls.append(clean_url)

    return image_urls

async def download_chapter(chapter_url: str, out_dir="images"):
    images = await get_chapter_images(chapter_url)
    os.makedirs(out_dir, exist_ok=True)
    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(images, 1):
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    ext = os.path.splitext(url)[1] or ".jpg"
                    filename = os.path.join(out_dir, f"{i}{ext}")
                    with open(filename, "wb") as f:
                        f.write(data)
                    print(f"[OK] Saved {filename}")
    return images