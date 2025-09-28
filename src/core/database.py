"""
Модуль для работы с базой данных
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from pathlib import Path

Base = declarative_base()


class Manga(Base):
    """Модель манги"""
    __tablename__ = "manga"

    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)  # Источник (mangalib, remanga, etc)
    source_id = Column(String(100), nullable=False)  # ID в источнике
    title = Column(String(500), nullable=False)
    description = Column(Text)
    cover_url = Column(String(500))
    status = Column(String(50))
    genres = Column(JSON)  # Список жанров
    chapters_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class Chapter(Base):
    """Модель главы"""
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True)
    manga_id = Column(Integer, nullable=False)
    source_chapter_id = Column(String(100), nullable=False)
    title = Column(String(500))
    chapter_number = Column(String(50))
    volume_number = Column(String(50))
    pages_count = Column(Integer, default=0)
    publish_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReadingProgress(Base):
    """Прогресс чтения"""
    __tablename__ = "reading_progress"

    id = Column(Integer, primary_key=True)
    manga_id = Column(Integer, nullable=False)
    chapter_id = Column(Integer, nullable=False)
    current_page = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    last_read = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class Bookmark(Base):
    """Закладки"""
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True)
    manga_id = Column(Integer, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# Глобальные переменные для подключения к БД
engine = None
async_session = None


async def init_database():
    """Инициализация базы данных"""
    global engine, async_session

    # Создаем папку data если не существует
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    database_url = f"sqlite+aiosqlite:///{data_dir}/mangamonitor.db"
    engine = create_async_engine(database_url, echo=False)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Получение сессии базы данных"""
    async with async_session() as session:
        yield session