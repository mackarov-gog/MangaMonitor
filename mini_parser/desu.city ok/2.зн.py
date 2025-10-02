import aiohttp
import asyncio
from bs4 import BeautifulSoup

async def search_desu(query: str):
    url = "https://desu.city/manga/search/"
    payload = {
        "q": query,
        "type": "manga",
        "title_only": "0",
        "nodes[]": "0",
        "order": "date",
        "group_discussion": "0",
        "users": "",
        "child_nodes": "1",
        "date": "0",
        "_xfRequestUri": "/manga/",
        "_xfNoRedirect": "1",
        "_xfToken": "",
        "_xfResponseType": "json"
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://desu.city",
        "Referer": "https://desu.city/manga/"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers) as resp:
            data = await resp.json(content_type=None)

    # достаём HTML из templateHtml
    html = data.get("templateHtml", "")
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # ищем только блок "Манга"
    for row in soup.select("tr"):
        header = row.select_one("th")
        if not header or "Манга" not in header.get_text():
            continue  # пропускаем аниме

        for li in row.select("ul.blockLinksList li"):
            a = li.find("a")
            if not a:
                continue

            href = a["href"]
            if not href.startswith("manga/"):  # фильтруем только мангу
                continue

            url = "https://desu.city/" + href.lstrip("/")
            title = a.select_one(".itemTitle").get_text(strip=True)
            subtitle = a.select_one(".itemSubTitle")
            subtitle = subtitle.get_text(strip=True) if subtitle else None

            year = None
            for dt, dd in zip(li.select("dt"), li.select("dd")):
                if "Год" in dt.get_text():
                    year = dd.get_text(strip=True)

            results.append({
                "title": title,
                "subtitle": subtitle,
                "url": url,
                "year": year
            })

    return results


async def main():
    res = await search_desu("наруто")
    for r in res:
        print(f"{r['title']} ({r['year']}) -> {r['url']} [{r['subtitle']}]")

asyncio.run(main())
