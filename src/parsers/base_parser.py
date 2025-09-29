from abc import ABC, abstractmethod
from typing import List, Dict
from enum import Enum


class MangaStatus(Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"
    UNKNOWN = "unknown"


class Manga:
    def __init__(self, title: str, url: str, author: str = None,
                 genres: List[str] = None, description: str = ""):
        self.title = title
        self.url = url
        self.author = author
        self.genres = genres or []
        self.description = description
        self.chapters: List[Chapter] = []  # объявится ниже


class Chapter:
    def __init__(self, title: str, url: str, date: str = None):
        self.title = title
        self.url = url
        self.date = date
        self.pages: List[Page] = []


class Page:
    def __init__(self, url: str, local_path: str = None):
        self.url = url
        self.local_path = local_path


class BaseParser(ABC):
    @abstractmethod
    async def search(self, query: str) -> List[Dict]:
        """Поиск манги по названию"""
        raise NotImplementedError

    @abstractmethod
    async def get_manga_info(self, url: str) -> Dict:
        """Инфо о манге + список глав"""
        raise NotImplementedError

    @abstractmethod
    async def get_chapters(self, manga_url: str) -> List[Dict]:
        """Список глав"""
        raise NotImplementedError

    @abstractmethod
    async def get_chapter_pages(self, chapter_url: str) -> List[str]:
        """Список страниц главы"""
        raise NotImplementedError

    @abstractmethod
    async def download_chapter(self, chapter_url: str, out_dir: str) -> List[str]:
        """Скачать главу"""
        raise NotImplementedError
