"""
Парсер для Desu с тестовыми данными
"""

from parsers.base_parser import BaseParser, Manga, MangaStatus, Chapter, Page
from typing import List, Optional
import logging
import random

logger = logging.getLogger(__name__)


class DesuParser(BaseParser):
    """Парсер для Desu"""

    def __init__(self):
        super().__init__("desu", "https://desu.me")
        self._test_data = self._create_test_data()

    def _create_test_data(self) -> List[Manga]:
        """Создает тестовые данные для Desu"""
        return [
            Manga(
                id="monogatari_series_desu",
                source=self.name,
                title="Monogatari Series",
                url="https://desu.me/manga/monogatari",
                cover_url="https://via.placeholder.com/200x300/9B59B6/FFFFFF?text=Monogatari",
                description="Кояоми Арараги, старшеклассник, который недавно пережил нападение вампира. Теперь он помогает различным девушкам, столкнувшимся с сверхъестественными явлениями, известными как 'аберрации'.",
                genres=["Сверхъестественное", "Комедия", "Драма", "Романтика", "Мистика"],
                status=MangaStatus.ONGOING,
                chapters_count=120,
                rating=4.7
            ),
            Manga(
                id="sangatsu_no_lion_desu",
                source=self.name,
                title="March Comes in Like a Lion",
                url="https://desu.me/manga/sangatsu-no-lion",
                cover_url="https://via.placeholder.com/200x300/1ABC9C/FFFFFF?text=March+Lion",
                description="Рэй Кирияма, профессиональный игрок в сёги, переживающий депрессию и одиночество. Его жизнь меняется, когда он встречает сёстёр Кавамото, которые помогают ему найти тепло и смысл в жизни.",
                genres=["Драма", "Повседневность", "Спорт", "Сэйнэн"],
                status=MangaStatus.ONGOING,
                chapters_count=180,
                rating=4.8
            ),
            Manga(
                id="ushio_to_tora_desu",
                source=self.name,
                title="Ushio and Tora",
                url="https://desu.me/manga/ushio-to-tora",
                cover_url="https://via.placeholder.com/200x300/E74C3C/FFFFFF?text=Ushio+Tora",
                description="Ушио Аоцуки находит в подвале своего храма запечатанного демона Тора. Вынужденный освободить его для борьбы с другими ёкаями, Ушио и Тора становятся невероятным дуэтом.",
                genres=["Фэнтези", "Комедия", "Экшен", "Сёнэн", "Сверхъестественное"],
                status=MangaStatus.COMPLETED,
                chapters_count=153,
                rating=4.4
            ),
            Manga(
                id="danshi_koukousei_no_nichijou_desu",
                source=self.name,
                title="Daily Lives of High School Boys",
                url="https://desu.me/manga/danshi-koukousei-no-nichijou",
                cover_url="https://via.placeholder.com/200x300/F39C12/FFFFFF?text=Daily+Lives",
                description="Комедийная манга о повседневной жизни трёх друзей-старшеклассников: Тадакуни, Ёситаке и Хидэнари. Их абсурдные приключения и уникальный взгляд на школьную жизнь.",
                genres=["Комедия", "Повседневность", "Школа", "Сёнэн"],
                status=MangaStatus.COMPLETED,
                chapters_count=66,
                rating=4.5
            )
        ]

    async def search(self, query: str) -> List[Manga]:
        """Поиск манги"""
        logger.info(f"Поиск манги на desu: '{query}'")

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
                title=f"Серия {i}",
                number=str(i),
                url=f"{self.base_url}/manga/{manga_id}/volume1/{i}",
                pages_count=random.randint(18, 24)
            ))
        return chapters

    async def get_pages(self, chapter_id: str) -> List[Page]:
        """Получение страниц главы"""
        pages = []
        for i in range(1, random.randint(17, 24)):
            pages.append(Page(
                number=i,
                url=f"https://via.placeholder.com/800x1200/9B59B6/FFFFFF?text=Desu+Page+{i}"
            ))
        return pages