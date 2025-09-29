#!/usr/bin/env python3
"""
MangaMonitor - Главный файл приложения
"""

import sys
import os
import asyncio
import logging
from pathlib import Path




# Добавляем src в путь для импортов
sys.path.append(str(Path(__file__).parent))



try:
    from core.config import AppConfig
    from core.database import init_database
    from core.parser_manager import ParserManager
    from web.server import WebServer
    from app.window import MainWindow
    from app.tray import SystemTray
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все модули созданы и зависимости установлены")
    sys.exit(1)



class MangaMonitor:
    """Основной класс приложения"""

    def __init__(self):
        self.config = AppConfig()
        self.parser_manager = ParserManager(self.config.model_dump())
        self.parser_manager = ParserManager()
        self.web_server = WebServer(self.config)
        self.main_window = None
        self.tray_icon = None
        self.setup_logging()


    def setup_logging(self):
        """Настройка системы логирования"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.DEBUG if self.config.debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "mangamonitor.log", encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("MangaMonitor")

    async def initialize(self):
        """Инициализация приложения"""
        self.logger.info("Инициализация MangaMonitor...")

        # Инициализация базы данных
        await init_database()

        # Регистрация всех парсеров
        self.parser_manager.register_all_parsers()
        self.logger.info(f"Зарегистрировано парсеров: {len(self.parser_manager.parsers)}")

        # Запуск веб-сервера в фоновой задаче
        self.server_task = asyncio.create_task(self.web_server.start())
        self.logger.info(f"Веб-сервер запущен на http://{self.config.host}:{self.config.port}")

        self.logger.info("MangaMonitor инициализирован")

    def create_ui(self):
        """Создание пользовательского интерфейса"""
        try:
            from PyQt5.QtWidgets import QApplication
            from qasync import QEventLoop

            self.app = QApplication(sys.argv)
            self.app.setApplicationName("MangaMonitor")
            self.app.setApplicationVersion("1.0.0")
            self.app.setQuitOnLastWindowClosed(False)

            # Главное окно
            self.main_window = MainWindow(self.config, self.parser_manager, self.web_server)

            # Системный трей
            self.tray_icon = SystemTray(self.main_window, self.app)
            self.tray_icon.show()

            return self.app
        except Exception as e:
            self.logger.error(f"Ошибка создания UI: {e}")
            raise

    async def run(self):
        """Запуск приложения"""
        try:
            await self.initialize()

            # Qt требует запуска в основном потоке
            from PyQt5.QtCore import QTimer
            from qasync import QEventLoop

            app = self.create_ui()
            loop = QEventLoop(app)
            asyncio.set_event_loop(loop)

            # Таймер для асинхронных задач
            timer = QTimer()
            timer.timeout.connect(lambda: None)
            timer.start(100)

            self.logger.info("Запуск пользовательского интерфейса...")

            with loop:
                # Показываем главное окно если не настроен запуск в трее
                if not self.config.start_minimized:
                    self.main_window.show()
                else:
                    if hasattr(self.tray_icon, 'show_notification'):
                        self.tray_icon.show_notification(
                            "MangaMonitor запущен",
                            "Приложение работает в фоновом режиме"
                        )

                # Запускаем event loop
                loop.run_forever()

        except Exception as e:
            self.logger.error(f"Ошибка при запуске: {e}")
            raise

    async def shutdown(self):
        """Корректное завершение работы"""
        self.logger.info("Завершение работы MangaMonitor...")

        # Остановка парсеров
        await self.parser_manager.close_all()

        # Остановка веб-сервера
        if hasattr(self, 'server_task'):
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass

        # Скрытие трея
        if self.tray_icon:
            self.tray_icon.hide()

        self.logger.info("MangaMonitor завершен")


async def main():
    """Точка входа приложения"""
    monitor = None
    try:
        monitor = MangaMonitor()
        await monitor.run()

    except KeyboardInterrupt:
        print("\nПриложение завершено пользователем")
    except Exception as e:
        print(f"Ошибка при запуске: {e}")
        if monitor:
            await monitor.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    # Обработка Ctrl+C
    import signal

    signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(main()))

    # Запуск приложения
    asyncio.run(main())