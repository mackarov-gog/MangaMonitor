import aiohttp
import asyncio
from bs4 import BeautifulSoup


BASE_URL = "https://a.zazaza.me"

async def fetch(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            print(f"[DEBUG] GET {url} -> {resp.status}")
            return await resp.text()

async def parse_manga_tile(tile) -> dict:
    # Ссылка и названия
    link_tag = tile.select_one("h3 a")
    url = BASE_URL + link_tag["href"] if link_tag else None
    title = link_tag.get_text(strip=True) if link_tag else None

    # Оригинальное название в <h5> внутри .long-description
    orig_name_tag = tile.select_one(".long-description h5")
    orig_name = orig_name_tag.get_text(strip=True) if orig_name_tag else None

    # Рейтинг
    rating_tag = tile.select_one(".compact-rate")
    rating = float(rating_tag["title"]) if rating_tag else None

    # Жанры
    genres = [g.get_text(strip=True) for g in tile.select(".elem_genre")]

    # Теги
    tags = [t.get_text(strip=True) for t in tile.select(".elem_tag")]

    # Описание
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

async def get_manga_list(page: int = 1):
    url = f"{BASE_URL}/list?page={page}"
    html = await fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    manga_tiles = soup.select(".tiles .tile")
    tasks = [parse_manga_tile(tile) for tile in manga_tiles]
    return await asyncio.gather(*tasks)

async def main():
    manga_list = await get_manga_list(page=1)
    for manga in manga_list:
        print(manga)

if __name__ == "__main__":
    asyncio.run(main())
