"""
Парсер для SeiManga с тестовыми данными
"""

from parsers.base_parser import BaseParser, Manga, MangaStatus, Chapter, Page
from typing import List, Optional
import logging
import random

logger = logging.getLogger(__name__)


class SeiMangaParser(BaseParser):
    """Парсер для SeiManga"""

    def __init__(self):
        super().__init__("seimanga", "https://seimanga.org")
        self._test_data = self._create_test_data()

    def _create_test_data(self) -> List[Manga]:
        """Создает тестовые данные для SeiManga"""
        return [
            Manga(
                id="claymore_seimanga",
                source=self.name,
                title="Claymore",
                url="https://seimanga.org/manga/claymore",
                cover_url="https://via.placeholder.com/200x300/7F8C8D/FFFFFF?text=Claymore",
                description="В мире, где люди страдают от существ под названием Йома, организация создаёт воинов-гибридов - Клеймор. Тереза, серебряноглазая воительница, сражается с Йома, скрывая свою человечность.",
                genres=["Фэнтези", "Ужасы", "Драма", "Сёнэн", "Экшен"],
                status=MangaStatus.COMPLETED,
                chapters_count=155,
                rating=4.5
            ),
            Manga(
                id="dorohedoro_seimanga",
                source=self.name,
                title="Dorohedoro",
                url="https://seimanga.org/manga/dorohedoro",
                cover_url="https://via.placeholder.com/200x300/F1C40F/FFFFFF?text=Dorohedoro",
                description="В городе-трущобах Хол, маги с другого мира проводят эксперименты на людях. Кайман, человек с головой ящера, ищет мага, который наложил на него проклятие.",
                genres=["Фэнтези", "Комедия", "Ужасы", "Сэйнэн", "Экшен"],
                status=MangaStatus.COMPLETED,
                chapters_count=167,
                rating=4.6
            ),
            Manga(
                id="blame_seimanga",
                source=self.name,
                title="Blame!",
                url="https://seimanga.org/manga/blame",
                cover_url="https://via.placeholder.com/200x300/34495E/FFFFFF?text=Blame!",
                description="Кили, одинокий странник в бесконечном техногенном городе, ищет людей с чистым генетическим кодом, чтобы восстановить систему контроля над городом.",
                genres=["Киберпанк", "Научная фантастика", "Сэйнэн", "Постапокалипсис"],
                status=MangaStatus.COMPLETED,
                chapters_count=65,
                rating=4.4
            ),
            Manga(
                id="gantz_seimanga",
                source=self.name,
                title="Gantz",
                url="https://seimanga.org/manga/gantz",
                cover_url="https://via.placeholder.com/200x300/E67E22/FFFFFF?text=Gantz",
                description="Кей Куроно и его друг погибают, но вместо смерти оказываются в комнате с чёрным шаром по имени Ганц. Теперь они должны участвовать в смертельных играх против инопланетян.",
                genres=["Научная фантастика", "Ужасы", "Экшен", "Сэйнэн", "Драма"],
                status=MangaStatus.COMPLETED,
                chapters_count=383,
                rating=4.3
            )
        ]

    async def search(self, query: str) -> List[Manga]:
        """Поиск манги"""
        logger.info(f"Поиск манги на seimanga: '{query}'")

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
            url=f"{self.base_url}/manga/{manga_id}",
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
                title=f"Книга 1 Глава {i}",
                number=str(i),
                url=f"{self.base_url}/manga/{manga_id}/book1/{i}",
                pages_count=random.randint(16, 22)
            ))
        return chapters

    async def get_pages(self, chapter_id: str) -> List[Page]:
        """Получение страниц главы"""
        pages = []
        for i in range(1, random.randint(15, 22)):
            pages.append(Page(
                number=i,
                url=f"https://via.placeholder.com/800x1200/7F8C8D/FFFFFF?text=SeiManga+Page+{i}"
            ))
        return pages