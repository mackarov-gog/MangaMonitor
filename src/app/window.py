import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QListWidget, QLabel, QHBoxLayout, QTextEdit
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import asyncio

from chapter_parser import get_chapter_images, download_chapter


class MangaMonitorUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MangaMonitor")
        self.setGeometry(200, 100, 900, 600)

        # Основной layout
        layout = QVBoxLayout()

        # Список манги (пока заглушка)
        self.manga_list = QListWidget()
        self.manga_list.addItem("Свадьба втроём")
        self.manga_list.addItem("Любовь за решёткой")
        layout.addWidget(QLabel("📚 Моя манга:"))
        layout.addWidget(self.manga_list)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_open = QPushButton("Открыть главу")
        self.btn_download = QPushButton("Скачать главу")
        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_download)
        layout.addLayout(btn_layout)

        # Поле просмотра (будет показывать картинки или текст)
        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        layout.addWidget(self.viewer)

        self.setLayout(layout)

        # Привязка действий
        self.btn_open.clicked.connect(self.open_chapter)
        self.btn_download.clicked.connect(self.download_chapter)

    def open_chapter(self):
        # пример: берём тестовую ссылку
        chapter_url = "https://1.seimanga.me/svadba_vtroem/vol1/2?mtr=true"
        images = asyncio.run(get_chapter_images(chapter_url))
        self.viewer.setText("\n".join(images))  # пока просто список ссылок

    def download_chapter(self):
        chapter_url = "https://1.seimanga.me/svadba_vtroem/vol1/2?mtr=true"
        asyncio.run(download_chapter(chapter_url, out_dir="downloads/svadba_vtroem"))
        self.viewer.setText("✅ Глава скачана в папку downloads/")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MangaMonitorUI()
    window.show()
    sys.exit(app.exec())