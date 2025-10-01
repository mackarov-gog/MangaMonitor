import aiohttp
import asyncio
from bs4 import BeautifulSoup

BASE_URL = "https://3.readmanga.ru"

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

async def parse_manga_tile(tile) -> dict:
    link_tag = tile.select_one("h3 a")
    url = BASE_URL + link_tag["href"] if link_tag else None
    title = link_tag.get_text(strip=True) if link_tag else None

    orig_name_tag = tile.select_one(".long-description h5")
    orig_name = orig_name_tag.get_text(strip=True) if orig_name_tag else None

    rating_tag = tile.select_one(".compact-rate")
    rating = float(rating_tag["title"]) if rating_tag else None

    genres = [g.get_text(strip=True) for g in tile.select(".elem_genre")]
    tags = [t.get_text(strip=True) for t in tile.select(".elem_tag")]

    desc_tag = tile.select_one(".manga-description")
    description = desc_tag.get_text(strip=True) if desc_tag else None

    return {
        "title": title,
        "orig_name": orig_name,
        "url": url,
        "rating": rating,
        "genres": genres,
        "tags": tags,
        "description": description
    }

async def get_manga_page(page: int):
    url = f"{BASE_URL}/list?page={page}"
    html = await fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    tiles = soup.select(".tiles .tile")
    if not tiles:  # если на странице нет манги, прекращаем
        return None
    tasks = [parse_manga_tile(tile) for tile in tiles]
    return await asyncio.gather(*tasks)

async def get_all_manga():
    page = 1
    all_manga = []
    while True:
        manga_page = await get_manga_page(page)
        if not manga_page:
            break
        all_manga.extend(manga_page)
        print(f"[INFO] Parsed page {page}, total mangas: {len(all_manga)}")
        page += 1
    return all_manga

async def main():
    manga_list = await get_all_manga()
    print(f"Всего манг спарсено: {len(manga_list)}")
    for manga in manga_list[:10]:  # пример: показываем только первые 10
        print(manga)

if __name__ == "__main__":
    asyncio.run(main())
