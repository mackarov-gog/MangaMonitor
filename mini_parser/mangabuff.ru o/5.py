import aiohttp
import asyncio
import os
from bs4 import BeautifulSoup

CHAPTER_URL = "https://mangabuff.ru/manga/slezy-na-uvyadshih-cvetah/1/71"

async def fetch(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            print(f"[DEBUG] GET {url} -> {resp.status}")
            return await resp.text()

async def get_chapter_images(chapter_url: str):
    html = await fetch(chapter_url)
    soup = BeautifulSoup(html, "html.parser")

    images = []
    # ищем все картинки внутри блока с мангой
    for img in soup.select("div.reader__pages img"):
        url = img.get("src") or img.get("data-src")
        if url:
            images.append(url)
    return images

async def download_images(urls, out_dir="images"):
    os.makedirs(out_dir, exist_ok=True)
    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(urls, 1):
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    ext = os.path.splitext(url.split("?")[0])[1] or ".jpg"
                    filename = os.path.join(out_dir, f"{i}{ext}")
                    with open(filename, "wb") as f:
                        f.write(data)
                    print(f"[OK] Saved {filename}")
                else:
                    print(f"[ERR] {url} -> {resp.status}")

async def main():
    images = await get_chapter_images(CHAPTER_URL)
    print("Found images:", images)
    await download_images(images)

if __name__ == "__main__":
    asyncio.run(main())
