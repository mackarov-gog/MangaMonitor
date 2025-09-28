"""
Конфигурация приложения
"""

import json
from pathlib import Path
from typing import Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """Конфигурация приложения"""

    # Настройки приложения
    app_name: str = "MangaMonitor"
    version: str = "0.0.1"
    debug: bool = Field(False, env="DEBUG")

    # Настройки веб-сервера
    host: str = "127.0.0.1"
    port: int = 8000
    auto_open_browser: bool = True

    # Настройки парсеров
    request_timeout: int = 30
    max_concurrent_requests: int = 5
    user_agent: str = "MangaMonitor/1.0.0"

    # Настройки кэша
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 час
    max_cache_size: str = "1GB"

    # Настройки базы данных
    database_url: str = "sqlite:///data/mangamonitor.db"

    # Настройки интерфейса
    window_width: int = 1200
    window_height: int = 800
    start_minimized: bool = False
    minimize_to_tray: bool = True

    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_config()

    def load_config(self):
        """Загрузка конфигурации из файла"""
        config_file = Path("config") / "default_config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                for key, value in file_config.items():
                    if hasattr(self, key):
                        setattr(self, key, value)

    def save_config(self):
        """Сохранение конфигурации в файл"""
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)

        config_data = {
            "app_name": self.app_name,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "auto_open_browser": self.auto_open_browser,
            "request_timeout": self.request_timeout,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "start_minimized": self.start_minimized,
            "minimize_to_tray": self.minimize_to_tray,
        }

        with open(config_dir / "default_config.json", 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)