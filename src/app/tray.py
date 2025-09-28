"""
Системный трей для MangaMonitor
"""

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QTimer, Qt  # Добавили импорт Qt
import os
import logging

logger = logging.getLogger(__name__)


class SystemTray:
    """Системный трей приложения"""

    def __init__(self, main_window, app):
        self.main_window = main_window
        self.app = app
        self.tray_icon = QSystemTrayIcon()
        self.setup_tray()

    def setup_tray(self):
        """Настройка системного трея"""
        # Создаем простую иконку
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)  # Теперь Qt определен
        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip("MangaMonitor - Читалка манги")

        # Создаем контекстное меню
        tray_menu = QMenu()

        show_action = QAction("Показать", self.tray_icon)
        show_action.triggered.connect(self.main_window.show)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        # Действия приложения
        search_action = QAction("Поиск манги", self.tray_icon)
        search_action.triggered.connect(self.show_and_search)
        tray_menu.addAction(search_action)

        popular_action = QAction("Популярное", self.tray_icon)
        popular_action.triggered.connect(self.show_popular)
        tray_menu.addAction(popular_action)

        tray_menu.addSeparator()

        quit_action = QAction("Выход", self.tray_icon)
        quit_action.triggered.connect(self.app.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)

        # Таймер для обновления уведомлений
        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(self.check_updates)
        self.notification_timer.start(300000)  # Проверка каждые 5 минут

    def on_tray_activated(self, reason):
        """Обработка активации иконки в трее"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.main_window.show()
            self.main_window.activateWindow()

    def show_and_search(self):
        """Показать окно и активировать поиск"""
        self.main_window.show()
        self.main_window.activateWindow()
        # Устанавливаем фокус на поле поиска
        if hasattr(self.main_window, 'search_input'):
            self.main_window.search_input.setFocus()

    def show_popular(self):
        """Показать популярную мангу"""
        self.main_window.show()
        self.main_window.activateWindow()
        # TODO: Реализовать загрузку популярной манги

    def check_updates(self):
        """Проверка обновлений (заглушка)"""
        # TODO: Реализовать проверку новых глав
        pass

    def show_notification(self, title, message):
        """Показать уведомление"""
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 5000)

    def show(self):
        """Показать иконку в трее"""
        self.tray_icon.show()

    def hide(self):
        """Скрыть иконку трея"""
        self.tray_icon.hide()