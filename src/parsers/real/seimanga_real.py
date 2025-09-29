import re
import os
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict
from parsers.base_parser import BaseParser





class SeiMangaParser(BaseParser):
    BASE_URL = "https://1.seimanga.me"

    async def _fetch_html(self, url: str) -> str:
        headers = {"User-Agent": "Mozilla/5.0"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                return await resp.text()

    # 🔎 Поиск манги
    async def search(self, query: str) -> List[Dict]:
        """
        Ищет мангу по названию.
        Возвращает список [{title, url}].
        """
        search_url = f"{self.BASE_URL}/list?title={query}"
        html = await self._fetch_html(search_url)
        soup = BeautifulSoup(html, "html.parser")

        results = []
        for item in soup.select("div.item"):
            link = item.select_one("a.cover")
            title = item.select_one("div.title")
            if link and title:
                results.append({
                    "title": title.get_text(strip=True),
                    "url": self.BASE_URL + link["href"]
                })
        return results

    # 📘 Инфо о манге
    async def get_manga_info(self, url: str) -> Dict:
        """
        Возвращает инфо о манге + список глав.
        """
        html = await self._fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")

        title = soup.select_one("h1.names").get_text(strip=True)
        author = soup.select_one("span.author a")
        description = soup.select_one("div.description")

        chapters = []
        for row in soup.select("tr.item-row"):
            ch_link = row.select_one("a.chapter-link")
            ch_date = row.select_one("td.date")
            if ch_link:
                chapters.append({
                    "title": ch_link.get_text(strip=True),
                    "url": self.BASE_URL + ch_link["href"],
                    "date": ch_date.get_text(strip=True) if ch_date else None
                })

        return {
            "title": title,
            "author": author.get_text(strip=True) if author else None,
            "genres": [g.get_text(strip=True) for g in soup.select("span.genre")],
            "description": description.get_text(strip=True) if description else "",
            "chapters": chapters
        }

    # 📄 Список глав
    async def get_chapters(self, manga_url: str) -> List[Dict]:
        info = await self.get_manga_info(manga_url)
        return info["chapters"]

    # 🖼️ Страницы главы
    async def get_chapter_pages(self, chapter_url: str) -> List[str]:
        """
        Парсит rm_h.readerInit(...) и достаёт ссылки на картинки.
        """
        html = await self._fetch_html(chapter_url)
        matches = re.findall(r"\['(https://[^']+)','',\"([^\"]+)\"", html)

        image_urls = []
        for base, path in matches:
            full_url = base + path
            clean_url = full_url.split("?")[0]  # убираем query string
            image_urls.append(clean_url)

        return image_urls

    # 💾 Скачать главу
    async def download_chapter(self, chapter_url: str, out_dir: str) -> List[str]:
        os.makedirs(out_dir, exist_ok=True)
        image_urls = await self.get_chapter_pages(chapter_url)
        saved_files = []

        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(image_urls, 1):
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        ext = os.path.splitext(url)[1] or ".jpg"
                        filename = os.path.join(out_dir, f"{i}{ext}")
                        with open(filename, "wb") as f:
                            f.write(data)
                        saved_files.append(filename)
        return saved_files
