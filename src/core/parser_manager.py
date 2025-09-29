# src/core/parser_manager.py
from typing import Dict
from src.parsers.seimanga import SeiMangaParser

_PARSERS: Dict[str, type] = {
    "seimanga": SeiMangaParser,   # ХРАНИМ КЛАСС, а не SeiMangaParser()
}

def get_parser(name: str):
    cls = _PARSERS.get(name)
    return cls() if cls else None

def list_parsers():
    return list(_PARSERS.keys())
