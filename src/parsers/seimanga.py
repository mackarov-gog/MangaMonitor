
from .base_parser import BaseMangaParser

class SeiMangaParser(BaseMangaParser):
    def __init__(self, base_url: str = "https://1.seimanga.me", headers: dict = None, timeout: int = 30):
        super().__init__(base_url, "seimanga", headers, timeout)