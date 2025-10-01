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

async def get_manga_info(slug: str):
    url = f"{BASE_URL}/{slug}"
    html = await fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    # Основная информация
    title = soup.select_one("h1.names > span.name").get_text(strip=True)
    eng_name_tag = soup.select_one("h1.names > .eng-name")
    eng_name = eng_name_tag.get_text(strip=True) if eng_name_tag else None
    orig_name_tag = soup.select_one("h1.names > .original-name")
    orig_name = orig_name_tag.get_text(strip=True) if orig_name_tag else None
    description_tag = soup.select_one('meta[itemprop="description"]')
    description = description_tag["content"] if description_tag else None

    # Автор
    author_tag = soup.select_one(".elem_author a.person-link")
    author = author_tag.get_text(strip=True) if author_tag else None

    # Год, Жанры, Категория
    year_tag = soup.select_one(".elem_year a")
    year = year_tag.get_text(strip=True) if year_tag else None
    genres = [g.get_text(strip=True) for g in soup.select(".elem_genre")]
    category_tag = soup.select_one(".elem_category a")
    category = category_tag.get_text(strip=True) if category_tag else None

    # Рейтинг
    rating_tag = soup.select_one("#user_rate_166600 input[name='score']")
    rating = float(rating_tag["value"]) if rating_tag else None

    # Список глав
    chapters = []
    for row in soup.select("tr.item-row"):
        ch_link = row.select_one("a.chapter-link")
        ch_date = row.select_one("td.date")
        if not ch_link:
            continue
        chapters.append({
            "title": ch_link.get_text(strip=True),
            "url": BASE_URL + ch_link["href"],
            "date": ch_date.get_text(strip=True) if ch_date else None
        })

    return {
        "title": title,
        "eng_name": eng_name,
        "orig_name": orig_name,
        "description": description,
        "author": author,
        "year": year,
        "category": category,
        "genres": genres,
        "rating": rating,
        "chapters": chapters
    }

if __name__ == "__main__":
    slug = "gatiakuta"
    info = asyncio.run(get_manga_info(slug))
    print("Манга:", info["title"])
    print("Жанры:", ", ".join(info["genres"]))
    print("Глав:", len(info["chapters"]))
    for ch in info["chapters"]:
        print(ch)
