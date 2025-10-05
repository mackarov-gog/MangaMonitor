# src/parsers/base_parser.py
from __future__ import annotations
import os
import re
import asyncio
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode

import aiohttp
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

DEFAULT_HEADERS =     headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Referer": "https://3.readmanga.ru/search",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }


class BaseMangaParser:
    """Базовый парсер для сайтов одинаковой структуры"""

    def __init__(self, base_url: str, name: str, headers: Optional[dict] = None, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.name = name
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

    # fetch text with params support
    async def fetch_text(self, url: str, params: Optional[dict] = None) -> str:
        sess = await self._get_session()
        async with sess.get(url, params=params) as resp:
            text = await resp.text()
            print(f"[{self.name}] GET {resp.url} -> {resp.status}")
            return text

    def _parse_search_tile(self, tile, query: str = "") -> Dict:
        title_el = tile.select_one(".desc h3 a")
        url = urljoin(self.base_url, title_el["href"]) if title_el else None
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
            "similarity": score,
            "parser": self.name
        }

    # search manga function
    async def search_manga(self, query: str, years: Tuple[int, int] = (1961, 2025),
                          sort: str = "POPULARITY", max_pages: int = 2) -> List[Dict]:
        """Search manga with similarity scoring and sorting"""
        results = []
        offset = 0
        search_url = f"{self.base_url}/search/advancedResults"

        for _ in range(max_pages):
            params = {
                "q": query,
                "offset": offset,
                "years": f"{years[0]},{years[1]}",
                "sortType": sort
            }
            html = await self.fetch_text(search_url, params=params)
            soup = BeautifulSoup(html, "html.parser")

            tiles = soup.select(".tiles .tile")
            if not tiles:
                break

            parsed = [self._parse_search_tile(tile, query) for tile in tiles]
            results.extend(parsed)

            offset += len(tiles)

        # сортировка по совпадению и рейтингу
        results.sort(key=lambda x: (x["similarity"], x["rating"] or 0), reverse=True)
        return results

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

        # переворачиваем порядок глав
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
            print(f"[{self.name}] No images found for", chapter_url)
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
                        print(f"[{self.name}] Saved {filename}")
                    else:
                        print(f"[{self.name}] Error downloading {img_url}: status {resp.status}")
            except Exception as e:
                print(f"[{self.name}] Exception downloading {img_url}: {e}")

        return saved_files