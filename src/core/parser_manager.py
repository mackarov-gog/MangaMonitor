"""
Менеджер парсеров для координации работы всех парсеров
"""

from typing import List, Dict
import asyncio
from parsers.base_parser import BaseParser, Manga
from parsers.mangalib import MangaLibParser
from parsers.readmanga import ReadMangaParser
from parsers.remanga import RemangaParser
from parsers.seimanga import SeiMangaParser
from parsers.desu import DesuParser
import logging

logger = logging.getLogger(__name__)


class ParserManager:
    """Управляет всеми зарегистрированными парсерами"""

    def __init__(self):
        self.parsers: Dict[str, BaseParser] = {}

    def register_parser(self, parser: BaseParser):
        """Регистрирует парсер в менеджере"""
        self.parsers[parser.name] = parser
        logger.info(f"Зарегистрирован парсер: {parser.name}")

    def register_all_parsers(self):
        """Регистрирует все доступные парсеры"""
        parsers = [
            MangaLibParser(),
            ReadMangaParser(),
            RemangaParser(),
            SeiMangaParser(),
            DesuParser()
        ]

        for parser in parsers:
            self.register_parser(parser)

    async def search_all(self, query: str) -> List[Manga]:
        """Выполняет поиск по всем зарегистрированным парсерам"""
        if not self.parsers:
            return []

        tasks = []
        for parser_name, parser in self.parsers.items():
            task = self._safe_search(parser, query, parser_name)
            tasks.append(task)

        # Запускаем все поиски параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Объединяем результаты
        all_manga = []
        for result in results:
            if isinstance(result, list):
                all_manga.extend(result)

        logger.info(f"Поиск завершен. Всего найдено: {len(all_manga)} манги")
        return all_manga

    async def _safe_search(self, parser: BaseParser, query: str, parser_name: str):
        """Безопасный поиск с обработкой ошибок"""
        try:
            logger.info(f"Поиск в парсере {parser_name}: '{query}'")
            results = await parser.search(query)
            logger.info(f"Парсер {parser_name} нашел {len(results)} результатов")
            return results
        except Exception as e:
            logger.error(f"Ошибка в парсере {parser_name}: {e}")
            return []

    def get_parser(self, source_name: str) -> BaseParser:
        """Возвращает парсер по имени источника"""
        return self.parsers.get(source_name)

    def get_available_sources(self) -> List[str]:
        """Возвращает список доступных источников"""
        return list(self.parsers.keys())

    async def close_all(self):
        """Закрывает все сессии парсеров"""
        for parser in self.parsers.values():
            if hasattr(parser, 'close'):
                await parser.close()