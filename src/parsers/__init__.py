"""
Парсеры для различных источников манги
"""

from .base_parser import BaseParser, Manga, Chapter, Page, MangaStatus
from .mangalib import MangaLibParser
from .readmanga import ReadMangaParser
from .remanga import RemangaParser
from .seimanga import SeiMangaParser
from .desu import DesuParser

__all__ = [
    'BaseParser', 'Manga', 'Chapter', 'Page', 'MangaStatus',
    'MangaLibParser', 'ReadMangaParser', 'RemangaParser',
    'SeiMangaParser', 'DesuParser'
]