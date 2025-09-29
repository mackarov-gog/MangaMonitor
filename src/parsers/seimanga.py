# src/parsers/seimanga.py
from __future__ import annotations
import os
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode

import aiohttp
from bs4 import BeautifulSoup

BASE_URL = "https://1.seimanga.me"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}


class SeiMangaParser:
    name = "seimanga"

    def __init__(self, base_url: str = BASE_URL, headers: Optional[dict] = None, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.headers = headers or DEFAULT_HEADERS
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    # context manager
    async def __aenter__(self):
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self) -> None:
        try:
            if self._session and not self._session.closed:
                await self._session.close()
        except Exception:
            pass
        finally:
            self._session = None

    # session helper
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self.headers, timeout=self.timeout)
        return self._session

    # ensure mtr param
    @staticmethod
    def ensure_mtr(url: str) -> str:
        parsed = urlparse(url)
        qs = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if qs.get("mtr") == "true":
            return url
        qs["mtr"] = "true"
        new_query = urlencode(qs, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)

    # fetch text
    async def fetch_text(self, url: str) -> str:
        sess = await self._get_session()
        async with sess.get(url) as resp:
            text = await resp.text()
            # краткий лог
            print(f"[seimanga] GET {url} -> {resp.status}")
            return text

    # search
    async def search(self, query: str = "", max_pages: int = 3) -> List[Dict]:
        results: List[Dict] = []
        offset = 0
        while True:
            if query:
                url = f"{self.base_url}/list?search={query}&offset={offset}"
            else:
                url = f"{self.base_url}/list?offset=0"

            html = await self.fetch_text(url)
            soup = BeautifulSoup(html, "html.parser")
            tiles = soup.select(".tiles .tile") or soup.select(".tile")
            if not tiles:
                break

            for tile in tiles:
                parsed = self._parse_manga_tile(tile)
                if not parsed:
                    continue
                if query:
                    if query.lower() in (parsed.get("title") or "").lower():
                        results.append(parsed)
                else:
                    results.append(parsed)

            if not query:
                break

            offset += len(tiles)
            if offset <= 0 or (offset // max(1, len(tiles))) + 1 >= max_pages:
                break

        return results

    def _parse_manga_tile(self, tile) -> Optional[Dict]:
        title_el = tile.select_one(".desc h3 a") or tile.select_one("a.tile-title") or tile.select_one("h3 a")
        if not title_el:
            return None
        url = urljoin(self.base_url, title_el.get("href"))
        title = title_el.get_text(strip=True)
        genres = [g.get_text(strip=True) for g in tile.select(".tile-info a[href*='/list/genre/']")]
        description_el = tile.select_one(".manga-description")
        description = description_el.get_text(strip=True) if description_el else None
        return {"title": title, "url": url, "genres": genres, "description": description}

    # get manga info
    async def get_manga_info(self, slug_or_url: str) -> Dict:
        if slug_or_url.startswith("http://") or slug_or_url.startswith("https://"):
            url = slug_or_url
        else:
            url = f"{self.base_url}/{slug_or_url.lstrip('/')}"

        html = await self.fetch_text(url)
        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.select_one("h1.names > span.name") or soup.select_one("h1") or soup.title
        title = title_tag.get_text(strip=True) if title_tag else None

        eng_name_tag = soup.select_one("h1.names > .eng-name")
        eng_name = eng_name_tag.get_text(strip=True) if eng_name_tag else None

        orig_name_tag = soup.select_one("h1.names > .original-name")
        orig_name = orig_name_tag.get_text(strip=True) if orig_name_tag else None

        description_tag = soup.select_one('meta[itemprop="description"]')
        description = description_tag["content"] if description_tag and description_tag.has_attr("content") else None

        author_tag = soup.select_one(".elem_author a.person-link")
        author = author_tag.get_text(strip=True) if author_tag else None

        year_tag = soup.select_one(".elem_year a")
        year = year_tag.get_text(strip=True) if year_tag else None

        genres = [g.get_text(strip=True) for g in soup.select(".elem_genre a")] or [g.get_text(strip=True) for g in soup.select(".elem_genre")]
        category_tag = soup.select_one(".elem_category a")
        category = category_tag.get_text(strip=True) if category_tag else None

        chapters = []
        for row in soup.select("tr.item-row"):
            ch_link = row.select_one("a.chapter-link") or row.select_one("a[href*='/chapter/']")
            if not ch_link:
                continue
            ch_date = row.select_one("td.date")
            ch_title = ch_link.get_text(strip=True)
            ch_url = urljoin(self.base_url, ch_link.get("href"))
            ch_url = self.ensure_mtr(ch_url)
            chapters.append({"title": ch_title, "url": ch_url, "date": ch_date.get_text(strip=True) if ch_date else None})

        # переворачиваем порядок глав (по требованию)
        chapters.reverse()

        return {"title": title, "eng_name": eng_name, "orig_name": orig_name, "description": description,
                "author": author, "year": year, "category": category, "genres": genres, "chapters": chapters}

    # get chapter images
    async def get_chapter_images(self, chapter_url: str) -> List[str]:
        chapter_url = self.ensure_mtr(chapter_url)
        html = await self.fetch_text(chapter_url)

        # основной regex на readerInit
        matches = re.findall(r"\['(https://[^']+)','',\"([^\"]+)\"", html)
        image_urls = []
        for base, path in matches:
            full_url = urljoin(base, path)
            clean_url = full_url.split("?")[0]
            image_urls.append(clean_url)

        return image_urls

    # download chapter images
    async def download_chapter(self, chapter_url: str, out_dir: str = "data/downloads/tmp") -> List[str]:
        chapter_url = self.ensure_mtr(chapter_url)
        os.makedirs(out_dir, exist_ok=True)
        saved_files: List[str] = []

        images = await self.get_chapter_images(chapter_url)
        if not images:
            print("[seimanga] No images found for", chapter_url)
            return []

        sess = await self._get_session()
        for idx, img_url in enumerate(images, start=1):
            try:
                async with sess.get(img_url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        parsed = urlparse(img_url)
                        _, ext = os.path.splitext(parsed.path)
                        if not ext:
                            ext = ".jpg"
                        filename = os.path.join(out_dir, f"{idx}{ext}")
                        with open(filename, "wb") as f:
                            f.write(data)
                        saved_files.append(filename)
                        print(f"[seimanga] Saved {filename}")
                    else:
                        print(f"[seimanga] Error downloading {img_url}: status {resp.status}")
            except Exception as e:
                print(f"[seimanga] Exception downloading {img_url}: {e}")

        return saved_files


# локальное тестирование
if __name__ == "__main__":
    import asyncio

    async def _demo():
        async with SeiMangaParser() as parser:
            res = await parser.search("свадьба", max_pages=1)
            print("search:", len(res))
            if res:
                print(res[0])
            info = await parser.get_manga_info("svadba_vtroem")
            print("title:", info.get("title"))
            if info.get("chapters"):
                ch = info["chapters"][0]
                imgs = await parser.get_chapter_images(ch["url"])
                print("images found:", len(imgs))
                await parser.download_chapter(ch["url"], out_dir="data/downloads/test_ch")

    asyncio.run(_demo())
