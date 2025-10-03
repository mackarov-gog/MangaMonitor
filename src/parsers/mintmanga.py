from .base_parser import BaseMangaParser

class MintMangaParser(BaseMangaParser):
    def __init__(self, base_url: str = "https://1.mintmanga.com/", headers: dict = None, timeout: int = 30):
        super().__init__(base_url, "mintmanga", headers, timeout)