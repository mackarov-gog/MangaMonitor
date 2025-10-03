
from .base_parser import BaseMangaParser

class ZazazaParser(BaseMangaParser):
    def __init__(self, base_url: str = "https://a.zazaza.me/", headers: dict = None, timeout: int = 30):
        super().__init__(base_url, "zazaza", headers, timeout)