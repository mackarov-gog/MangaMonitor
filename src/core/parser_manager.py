# src/core/parser_manager.py
import asyncio
from typing import Dict, List, Optional
from urllib.parse import urlparse

from src.parsers.seimanga import SeiMangaParser
from src.parsers.selfmanga import SelfMangaParser
from src.parsers.readmanga import ReadMangaParser
from src.parsers.mintmanga import MintMangaParser
from src.parsers.zazaza import ZazazaParser
from src.parsers.desucity import DesuCityParser

_PARSERS: Dict[str, type] = {
    "seimanga": SeiMangaParser,
    "selfmanga": SelfMangaParser,
    "readmanga": ReadMangaParser,
    "mintmanga": MintMangaParser,
    "zazaza": ZazazaParser,
    "desucity": DesuCityParser,
}

# Карта доменов для автоматического определения парсера
_DOMAIN_MAP = {
    "seimanga.me": "seimanga",
    "selfmanga.ru": "selfmanga",
    "readmanga.io": "readmanga",
    "mintmanga.live": "mintmanga",
    "zazaza.ru": "zazaza",
}


def get_parser(name: str):
    """Получить конкретный парсер по имени"""
    cls = _PARSERS.get(name)
    return cls() if cls else None


def get_parsers(names: List[str] = None):
    """Получить список парсеров"""
    if names is None:
        names = list(_PARSERS.keys())
    return [cls() for name, cls in _PARSERS.items() if name in names]


def get_all_parsers():
    """Получить все парсеры"""
    return [cls() for cls in _PARSERS.values()]


def list_parsers():
    return list(_PARSERS.keys())


def get_parser_by_url(url: str):
    """Автоматически определить подходящий парсер по URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Ищем подходящий домен в карте
        for domain_pattern, parser_name in _DOMAIN_MAP.items():
            if domain_pattern in domain:
                return get_parser(parser_name)

        # Если точного совпадения нет, попробуем найти по имени хоста
        for parser_name, parser_cls in _PARSERS.items():
            parser_instance = parser_cls()
            parser_domain = urlparse(parser_instance.base_url).netloc.lower()
            if parser_domain in domain or domain in parser_domain:
                return parser_instance

        return None
    except Exception:
        return None


async def search_all_parsers(query: str, parsers: List = None, **kwargs) -> List[Dict]:
    """Поиск по всем парсерам с объединением результатов"""
    if parsers is None:
        parsers = get_all_parsers()

    all_results = []

    # Запускаем поиск параллельно во всех парсерах
    tasks = []
    for parser in parsers:
        tasks.append(parser.search_manga(query, **kwargs))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Обрабатываем результаты
    for parser, result in zip(parsers, results):
        if isinstance(result, Exception):
            print(f"Ошибка в парсере {parser.name}: {result}")
            continue
        all_results.extend(result)

    # Сортируем объединенные результаты
    all_results.sort(key=lambda x: (x.get("similarity", 0), x.get("rating", 0)), reverse=True)
    return all_results