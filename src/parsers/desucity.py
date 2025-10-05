import re
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List
from .base_parser import BaseMangaParser



class DesuCityParser(BaseMangaParser):
    def __init__(self, base_url: str = "https://desu.city", headers: dict = None, timeout: int = 30):
        super().__init__(base_url, "desucity", headers, timeout)

    async def search_manga(self, query: str, max_pages: int = 1):
        """Поиск манги через AJAX запрос"""
        url = f"{self.base_url}/manga/search/"
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
            "User-Agent": self.headers.get("User-Agent"),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/manga/"
        }

        sess = await self._get_session()
        async with sess.post(url, data=payload, headers=headers) as resp:
            data = await resp.json(content_type=None)

        html = data.get("templateHtml", "")
        soup = BeautifulSoup(html, "html.parser")
        results = []

        for row in soup.select("tr"):
            header = row.select_one("th")
            if not header or "Манга" not in header.get_text():
                continue
            for li in row.select("ul.blockLinksList li"):
                a = li.find("a")
                if not a or not a.get("href", "").startswith("manga/"):
                    continue
                title = a.select_one(".itemTitle").get_text(strip=True)
                subtitle = a.select_one(".itemSubTitle")
                subtitle = subtitle.get_text(strip=True) if subtitle else None
                url = urljoin(self.base_url, a["href"])
                year = None
                for dt, dd in zip(li.select("dt"), li.select("dd")):
                    if "Год" in dt.get_text():
                        year = dd.get_text(strip=True)
                results.append({
                    "title": title,
                    "url": url,
                    "year": year,
                    "parser": self.name,
                    "subtitle": subtitle
                })
        return results

    async def get_manga_info(self, slug_or_url: str):
        """Получение информации о манге"""
        url = slug_or_url if slug_or_url.startswith("http") else f"{self.base_url}/{slug_or_url.lstrip('/')}"
        html = await self.fetch_text(url)
        soup = BeautifulSoup(html, "html.parser")

        title_ru = soup.select_one("h1 .rus-name")
        title_en = soup.select_one("h1 .name")
        title = title_ru.get_text(strip=True) if title_ru else (title_en.get_text(strip=True) if title_en else None)

        description_tag = soup.select_one("#description .russian")
        description = description_tag.get_text(" ", strip=True) if description_tag else None

        author_tag = soup.select_one(".line .key:contains('Авторы:') + .value a")
        author = author_tag.get_text(strip=True) if author_tag else None

        genres = [g.get_text(strip=True) for g in soup.select(".tagList li a")]

        chapters = []
        for li in soup.select("ul.chlist li"):
            ch_link = li.select_one("h4 a")
            ch_date = li.select_one("span.date")
            if not ch_link:
                continue
            chapters.append({
                "title": ch_link.get_text(strip=True),
                "url": urljoin(self.base_url, ch_link["href"]),
                "date": ch_date.get_text(strip=True) if ch_date else None
            })
        return {
            "title": title,
            "eng_name": title_en.get_text(strip=True) if title_en else None,
            "orig_name": title_ru.get_text(strip=True) if title_ru else None,
            "description": description,
            "author": author,
            "genres": genres,
            "chapters": chapters
        }



    async def get_chapter_images(self, chapter_url: str) -> List[str]:
        # скачиваем html стандартно (fetch_text уже в BaseMangaParser)
        html = await self.fetch_text(chapter_url)
        images = []

        # 1) Попробуем Reader.init
        m = re.search(r"Reader\.init\(\s*\{(.+?)\}\s*\);", html, re.S | re.I)
        if m:
            block = m.group(1)
            dir_match = re.search(r"dir\s*:\s*['\"]([^'\"]+)['\"]", block)
            if dir_match:
                base_dir = dir_match.group(1)
                if base_dir.startswith("//"):
                    base_dir = "https:" + base_dir
                items = re.findall(r'["\']([^"\']+\.(?:jpe?g|png|webp)(?:\?[^"\']*)?)["\']', block, flags=re.I)
                images = [urljoin(base_dir, img) for img in items]
                if images:
                    return images

        # 2) Попробуем старую стратегию (если reader.init не сработал)
        matches = re.findall(r"\['(https?://[^']+)','',\"([^\"]+)\"", html)
        for base, path in matches:
            full = urljoin(base, path)
            images.append(full.split("?")[0])

        if images:
            return images

        # 3) Fallback — взять все <img> в #preload или на странице (фильтруем по домену desu.city/img)
        soup = BeautifulSoup(html, "html.parser")
        for img in soup.select("#preload img, img"):
            src = img.get("src")
            if not src:
                continue
            # нормализуем
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = urljoin(self.base_url, src)
            images.append(src.split("?")[0])

        # Уберём дубликаты, сохранив порядок
        seen = set()
        uniq = []
        for u in images:
            if u not in seen:
                seen.add(u)
                uniq.append(u)
        return uniq

