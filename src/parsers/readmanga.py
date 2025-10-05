
from .base_parser import BaseMangaParser

class ReadMangaParser(BaseMangaParser):
    def __init__(self, base_url: str = "https://3.readmanga.ru/", headers: dict = None, timeout: int = 30):
        super().__init__(base_url, "readmanga", headers, timeout)