# src/main.py
import asyncio
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.core.parser_manager import get_parser, list_parsers
from src.core.database import init_db, ensure_manga, ensure_chapter, save_page, mark_chapter_saved
from urllib.parse import urlparse

async def run():
    init_db()
    print("Доступные парсеры:", list_parsers())
    parser = get_parser("seimanga")
    if parser is None:
        print("Parser not found")
        return

    q = input("Введите название для поиска: ").strip()
    if not q:
        print("Пустой запрос, выход.")
        return

    # используем контекстный менеджер, чтобы сессия гарантированно закрывалась
    async with parser:
        results = await parser.search(q, max_pages=2000)
        if not results:
            print("Ничего не найдено.")
            return

        for i, r in enumerate(results, 1):
            print(f"{i}. {r.get('title')} — {r.get('url')}")

        sel = int(input(f"Выберите мангу (1-{len(results)}): ").strip() or "1") - 1
        sel = max(0, min(sel, len(results)-1))
        chosen = results[sel]

        print("Получаем инфо...")
        info = await parser.get_manga_info(chosen["url"])
        print("Title:", info.get("title"))
        print("Desc:", (info.get("description") or "")[:300])
        chapters = info.get("chapters", [])
        if not chapters:
            print("Глав нет.")
            return

        for i, ch in enumerate(chapters, 1):
            print(f"{i}. {ch.get('title')} — {ch.get('url')}")

        selc = int(input(f"Выберите главу (1-{len(chapters)}): ").strip() or "1") - 1
        selc = max(0, min(selc, len(chapters)-1))
        chapter = chapters[selc]

        # Сохраним в БД
        manga_id = ensure_manga(info.get("title"), chosen["url"])
        chapter_id = ensure_chapter(manga_id, chapter.get("title"), chapter.get("url"))

        print("Парсим страницы главы (ссылки на картинки)...")
        images = await parser.get_chapter_images(chapter.get("url"))
        if not images:
            print("Не найдено изображений.")
            return

        print(f"Найдено {len(images)} изображений. Первые 5:")
        for idx, im in enumerate(images[:5], 1):
            print(f"{idx}. {im}")
            save_page(chapter_id, idx, im, None)

        dl = input("Скачать главу локально? (y/N): ").strip().lower()
        if dl == "y":
            def slug_from_url(u):
                p = urlparse(u).path.strip("/").replace("/", "_")
                return p or "chapter"

            manga_slug = slug_from_url(chosen["url"])
            chap_slug = slug_from_url(chapter.get("url"))
            out_dir = os.path.join(ROOT, "data", "downloads", manga_slug, chap_slug)

            saved = await parser.download_chapter(chapter.get("url"), out_dir=out_dir)
            for i, path in enumerate(saved, 1):
                save_page(chapter_id, i, images[i-1] if i-1 < len(images) else "", path)
            mark_chapter_saved(chapter_id)
            print(f"Скачано {len(saved)} файлов в {out_dir}")

    print("Готово.")

if __name__ == "__main__":
    asyncio.run(run())
