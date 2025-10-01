import re
import aiohttp
import asyncio
import os

CHAPTER_URL = "https://1.mintmanga.com/21230/vol1/30?mtr=true"


async def fetch(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Referer": "https://readmanga.me/",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            print(f"[DEBUG] GET {url} -> {resp.status}")
            return await resp.text()


async def get_chapter_images(chapter_url: str):
    html = await fetch(chapter_url)

    # ищем вызов rm_h.readerInit(...) и достаём все пути картинок
    matches = re.findall(r"\['(https://[^']+)','',\"([^\"]+)\"", html)

    image_urls = []
    for base, path in matches:
        full_url = base + path
        # обрезаем всё от знака "?"
        clean_url = full_url.split("?")[0]
        image_urls.append(clean_url)

    return image_urls

async def download_images(urls, out_dir="images"):
    os.makedirs(out_dir, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(urls, 1):
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    ext = os.path.splitext(url)[1] or ".jpg"
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
