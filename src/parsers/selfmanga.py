from .base_parser import BaseMangaParser

class SelfMangaParser(BaseMangaParser):
    def __init__(self, base_url: str = "https://1.selfmanga.live/", headers: dict = None, timeout: int = 30):
        super().__init__(base_url, "selfmanga", headers, timeout)