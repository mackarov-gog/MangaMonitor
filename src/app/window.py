"""
Главное окно приложения MangaMonitor
"""
"""
Главное окно приложения MangaMonitor
"""

import sys
import asyncio
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QPushButton, QListWidget,
                             QListWidgetItem, QLabel, QMessageBox, QTabWidget,
                             QSplitter, QScrollArea, QFrame, QProgressBar,
                             QComboBox, QCheckBox, QGroupBox, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QPixmap, QIcon, QFont, QPalette, QColor
from PyQt5.QtWebEngineWidgets import QWebEngineView
import aiohttp
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MangaItemWidget(QWidget):
    """Виджет для отображения элемента манги в списке"""

    def __init__(self, manga, parent=None):
        super().__init__(parent)
        self.manga = manga
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Обложка (заглушка)
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(60, 80)
        self.cover_label.setStyleSheet("""
            QLabel {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
            }
        """)
        self.cover_label.setAlignment(Qt.AlignCenter)

        # Загружаем обложку если есть URL
        if self.manga.cover_url and self.manga.cover_url.startswith('http'):
            # TODO: Реализовать загрузку изображений
            self.cover_label.setText("🖼️")
        else:
            self.cover_label.setText("📚")

        # Информация о манге
        info_layout = QVBoxLayout()

        self.title_label = QLabel(self.manga.title)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #e2e8f0;")
        self.title_label.setWordWrap(True)

        self.details_label = QLabel(
            f"{self.manga.source} • {self.manga.chapters_count} глав • {self.manga.status.value}")
        self.details_label.setStyleSheet("color: #a0aec0; font-size: 12px;")

        self.genres_label = QLabel(", ".join(self.manga.genres[:3]))
        self.genres_label.setStyleSheet("color: #718096; font-size: 11px;")
        self.genres_label.setWordWrap(True)

        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.details_label)
        info_layout.addWidget(self.genres_label)
        info_layout.addStretch()

        layout.addWidget(self.cover_label)
        layout.addLayout(info_layout)
        layout.addStretch()

        self.setLayout(layout)
        self.setFixedHeight(100)
        self.setStyleSheet("""
            MangaItemWidget {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 6px;
                margin: 2px;
            }
            MangaItemWidget:hover {
                background-color: #4a5568;
                border-color: #718096;
            }
        """)


class SearchWorker(QThread):
    """Поток для выполнения поиска манги"""

    search_finished = pyqtSignal(list)
    search_error = pyqtSignal(str)

    def __init__(self, parser_manager, query):
        super().__init__()
        self.parser_manager = parser_manager
        self.query = query

    def run(self):
        try:
            # Запускаем асинхронный поиск в отдельном event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def do_search():
                return await self.parser_manager.search_all(self.query)

            results = loop.run_until_complete(do_search())
            loop.close()

            self.search_finished.emit(results)

        except Exception as e:
            self.search_error.emit(str(e))


class MainWindow(QMainWindow):
    """Главное окно приложения MangaMonitor"""

    def __init__(self, config, parser_manager, web_server):
        super().__init__()
        self.config = config
        self.parser_manager = parser_manager
        self.web_server = web_server
        self.current_manga = None
        self.search_worker = None

        self.setup_ui()
        self.setup_styles()

        # Таймер для проверки статуса веб-сервера
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle(f"{self.config.app_name} v{self.config.version}")
        self.setGeometry(100, 100, self.config.window_width, self.config.window_height)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Заголовок
        title_layout = QHBoxLayout()
        title_label = QLabel("MangaMonitor")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #e2e8f0;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # Статус веб-сервера
        self.status_label = QLabel("🟢 API доступен")
        self.status_label.setStyleSheet("color: #68d391; font-size: 12px;")
        title_layout.addWidget(self.status_label)

        main_layout.addLayout(title_layout)

        # Поисковая панель
        search_group = QGroupBox("Поиск манги")
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите название манги для поиска...")
        self.search_input.returnPressed.connect(self.search_manga)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #4a5568;
                border-radius: 4px;
                background-color: #2d3748;
                color: #e2e8f0;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4299e1;
            }
        """)

        self.search_button = QPushButton("Поиск")
        self.search_button.clicked.connect(self.search_manga)
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #4299e1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3182ce;
            }
            QPushButton:pressed {
                background-color: #2b6cb0;
            }
        """)

        # Фильтр источников
        self.source_combo = QComboBox()
        self.source_combo.addItem("Все источники")
        for source in self.parser_manager.get_available_sources():
            self.source_combo.addItem(source)
        self.source_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #4a5568;
                border-radius: 4px;
                background-color: #2d3748;
                color: #e2e8f0;
                min-width: 120px;
            }
        """)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.source_combo)
        search_layout.addWidget(self.search_button)
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        # Сплиттер для разделения списка и деталей
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель - список результатов
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        self.results_label = QLabel("Результаты поиска:")
        self.results_label.setStyleSheet("color: #e2e8f0; font-weight: bold;")

        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.on_manga_selected)
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                outline: none;
            }
            QListWidget::item {
                border: none;
            }
        """)

        left_layout.addWidget(self.results_label)
        left_layout.addWidget(self.results_list)
        left_panel.setLayout(left_layout)

        # Правая панель - детали манги
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        self.details_label = QLabel("Выберите мангу для просмотра деталей")
        self.details_label.setStyleSheet("color: #a0aec0; font-size: 14px;")
        self.details_label.setAlignment(Qt.AlignCenter)

        # Табы для деталей
        self.tabs = QTabWidget()

        # Вкладка информации
        self.info_tab = QWidget()
        self.setup_info_tab()
        self.tabs.addTab(self.info_tab, "Информация")

        # Вкладка глав
        self.chapters_tab = QWidget()
        self.setup_chapters_tab()
        self.tabs.addTab(self.chapters_tab, "Главы")

        # Вкладка чтения
        self.reader_tab = QWidget()
        self.setup_reader_tab()
        self.tabs.addTab(self.reader_tab, "Чтение")

        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #4a5568;
                background-color: #2d3748;
            }
            QTabBar::tab {
                background-color: #4a5568;
                color: #e2e8f0;
                padding: 8px 16px;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #4299e1;
            }
            QTabBar::tab:hover:!selected {
                background-color: #718096;
            }
        """)

        right_layout.addWidget(self.details_label)
        right_layout.addWidget(self.tabs)
        right_panel.setLayout(right_layout)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])

        main_layout.addWidget(splitter)

        # Прогресс-бар для поиска
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #4a5568;
                border-radius: 4px;
                text-align: center;
                color: #e2e8f0;
            }
            QProgressBar::chunk {
                background-color: #4299e1;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        central_widget.setLayout(main_layout)

    def setup_info_tab(self):
        """Настройка вкладки информации о манге"""
        layout = QVBoxLayout()

        # Прокручиваемая область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout()

        # Заголовок и обложка
        header_layout = QHBoxLayout()

        self.manga_cover = QLabel()
        self.manga_cover.setFixedSize(200, 300)
        self.manga_cover.setStyleSheet("""
            QLabel {
                background-color: #4a5568;
                border: 1px solid #718096;
                border-radius: 6px;
            }
        """)
        self.manga_cover.setAlignment(Qt.AlignCenter)
        self.manga_cover.setText("Обложка\nне загружена")

        self.manga_title = QLabel()
        self.manga_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e2e8f0;")
        self.manga_title.setWordWrap(True)

        title_info_layout = QVBoxLayout()
        title_info_layout.addWidget(self.manga_title)
        title_info_layout.addStretch()

        header_layout.addWidget(self.manga_cover)
        header_layout.addLayout(title_info_layout)
        header_layout.addStretch()

        content_layout.addLayout(header_layout)

        # Детали
        details_group = QGroupBox("Детали")
        details_layout = QVBoxLayout()

        self.manga_description = QTextEdit()
        self.manga_description.setReadOnly(True)
        self.manga_description.setStyleSheet("""
            QTextEdit {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 8px;
            }
        """)

        self.manga_meta = QLabel()
        self.manga_meta.setStyleSheet("color: #a0aec0;")

        details_layout.addWidget(QLabel("Описание:"))
        details_layout.addWidget(self.manga_description)
        details_layout.addWidget(self.manga_meta)
        details_group.setLayout(details_layout)

        content_layout.addWidget(details_group)
        content_layout.addStretch()

        content.setLayout(content_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.info_tab.setLayout(layout)

    def setup_chapters_tab(self):
        """Настройка вкладки глав"""
        layout = QVBoxLayout()

        self.chapters_list = QListWidget()
        self.chapters_list.itemClicked.connect(self.on_chapter_selected)
        self.chapters_list.setStyleSheet("""
            QListWidget {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
            }
        """)

        layout.addWidget(QLabel("Список глав:"))
        layout.addWidget(self.chapters_list)

        self.chapters_tab.setLayout(layout)

    def setup_reader_tab(self):
        """Настройка вкладки чтения"""
        layout = QVBoxLayout()

        self.reader_label = QLabel("Выберите главу для чтения")
        self.reader_label.setStyleSheet("color: #a0aec0; font-size: 16px;")
        self.reader_label.setAlignment(Qt.AlignCenter)

        # Навигация
        nav_layout = QHBoxLayout()

        self.prev_button = QPushButton("← Предыдущая")
        self.prev_button.clicked.connect(self.prev_page)
        self.prev_button.setEnabled(False)

        self.next_button = QPushButton("Следующая →")
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)

        self.page_label = QLabel("Страница: - / -")
        self.page_label.setStyleSheet("color: #e2e8f0;")

        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_button)

        # Область просмотра
        self.reader_view = QWebEngineView()
        self.reader_view.setHtml("""
            <html>
                <body style="background-color: #2d3748; color: #e2e8f0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
                    <div style="text-align: center;">
                        <h1>Выберите главу для чтения</h1>
                        <p>Нажмите на главу в списке чтобы начать чтение</p>
                    </div>
                </body>
            </html>
        """)

        layout.addLayout(nav_layout)
        layout.addWidget(self.reader_view)

        self.reader_tab.setLayout(layout)

    def setup_styles(self):
        """Настройка стилей приложения"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a202c;
            }
            QWidget {
                background-color: #1a202c;
                color: #e2e8f0;
            }
            QGroupBox {
                color: #e2e8f0;
                font-weight: bold;
                border: 1px solid #4a5568;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #e2e8f0;
            }
        """)

    def search_manga(self):
        """Выполнение поиска манги"""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Ошибка", "Введите запрос для поиска")
            return

        # Показываем прогресс-бар
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Индикатор без определенного прогресса

        # Очищаем предыдущие результаты
        self.results_list.clear()
        self.results_label.setText(f"Поиск: {query}...")

        # Запускаем поиск в отдельном потоке
        self.search_worker = SearchWorker(self.parser_manager, query)
        self.search_worker.search_finished.connect(self.on_search_finished)
        self.search_worker.search_error.connect(self.on_search_error)
        self.search_worker.start()

    def on_search_finished(self, results):
        """Обработка завершения поиска"""
        self.progress_bar.setVisible(False)
        self.results_label.setText(f"Найдено манги: {len(results)}")

        # Отображаем результаты
        for manga in results:
            item_widget = MangaItemWidget(manga)
            item = QListWidgetItem(self.results_list)
            item.setSizeHint(item_widget.sizeHint())
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, item_widget)

    def on_search_error(self, error_message):
        """Обработка ошибки поиска"""
        self.progress_bar.setVisible(False)
        self.results_label.setText("Ошибка при поиске")
        QMessageBox.critical(self, "Ошибка поиска", f"Произошла ошибка при поиске: {error_message}")

    def on_manga_selected(self, item):
        """Обработка выбора манги из списка"""
        # Получаем виджет манги
        widget = self.results_list.itemWidget(item)
        if not widget:
            return

        self.current_manga = widget.manga
        self.show_manga_details(self.current_manga)

    def show_manga_details(self, manga):
        """Отображение детальной информации о манге"""
        self.details_label.setText(f"Детали: {manga.title}")

        # Обновляем информацию
        self.manga_title.setText(manga.title)
        self.manga_description.setText(manga.description or "Описание отсутствует")

        meta_text = f"""
        Источник: {manga.source}<br>
        Статус: {manga.status.value}<br>
        Глав: {manga.chapters_count}<br>
        Жанры: {', '.join(manga.genres)}<br>
        {f'Рейтинг: {manga.rating}' if manga.rating else ''}
        """
        self.manga_meta.setText(meta_text)

        # Загружаем главы
        self.load_chapters(manga.id)

    def load_chapters(self, manga_id):
        """Загрузка списка глав"""
        self.chapters_list.clear()
        self.chapters_list.addItem("Загрузка глав...")

        # TODO: Реализовать загрузку глав через парсер
        # Пока используем тестовые данные
        for i in range(1, 6):
            item = QListWidgetItem(f"Глава {i}")
            item.setData(Qt.UserRole, f"chapter_{i}")
            self.chapters_list.addItem(item)

        # Убираем элемент "Загрузка..."
        if self.chapters_list.count() > 1:
            self.chapters_list.takeItem(0)

    def on_chapter_selected(self, item):
        """Обработка выбора главы"""
        chapter_id = item.data(Qt.UserRole)
        self.reader_label.setText(f"Чтение: {item.text()}")

        # TODO: Реализовать загрузку страниц
        # Пока показываем заглушку
        html_content = f"""
        <html>
            <body style="background-color: #2d3748; color: #e2e8f0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; flex-direction: column;">
                <div style="text-align: center;">
                    <h1>{item.text()}</h1>
                    <p>Функция чтения в разработке</p>
                    <p>В будущем здесь будут отображаться страницы манги</p>
                </div>
            </body>
        </html>
        """
        self.reader_view.setHtml(html_content)

        # Активируем навигацию
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.page_label.setText("Страница: 1 / 1")

    def prev_page(self):
        """Переход к предыдущей странице"""
        # TODO: Реализовать навигацию по страницам
        pass

    def next_page(self):
        """Переход к следующей странице"""
        # TODO: Реализовать навигацию по страницам
        pass

    def update_status(self):
        """Обновление статуса веб-сервера"""
        try:
            # Проверяем доступность API
            import requests
            response = requests.get(f"http://{self.config.host}:{self.config.port}/api/health", timeout=2)
            if response.status_code == 200:
                self.status_label.setText("🟢 API доступен")
                self.status_label.setStyleSheet("color: #68d391; font-size: 12px;")
            else:
                self.status_label.setText("🟡 API не отвечает")
                self.status_label.setStyleSheet("color: #ed8936; font-size: 12px;")
        except:
            self.status_label.setText("🔴 API недоступен")
            self.status_label.setStyleSheet("color: #fc8181; font-size: 12px;")

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.config.minimize_to_tray:
            event.ignore()
            self.hide()
            # TODO: Показать уведомление в трее
            QMessageBox.information(self, "MangaMonitor", "Приложение свернуто в системный трей")
        else:
            # Останавливаем поиск если он выполняется
            if self.search_worker and self.search_worker.isRunning():
                self.search_worker.terminate()
                self.search_worker.wait()
            event.accept()