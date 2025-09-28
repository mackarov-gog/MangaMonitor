"""
Базовый класс для всех парсеров
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
import asyncio


class MangaStatus(Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"
    PAUSED = "paused"
    ANNOUNCED = "announced"


@dataclass
class Manga:
    """Класс для представления манги"""
    id: str
    source: str
    title: str
    url: str
    cover_url: str
    description: Optional[str] = None
    genres: List[str] = None
    status: Optional[MangaStatus] = None
    chapters_count: int = 0
    rating: Optional[float] = None


@dataclass
class Chapter:
    """Класс для представления главы"""
    id: str
    manga_id: str
    title: str
    number: str
    url: str
    volume: Optional[str] = None
    pages_count: int = 0
    publish_date: Optional[str] = None


@dataclass
class Page:
    """Класс для представления страницы"""
    number: int
    url: str
    width: Optional[int] = None
    height: Optional[int] = None


class BaseParser(ABC):
    """Базовый класс парсера"""

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = 30

    async def get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close(self):
        """Закрытие сессии"""
        if self.session and not self.session.closed:
            await self.session.close()

    # В base_parser.py, метод fetch - улучшенная версия
    async def fetch(self, url: str, headers: Dict[str, str] = None, params: Dict[str, str] = None) -> str:
        """Выполнение HTTP запроса с улучшенной обработкой ошибок"""
        session = await self.get_session()

        default_headers = {
            'User-Agent': 'MangaMonitor/1.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        if headers:
            default_headers.update(headers)

        try:
            async with session.get(url, headers=default_headers, params=params) as response:
                if response.status == 403:
                    raise Exception(f"Доступ запрещен (403) для {url}")
                elif response.status == 404:
                    raise Exception(f"Страница не найдена (404) для {url}")
                elif response.status == 429:
                    raise Exception(f"Слишком много запросов (429) для {url}")
                elif response.status >= 500:
                    raise Exception(f"Ошибка сервера ({response.status}) для {url}")

                response.raise_for_status()
                return await response.text()

        except aiohttp.ClientError as e:
            raise Exception(f"Network error for {url}: {e}")
        except asyncio.TimeoutError:
            raise Exception(f"Timeout error for {url}: request took longer than {self.timeout} seconds")

    @abstractmethod
    async def search(self, query: str) -> List[Manga]:
        """Поиск манги"""
        pass

    @abstractmethod
    async def get_popular(self) -> List[Manga]:
        """Получение популярной манги"""
        pass

    @abstractmethod
    async def get_manga_details(self, manga_id: str) -> Manga:
        """Получение детальной информации о манге"""
        pass

    @abstractmethod
    async def get_chapters(self, manga_id: str) -> List[Chapter]:
        """Получение списка глав"""
        pass

    @abstractmethod
    async def get_pages(self, chapter_id: str) -> List[Page]:
        """Получение страниц главы"""
        pass