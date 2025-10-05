# src/parsers/__init__.py
from .base_parser import BaseMangaParser
from .seimanga import SeiMangaParser
from .selfmanga import SelfMangaParser
from .readmanga import ReadMangaParser
from .mintmanga import MintMangaParser
from .zazaza import ZazazaParser

__all__ = [
    'BaseMangaParser',
    'SeiMangaParser',
    'SelfMangaParser',
    'ReadMangaParser',
    'MintMangaParser',
    'ZazazaParser'
]