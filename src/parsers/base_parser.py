from abc import ABC, abstractmethod
from typing import List, Dict
from parsers.real.seimanga_real import SeiMangaParser

def register_all_parsers(self):
    # тестовые
    from parsers import mangalib, remanga, readmanga

    self.register_parser("mangalib", mangalib.MockParser())
    self.register_parser("remanga", remanga.MockParser())
    self.register_parser("readmanga", readmanga.MockParser())

    # реальные
    self.register_parser("seimanga", SeiMangaParser())


class BaseParser(ABC):
    """
    Абстрактный класс для всех парсеров манги.
    Все реальные и тестовые парсеры должны реализовать эти методы.
    """

    @abstractmethod
    async def get_manga_info(self, url: str) -> Dict:
        """
        Возвращает информацию о манге:
        {
            "title": str,
            "author": str,
            "genres": [str],
            "description": str,
            "chapters": [ { "title": str, "url": str, "date": str } ]
        }
        """
        raise NotImplementedError

    @abstractmethod
    async def get_chapters(self, manga_url: str) -> List[Dict]:
        """
        Возвращает список глав по URL манги:
        [
            { "title": str, "url": str, "date": str }
        ]
        """
        raise NotImplementedError

    @abstractmethod
    async def get_chapter_pages(self, chapter_url: str) -> List[str]:
        """
        Возвращает список страниц главы (ссылки на изображения).
        """
        raise NotImplementedError

    @abstractmethod
    async def download_chapter(self, chapter_url: str, out_dir: str) -> List[str]:
        """
        Скачивает страницы главы в указанную папку.
        Возвращает список локальных файлов.
        """
        raise NotImplementedError
