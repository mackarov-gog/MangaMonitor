import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import quote

BASE_URL = "https://1.seimanga.me"

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


def parse_manga_tile(tile):
    title_el = tile.select_one(".desc h3 a")
    url = BASE_URL + title_el["href"] if title_el else None
    title = title_el.get_text(strip=True) if title_el else None

    rating_el = tile.select_one(".compact-rate")
    rating = float(rating_el["title"]) if rating_el else None

    genres = [g.get_text(strip=True) for g in tile.select(".tile-info a[href*='/list/genre/']")]
    description_el = tile.select_one(".manga-description")
    description = description_el.get_text(strip=True) if description_el else None

    return {
        "title": title,
        "url": url,
        "rating": rating,
        "genres": genres,
        "description": description
    }

async def get_manga(name: str = ""):
    """Если name пустой, берёт только первую страницу каталога.
       Если name указан, ищет по всем страницам поиска."""
    offset = 0
    all_results = []

    while True:
        if name:
            name_encoded = quote(name)
            url = f"{BASE_URL}/list?search={name_encoded}&offset={offset}"
        else:
            url = f"{BASE_URL}/list?offset=0"  # только первая страница
        html = await fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        tiles = soup.select(".tiles .tile")
        if not tiles:
            break

        results = [parse_manga_tile(tile) for tile in tiles]

        # фильтруем по названию, если есть поисковый запрос
        if name:
            results = [r for r in results if name.lower() in r["title"].lower()]

        all_results.extend(results)
        print(f"[INFO] Fetched {len(results)} results, total: {len(all_results)}")

        if not name:  # если нет поиска, берём только первую страницу
            break

        offset += len(tiles)

    return all_results

if __name__ == "__main__":
    search_query = "Мстители"  # или "" для первой страницы
    results = asyncio.run(get_manga(search_query))
    print(f"Всего найдено: {len(results)}")
    for r in results:
        print(r)
