"""
Парсер для readmanga.io с тестовыми данными
"""

from parsers.base_parser import BaseParser, Manga, MangaStatus, Chapter, Page
from typing import List, Optional
import logging
import random

logger = logging.getLogger(__name__)


class ReadMangaParser(BaseParser):
    """Парсер для readmanga.io"""

    def __init__(self):
        super().__init__("readmanga", "https://readmanga.io")
        self._test_data = self._create_test_data()

    def _create_test_data(self) -> List[Manga]:
        """Создает тестовые данные для readmanga.io"""
        return [
            Manga(
                id="berserk__readmanga",
                source=self.name,
                title="Berserk",
                url="https://readmanga.io/berserk",
                cover_url="https://via.placeholder.com/200x300/2C3E50/FFFFFF?text=Berserk",
                description="Мрачная история о воине Гатсе, сражающемся с демонами в средневековом мире. Путь мести и выживания в жестоком мире, где демоны правят бал.",
                genres=["Ужасы", "Фэнтези", "Драма", "Сэйнэн", "Экшен"],
                status=MangaStatus.ONGOING,
                chapters_count=367,
                rating=4.9
            ),
            Manga(
                id="vagabond__readmanga",
                source=self.name,
                title="Vagabond",
                url="https://readmanga.io/vagabond",
                cover_url="https://via.placeholder.com/200x300/27AE60/FFFFFF?text=Vagabond",
                description="История о Миямото Мусаси, легендарном японском фехтовальщике. Путь воина, ищущего просветление через мастерство меча.",
                genres=["Исторический", "Драма", "Сэйнэн", "Боевик"],
                status=MangaStatus.PAUSED,
                chapters_count=327,
                rating=4.8
            ),
            Manga(
                id="kingdom__readmanga",
                source=self.name,
                title="Kingdom",
                url="https://readmanga.io/kingdom",
                cover_url="https://via.placeholder.com/200x300/E74C3C/FFFFFF?text=Kingdom",
                description="Эпическая сага о периоде Воюющих царств в древнем Китае. Син и его путь от раба до великого генерала.",
                genres=["Исторический", "Боевик", "Драма", "Сэйнэн"],
                status=MangaStatus.ONGOING,
                chapters_count=750,
                rating=4.7
            ),
            Manga(
                id="vinland_saga__readmanga",
                source=self.name,
                title="Vinland Saga",
                url="https://readmanga.io/vinland_saga",
                cover_url="https://via.placeholder.com/200x300/3498DB/FFFFFF?text=Vinland",
                description="История викингов и их завоеваний. Торфинн ищет мести за смерть отца в жестоком мире скандинавских воителей.",
                genres=["Исторический", "Драма", "Сэйнэн", "Приключения"],
                status=MangaStatus.ONGOING,
                chapters_count=200,
                rating=4.6
            )
        ]

    async def search(self, query: str) -> List[Manga]:
        """Поиск манги"""
        logger.info(f"Поиск манги на readmanga: '{query}'")

        if not query:
            return self._test_data[:3]

        query_lower = query.lower()
        results = []

        for manga in self._test_data:
            if (query_lower in manga.title.lower() or
                    any(query_lower in genre.lower() for genre in manga.genres) or
                    query_lower in manga.description.lower()):
                results.append(manga)

        return results if results else random.sample(self._test_data, min(2, len(self._test_data)))

    async def get_manga_details(self, manga_id: str) -> Manga:
        """Получение детальной информации о манге"""
        for manga in self._test_data:
            if manga.id == manga_id:
                return manga

        return Manga(
            id=manga_id,
            source=self.name,
            title=f"Манга {manga_id}",
            url=f"{self.base_url}/{manga_id}",
            cover_url=""
        )

    async def get_popular(self) -> List[Manga]:
        """Получение популярной манги"""
        return self._test_data[:3]

    async def get_chapters(self, manga_id: str) -> List[Chapter]:
        """Получение списка глав"""
        chapters = []
        for i in range(1, 6):
            chapters.append(Chapter(
                id=f"{manga_id}_chapter_{i}",
                manga_id=manga_id,
                title=f"Том 1 Глава {i}",
                number=str(i),
                url=f"{self.base_url}/{manga_id}/vol1/{i}",
                pages_count=random.randint(18, 25)
            ))
        return chapters

    async def get_pages(self, chapter_id: str) -> List[Page]:
        """Получение страниц главы"""
        pages = []
        for i in range(1, random.randint(15, 25)):
            pages.append(Page(
                number=i,
                url=f"https://via.placeholder.com/800x1200/2C3E50/FFFFFF?text=ReadManga+Page+{i}"
            ))
        return pages