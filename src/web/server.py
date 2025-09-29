"""
Веб-сервер FastAPI для MangaMonitor
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from core.parser_manager import ParserManager
from core.config import AppConfig

import os

app = FastAPI(title="MangaMonitor API", version="1.0.0")

# Инициализация компонентов
parser_manager = ParserManager()
config = AppConfig()



# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="web/static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Действия при запуске сервера"""
    # Регистрация парсеров
    from parsers.mangalib import MangaLibParser
    mangalib_parser = MangaLibParser()
    parser_manager.register_parser(mangalib_parser)


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "MangaMonitor API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/api/search?q=запрос",
            "health": "/api/health",
            "popular": "/api/popular"
        }
    }


@app.get("/api/search")
async def search_manga(q: str, limit: int = 20):
    """Поиск манги по всем источникам"""
    if not q or len(q.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="Query parameter 'q' is required and must be at least 2 characters long"
        )

    results = await parser_manager.search_all(q.strip())
    limited_results = results[:limit]

    return {
        "query": q,
        "results": limited_results,
        "count": len(limited_results),
        "total_found": len(results)
    }


@app.get("/api/popular")
async def get_popular(limit: int = 10):
    """Получение популярной манги"""
    # TODO: Реализовать получение популярной манги
    return {
        "message": "Popular manga endpoint - to be implemented",
        "limit": limit
    }


@app.get("/api/health")
async def health_check():
    """Проверка здоровья API"""
    return {
        "status": "healthy",
        "parsers_registered": len(parser_manager.parsers),
        "active_parsers": list(parser_manager.parsers.keys())
    }


@app.get("/api/manga/{manga_id}")
async def get_manga_details(manga_id: str, source: str = "mangalib"):
    """Получение детальной информации о манге"""
    parser = parser_manager.get_parser(source)
    if not parser:
        raise HTTPException(status_code=404, detail=f"Parser for source '{source}' not found")

    manga_details = await parser.get_manga_details(manga_id)
    return manga_details


class WebServer:
    def __init__(self, config: AppConfig):
        self.config = config
        self.server = None

    async def start(self):
        """Запуск веб-сервера"""
        import uvicorn

        if self.config.auto_open_browser:
            # Автоматическое открытие браузера
            import webbrowser
            import asyncio
            await asyncio.sleep(1)  # Даем серверу время на запуск
            webbrowser.open(f"http://{self.config.host}:{self.config.port}")

        config = uvicorn.Config(
            app,
            host=self.config.host,
            port=self.config.port,
            log_level="info" if self.config.debug else "warning"
        )
        self.server = uvicorn.Server(config)
        await self.server.serve()

    async def stop(self):
        """Остановка веб-сервера"""
        if self.server:
            self.server.should_exit = True