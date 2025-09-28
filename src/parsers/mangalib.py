"""
Качественный парсер с тестовыми данными для разработки приложения
"""

from parsers.base_parser import BaseParser, Manga, MangaStatus, Chapter, Page
from typing import List, Optional
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class MangaLibParser(BaseParser):
    """Качественный парсер с тестовыми данными для продолжения разработки"""

    def __init__(self):
        super().__init__("mangalib", "https://mangalib.me")
        self._test_data = self._create_test_data()

    def _create_test_data(self) -> List[Manga]:
        """Создает качественные тестовые данные"""
        return [
            Manga(
                id="195--naruto",
                source=self.name,
                title="Naruto",
                url="https://mangalib.me/ru/manga/195--naruto",
                cover_url="https://via.placeholder.com/200x300/FF6B6B/FFFFFF?text=Naruto",
                description="История о ниндзя-подростке Наруто Узумаки, который мечтает стать Хокаге - лидером своей деревни. Несмотря на то, что в нём запечатан Девятихвостый демон-лис, он не сдаётся и продолжает тренироваться, чтобы достичь своей цели.",
                genres=["Приключения", "Боевик", "Комедия", "Сёнэн", "Экшен"],
                status=MangaStatus.COMPLETED,
                chapters_count=700,
                rating=4.8
            ),
            Manga(
                id="2--one-piece",
                source=self.name,
                title="One Piece",
                url="https://mangalib.me/ru/manga/2--one-piece",
                cover_url="https://via.placeholder.com/200x300/4ECDC4/FFFFFF?text=One+Piece",
                description="Пиратские приключения Манки Д. Луффи и его команды в поисках величайшего сокровища Ван Пис. Луффи, обладающий способностью растягиваться как резина после съедения Дьявольского плода, собирает разношёрстную команду пиратов для достижения своей мечты.",
                genres=["Приключения", "Комедия", "Фэнтези", "Сёнэн", "Экшен"],
                status=MangaStatus.ONGOING,
                chapters_count=1100,
                rating=4.9
            ),
            Manga(
                id="3--attack-on-titan",
                source=self.name,
                title="Attack on Titan",
                url="https://mangalib.me/ru/manga/3--attack-on-titan",
                cover_url="https://via.placeholder.com/200x300/45B7D1/FFFFFF?text=Attack+on+Titan",
                description="Человечество борется за выживание против гигантских титанов. Эрен Йегер и его друзья вступают в разведкорпус, чтобы отомстить титанам и раскрыть тайны своего мира.",
                genres=["Ужасы", "Драма", "Фэнтези", "Боевик", "Сёнэн"],
                status=MangaStatus.COMPLETED,
                chapters_count=139,
                rating=4.8
            ),
            Manga(
                id="7072--eleceed-",
                source=self.name,
                title="Eleceed",
                url="https://mangalib.me/ru/manga/7072--eleceed-",
                cover_url="https://via.placeholder.com/200x300/96CEB4/FFFFFF?text=Eleceed",
                description="Парень, который может превращаться в кота, и его приключения в мире способностей. Сейха ДжинвУ обладает способностью превращаться в кота и встречает Кайдана, который скрывает свои силы.",
                genres=["Фэнтези", "Боевик", "Комедия", "Сверхъестественное", "Сёнэн"],
                status=MangaStatus.ONGOING,
                chapters_count=250,
                rating=4.7
            ),
            Manga(
                id="23456--boruto",
                source=self.name,
                title="Boruto: Naruto Next Generations",
                url="https://mangalib.me/ru/manga/23456--boruto",
                cover_url="https://via.placeholder.com/200x300/F7CAC9/FFFFFF?text=Boruto",
                description="Продолжение истории Наруто, сосредоточенное на его сыне Боруто и новом поколении ниндзя. Боруто сталкивается с новыми угрозами и вызовами в эпоху технологий.",
                genres=["Приключения", "Боевик", "Сёнэн", "Экшен"],
                status=MangaStatus.ONGOING,
                chapters_count=85,
                rating=4.3
            ),
            Manga(
                id="7890--onepunchman",
                source=self.name,
                title="One-Punch Man",
                url="https://mangalib.me/ru/manga/7890--onepunchman",
                cover_url="https://via.placeholder.com/200x300/FFEAA7/FFFFFF?text=One+Punch+Man",
                description="Сайтама - герой, который может победить любого врага одним ударом. Он ищет достойного противника, страдая от скуки из-за своей непобедимости.",
                genres=["Комедия", "Боевик", "Сёнэн", "Пародия", "Супергерои"],
                status=MangaStatus.ONGOING,
                chapters_count=200,
                rating=4.7
            ),
            Manga(
                id="4567--demon-slayer",
                source=self.name,
                title="Demon Slayer: Kimetsu no Yaiba",
                url="https://mangalib.me/ru/manga/4567--demon-slayer",
                cover_url="https://via.placeholder.com/200x300/DDA0DD/FFFFFF?text=Demon+Slayer",
                description="Танджиро Камадо становится истребителем демонов, чтобы найти лекарство для своей сестры, превращённой в демона, и отомстить за смерть своей семьи.",
                genres=["Приключения", "Боевик", "Сверхъестественное", "Сёнэн", "Драма"],
                status=MangaStatus.COMPLETED,
                chapters_count=205,
                rating=4.6
            ),
            Manga(
                id="8912--my-hero-academia",
                source=self.name,
                title="My Hero Academia",
                url="https://mangalib.me/ru/manga/8912--my-hero-academia",
                cover_url="https://via.placeholder.com/200x300/98D8C8/FFFFFF?text=MHA",
                description="В мире, где у большинства людей есть сверхспособности, мальчик без способностей мечтает стать величайшим героем. Идзуку Мидория встречает своего кумира Всемогущего и получает шанс осуществить свою мечту.",
                genres=["Боевик", "Комедия", "Сёнэн", "Супергерои", "Школа"],
                status=MangaStatus.ONGOING,
                chapters_count=400,
                rating=4.5
            )
        ]

    async def search(self, query: str) -> List[Manga]:
        """Поиск манги по тестовым данным"""
        logger.info(f"Поиск манги: '{query}' (тестовые данные)")

        if not query or not query.strip():
            return self._test_data[:5]  # Возвращаем первые 5 по умолчанию

        query_lower = query.lower().strip()
        results = []

        for manga in self._test_data:
            # Поиск по названию
            if query_lower in manga.title.lower():
                results.append(manga)
                continue

            # Поиск по жанрам
            for genre in manga.genres:
                if query_lower in genre.lower():
                    results.append(manga)
                    break

            # Поиск по описанию (только если запрос длинный)
            if len(query_lower) > 3 and query_lower in manga.description.lower():
                results.append(manga)
                continue

        # Если ничего не нашли, возвращаем случайные манги
        if not results:
            logger.info(f"По запросу '{query}' ничего не найдено, возвращаем случайные манги")
            results = random.sample(self._test_data, min(3, len(self._test_data)))

        return results

    async def get_manga_details(self, manga_id: str) -> Manga:
        """Получение детальной информации о манге"""
        logger.info(f"Получение деталей манги: {manga_id}")

        for manga in self._test_data:
            if manga.id == manga_id:
                return manga

        # Если не нашли, создаем базовую мангу
        return Manga(
            id=manga_id,
            source=self.name,
            title=f"Манга {manga_id}",
            url=f"{self.base_url}/manga/{manga_id}",
            cover_url="",
            description="Информация о манге будет доступна позже"
        )

    async def get_popular(self) -> List[Manga]:
        """Получение популярной манги"""
        logger.info("Получение популярной манги")
        # Возвращаем случайные 5 манг как популярные
        return random.sample(self._test_data, min(5, len(self._test_data)))

    async def get_chapters(self, manga_id: str) -> List[Chapter]:
        """Получение списка глав"""
        logger.info(f"Получение глав для манги: {manga_id}")

        chapters = []
        base_chapter_count = random.randint(50, 300)

        for i in range(1, min(11, base_chapter_count)):  # Ограничим 10 главами для демо
            chapters.append(Chapter(
                id=f"{manga_id}_chapter_{i}",
                manga_id=manga_id,
                title=f"Глава {i}",
                number=str(i),
                url=f"{self.base_url}/manga/{manga_id}/chapter/{i}",
                volume="1",
                pages_count=random.randint(15, 25),
                publish_date=f"2023-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            ))

        return chapters

    async def get_pages(self, chapter_id: str) -> List[Page]:
        """Получение страниц главы"""
        logger.info(f"Получение страниц для главы: {chapter_id}")

        pages = []
        pages_count = random.randint(15, 25)

        for i in range(1, pages_count + 1):
            pages.append(Page(
                number=i,
                url=f"https://via.placeholder.com/800x1200/333/fff?text=Страница+{i}",
                width=800,
                height=1200
            ))

        return pages

    async def get_latest_updates(self) -> List[Manga]:
        """Получение последних обновлений"""
        logger.info("Получение последних обновлений")
        # Возвращаем случайные 5 манг как обновленные
        return random.sample(self._test_data, min(5, len(self._test_data)))