import aiohttp
import asyncio
from bs4 import BeautifulSoup

BASE_URL = "https://desu.city"

async def fetch(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
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

    # Заголовки
    title_en = soup.select_one("h1 .name")
    title_ru = soup.select_one("h1 .rus-name")
    title = title_ru.get_text(strip=True) if title_ru else (title_en.get_text(strip=True) if title_en else None)

    # Альтернативные названия
    alt_names = soup.select_one(".alternativeHeadline")
    alt_names = alt_names.get_text(strip=True) if alt_names else None

    # Описание
    description_tag = soup.select_one("#description .russian")
    description = description_tag.get_text(" ", strip=True) if description_tag else None

    # Автор
    author_tag = soup.select_one(".line .key:contains('Авторы:') + .value a")
    author = author_tag.get_text(strip=True) if author_tag else None

    # Жанры
    genres = [g.get_text(strip=True) for g in soup.select(".tagList li a")]

    # Год и статус
    year_status = soup.select_one(".line .key:contains('Статус:') + .value")
    year = None
    status = None
    if year_status:
        txt = year_status.get_text(" ", strip=True)
        status = "выходит" if "выходит" in txt else ("завершено" if "заверш" in txt else None)
        import re
        m = re.search(r"(\d{4})", txt)
        if m:
            year = m.group(1)

    # Список глав
    chapters = []
    for li in soup.select("ul.chlist li"):
        ch_link = li.select_one("h4 a")
        ch_date = li.select_one("span.date")
        if ch_link:
            chapters.append({
                "title": ch_link.get_text(strip=True),
                "url": ch_link["href"],
                "date": ch_date.get_text(strip=True) if ch_date else None
            })

    return {
        "title": title,
        "title_en": title_en.get_text(strip=True) if title_en else None,
        "title_ru": title_ru.get_text(strip=True) if title_ru else None,
        "alt_names": alt_names,
        "description": description,
        "author": author,
        "year": year,
        "status": status,
        "genres": genres,
        "chapters": chapters
    }

if __name__ == "__main__":
    slug = "manga/the-vampire-dies-in-no-time.2761/"
    info = asyncio.run(get_manga_info(slug))
    print("Манга:", info["title"])
    print("Жанры:", ", ".join(info["genres"]))
    print("Глав:", len(info["chapters"]))
    for ch in info["chapters"][:5]:
        print(ch)
