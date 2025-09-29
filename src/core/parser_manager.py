import logging
from typing import Dict, Any


class ParserManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.parsers = {}
        self.logger = logging.getLogger("ParserManager")


    def register_parser(self, name: str, parser):
        """Регистрирует парсер по имени"""
        self.parsers[name] = parser
        self.logger.debug(f"Зарегистрирован парсер: {name}")

    def register_all_parsers(self):
        """Регистрирует парсеры в соответствии с конфигом"""
        enabled = self.config.get("enabled_parsers", [])
        self.logger.info(f"Активные парсеры из конфига: {enabled}")

        if "seimanga" in enabled:
            try:
                from parsers.real.seimanga_real import SeiMangaParser
                self.register_parser("seimanga", SeiMangaParser())
            except Exception as e:
                self.logger.error(f"Ошибка регистрации парсера seimanga: {e}")

        # можно по аналогии подключать и другие реальные/тестовые
        if "mangalib" in enabled:
            try:
                from parsers.mangalib import MangaLibParser
                self.register_parser("mangalib", MangaLibParser())
            except Exception as e:
                self.logger.error(f"Ошибка регистрации парсера mangalib: {e}")

        if "remanga" in enabled:
            try:
                from parsers.remanga import RemangaParser
                self.register_parser("remanga", RemangaParser())
            except Exception as e:
                self.logger.error(f"Ошибка регистрации парсера remanga: {e}")

        if "readmanga" in enabled:
            try:
                from parsers.readmanga import ReadMangaParser
                self.register_parser("readmanga", ReadMangaParser())
            except Exception as e:
                self.logger.error(f"Ошибка регистрации парсера readmanga: {e}")

    async def close_all(self):
        """Закрыть все парсеры (например, сессии aiohttp)"""
        for name, parser in self.parsers.items():
            close = getattr(parser, "close", None)
            if callable(close):
                try:
                    await close()
                    self.logger.debug(f"Закрыт парсер: {name}")
                except Exception as e:
                    self.logger.warning(f"Ошибка при закрытии {name}: {e}")
