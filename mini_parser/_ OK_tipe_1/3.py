import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import quote
from rapidfuzz import fuzz

BASE_URL = "https://3.readmanga.ru/search/advancedResults"

async def fetch_html(url: str, params: dict) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Referer": "https://3.readmanga.ru/search",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as resp:
            print(f"[DEBUG] GET {resp.url} -> {resp.status}")
            return await resp.text()

def parse_manga_tile(tile, query=""):
    title_el = tile.select_one(".desc h3 a")
    url = "https://3.readmanga.ru" + title_el["href"] if title_el else None
    title = title_el.get_text(strip=True) if title_el else None

    rating_el = tile.select_one(".compact-rate")
    rating = float(rating_el["title"]) if rating_el and rating_el.has_attr("title") else None

    genres = [g.get_text(strip=True) for g in tile.select(".tile-info a[href*='/list/genre/']")]
    year_el = tile.select_one(".tile-info a[href*='/list/year/']")
    year = year_el.get_text(strip=True) if year_el else None

    score = fuzz.partial_ratio(query.lower(), title.lower()) if title and query else 0

    return {
        "title": title,
        "url": url,
        "rating": rating,
        "genres": genres,
        "year": year,
        "similarity": score
    }

async def search_manga(query: str, years=(1961, 2025), sort="POPULARITY", max_pages=2):
    results = []
    offset = 0

    for _ in range(max_pages):
        params = {
            "q": query,
            "offset": offset,
            "years": f"{years[0]},{years[1]}",
            "sortType": sort
        }
        html = await fetch_html(BASE_URL, params)
        soup = BeautifulSoup(html, "html.parser")

        tiles = soup.select(".tiles .tile")
        if not tiles:
            break

        parsed = [parse_manga_tile(tile, query) for tile in tiles]
        results.extend(parsed)

        offset += len(tiles)

    # сортировка по совпадению и рейтингу
    results.sort(key=lambda x: (x["similarity"], x["rating"] or 0), reverse=True)
    return results

if __name__ == "__main__":
    query = "пис"
    results = asyncio.run(search_manga(query, max_pages=2))
    print(f"Найдено: {len(results)}")
    for r in results[:10]:
        print(f"{r['title']} ({r['year']}) ⭐ {r['rating']} [{r['similarity']}%] -> {r['url']}")
