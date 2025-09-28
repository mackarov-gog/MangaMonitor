"""
Парсер для remanga.org с тестовыми данными
"""

from parsers.base_parser import BaseParser, Manga, MangaStatus, Chapter, Page
from typing import List, Optional
import logging
import random

logger = logging.getLogger(__name__)


class RemangaParser(BaseParser):
    """Парсер для remanga.org"""

    def __init__(self):
        super().__init__("remanga", "https://remanga.org")
        self._test_data = self._create_test_data()

    def _create_test_data(self) -> List[Manga]:
        """Создает тестовые данные для remanga.org"""
        return [
            Manga(
                id="solo_leveling_remanga",
                source=self.name,
                title="Solo Leveling",
                url="https://remanga.org/manga/solo-leveling",
                cover_url="https://via.placeholder.com/200x300/8E44AD/FFFFFF?text=Solo+Leveling",
                description="Сон Джин-Ву - самый слабый охотник в мире, но после попадания в загадочный подземелье он получает уникальную способность - систему уровней. Теперь он может расти в силе, выполняя quest-ы и повышая уровень.",
                genres=["Фэнтези", "Боевик", "Приключения", "Система", "Экшен"],
                status=MangaStatus.COMPLETED,
                chapters_count=179,
                rating=4.8
            ),
            Manga(
                id="tower_of_god_remanga",
                source=self.name,
                title="Tower of God",
                url="https://remanga.org/manga/tower-of-god",
                cover_url="https://via.placeholder.com/200x300/F39C12/FFFFFF?text=Tower+of+God",
                description="Двадцать пятый ночь следует за загадочной девушкой по имени Рейчел в Башню - мистическое сооружение, где исполняются любые желания тех, кто достигнет вершины.",
                genres=["Фэнтези", "Приключения", "Драма", "Экшен", "Загадка"],
                status=MangaStatus.ONGOING,
                chapters_count=550,
                rating=4.7
            ),
            Manga(
                id="the_beginning_after_the_end_remanga",
                source=self.name,
                title="The Beginning After the End",
                url="https://remanga.org/manga/the-beginning-after-the-end",
                cover_url="https://via.placeholder.com/200x300/16A085/FFFFFF?text=TBATE",
                description="Король Грей умирает и перерождается в мире магии как Артур Лейвин. Используя знания из прошлой жизни, он стремится защитить свою новую семью и стать сильнее в этом опасном мире.",
                genres=["Фэнтези", "Драма", "Экшен", "Перерождение", "Магия"],
                status=MangaStatus.ONGOING,
                chapters_count=180,
                rating=4.6
            ),
            Manga(
                id="omniscient_reader_remanga",
                source=self.name,
                title="Omniscient Reader",
                url="https://remanga.org/manga/omniscient-reader",
                cover_url="https://via.placeholder.com/200x300/C0392B/FFFFFF?text=Omniscient+Reader",
                description="Ким Докча - обычный офисный работник, который оказывается единственным читателем непопулярного веб-романа. Когда роман становится реальностью, его знания становятся ключом к выживанию.",
                genres=["Фэнтези", "Драма", "Экшен", "Выживание", "Приключения"],
                status=MangaStatus.ONGOING,
                chapters_count=150,
                rating=4.8
            )
        ]

    async def search(self, query: str) -> List[Manga]:
        """Поиск манги"""
        logger.info(f"Поиск манги на remanga: '{query}'")

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
                title=f"Глава {i}",
                number=str(i),
                url=f"{self.base_url}/manga/{manga_id}/chapter/{i}",
                pages_count=random.randint(20, 30)
            ))
        return chapters

    async def get_pages(self, chapter_id: str) -> List[Page]:
        """Получение страниц главы"""
        pages = []
        for i in range(1, random.randint(18, 30)):
            pages.append(Page(
                number=i,
                url=f"https://via.placeholder.com/800x1200/8E44AD/FFFFFF?text=ReManga+Page+{i}"
            ))
        return pages