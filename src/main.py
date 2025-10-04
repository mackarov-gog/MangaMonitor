# src/main.py
import asyncio
import os
import sys
from contextlib import AsyncExitStack
from typing import Optional
1
BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.core.parser_manager import get_parser, list_parsers, get_all_parsers, search_all_parsers
from src.core.database import init_db, ensure_manga, ensure_chapter, save_page, mark_chapter_saved
from urllib.parse import urlparse

# Константы для специальных команд
BACK_COMMAND = "назад"
EXIT_COMMAND = "выход"
CANCEL_COMMAND = "отмена"


def is_special_command(input_str: str) -> bool:
    """Проверяет, является ли ввод специальной командой"""
    return input_str.lower() in [BACK_COMMAND, EXIT_COMMAND, CANCEL_COMMAND]


def handle_special_command(input_str: str) -> str:
    """Обрабатывает специальные команды"""
    cmd = input_str.lower()
    if cmd == BACK_COMMAND:
        return "back"
    elif cmd in [EXIT_COMMAND, CANCEL_COMMAND]:
        return "exit"
    return "continue"


def get_int_input(prompt: str, min_val: int, max_val: int, default: int = None, allow_back: bool = True) -> Optional[
    int]:
    """Безопасный ввод целого числа с проверкой диапазона и поддержкой отмены"""
    help_text = " (или 'назад' для возврата, 'выход' для завершения)" if allow_back else ""

    while True:
        try:
            user_input = input(prompt + help_text + ": ").strip()

            # Проверка специальных команд
            if is_special_command(user_input):
                command = handle_special_command(user_input)
                return command

            if not user_input and default is not None:
                return default

            value = int(user_input)
            if min_val <= value <= max_val:
                return value
            else:
                print(f"Введите число от {min_val} до {max_val}")
        except ValueError:
            print("Пожалуйста, введите целое число")


def get_yes_no_input(prompt: str, default: bool = False, allow_back: bool = True) -> Optional[bool]:
    """Безопасный ввод да/нет с поддержкой отмены"""
    help_text = " (или 'назад' для возврата, 'выход' для завершения)" if allow_back else ""

    while True:
        user_input = input(prompt + help_text + ": ").strip().lower()

        # Проверка специальных команд
        if is_special_command(user_input):
            return handle_special_command(user_input)

        if not user_input:
            return default

        if user_input in ['y', 'yes', 'да', 'д']:
            return True
        elif user_input in ['n', 'no', 'нет', 'н']:
            return False
        else:
            print("Пожалуйста, введите 'y' (да) или 'n' (нет)")


def get_string_input(prompt: str, allow_empty: bool = False, allow_back: bool = True) -> Optional[str]:
    """Безопасный ввод строки с поддержкой отмены"""
    help_text = " (или 'назад' для возврата, 'выход' для завершения)" if allow_back else ""

    while True:
        user_input = input(prompt + help_text + ": ").strip()

        # Проверка специальных команд
        if is_special_command(user_input):
            return handle_special_command(user_input)

        if not user_input and not allow_empty:
            print("Пожалуйста, введите не пустую строку")
            continue

        return user_input


def display_parsers_menu(parsers_list):
    """Показать меню выбора парсеров"""
    print("\nДоступные парсеры:")
    for i, parser_name in enumerate(parsers_list, 1):
        print(f"{i} - {parser_name}")
    return len(parsers_list)


async def run():
    init_db()
    available_parsers = list_parsers()

    # Главный цикл программы
    while True:
        # Выбор режима поиска
        print("\n" + "=" * 50)
        print("Менеджер манги")
        print("=" * 50)
        print("\nРежимы поиска:")
        print("1 - Поиск по всем сайтам")
        print("2 - Поиск по конкретному сайту")
        print("0 - Выход из программы")

        mode_choice = get_int_input("Выберите режим", 0, 2, allow_back=False)

        if mode_choice == "exit" or mode_choice == 0:
            print("Выход из программы.")
            return

        if mode_choice == "back":
            continue  # На главный цикл

        async with AsyncExitStack() as stack:
            if mode_choice == 1:
                # Поиск по всем сайтам
                while True:
                    q = get_string_input("Введите название для поиска", allow_empty=False, allow_back=True)

                    if q == "exit":
                        print("Выход из программы.")
                        return
                    elif q == "back":
                        break  # Вернуться к выбору режима

                    parsers = get_all_parsers()
                    # Добавляем все парсеры в контекст
                    for parser in parsers:
                        await stack.enter_async_context(parser)

                    print(f"Поиск по {len(parsers)} сайтам...")
                    results = await search_all_parsers(q, parsers=parsers, max_pages=1)

                    if not results:
                        print("Ничего не найдено. Попробуйте другой запрос.")
                        continue

                    # Обработка результатов поиска
                    if await handle_search_results(results, stack, mode_choice):
                        break  # Успешный выбор, выходим из цикла поиска
                    # Иначе продолжаем поиск с тем же режимом

            elif mode_choice == 2:
                # Поиск по конкретному сайту
                while True:
                    num_parsers = display_parsers_menu(available_parsers)
                    print("0 - Назад к выбору режима")

                    parser_choice = get_int_input("Выберите парсер", 0, num_parsers, allow_back=False)

                    if parser_choice == "exit":
                        print("Выход из программы.")
                        return
                    elif parser_choice == 0:
                        break  # Назад к выбору режима

                    parser_name = available_parsers[parser_choice - 1]

                    # Ввод поискового запроса
                    while True:
                        q = get_string_input("Введите название для поиска", allow_empty=False, allow_back=True)

                        if q == "exit":
                            print("Выход из программы.")
                            return
                        elif q == "back":
                            break  # Назад к выбору парсера

                        parser = get_parser(parser_name)
                        if parser is None:
                            print(f"Парсер {parser_name} не найден")
                            break

                        parser_inst = await stack.enter_async_context(parser)
                        print(f"Поиск на {parser_name}...")
                        results = await parser_inst.search_manga(q, max_pages=2)

                        if not results:
                            print("Ничего не найдено. Попробуйте другой запрос.")
                            continue

                        # Обработка результатов поиска
                        if await handle_search_results(results, stack, mode_choice, parser_inst):
                            return  # Успешное завершение работы с главой
                        # Иначе продолжаем поиск с тем же парсером

                    # Если вышли из внутреннего цикла, продолжаем внешний (выбор парсера)


async def handle_search_results(results, stack, mode_choice, parser_inst=None):
    """Обработка результатов поиска и навигация по манге/главам"""
    # Показываем результаты
    max_results_to_show = min(20, len(results))
    print(f"\nНайдено результатов: {len(results)}")
    for i, r in enumerate(results[:max_results_to_show], 1):
        parser_name = r.get('parser', 'unknown')
        rating = r.get('rating', 'N/A')
        similarity = r.get('similarity', 0)
        year = r.get('year', 'N/A')
        print(f"{i}. {r['title']} ({year}) ⭐ {rating} [{similarity}%] -> {parser_name}")
    print("0 - Назад к поиску")

    # Выбор манги
    while True:
        manga_choice = get_int_input(
            f"Выберите мангу (1-{max_results_to_show})",
            0, max_results_to_show, default=1
        )

        if manga_choice == "exit":
            print("Выход из программы.")
            return True
        elif manga_choice == "back" or manga_choice == 0:
            return False  # Назад к поиску

        chosen = results[manga_choice - 1]

        # Определяем парсер для выбранной манги
        if mode_choice == 1:
            parser_name = chosen.get('parser')
            parser = get_parser(parser_name)()
            await stack.enter_async_context(parser)
        else:
            parser = parser_inst

        print(f"\nЗагружаем информацию о '{chosen['title']}'...")
        info = await parser.get_manga_info(chosen["url"])

        # Вывод информации о манге
        print(f"\n=== {info.get('title')} ===")
        if info.get('eng_name'):
            print(f"Английское название: {info.get('eng_name')}")
        if info.get('orig_name'):
            print(f"Оригинальное название: {info.get('orig_name')}")
        if info.get('author'):
            print(f"Автор: {info.get('author')}")
        if info.get('year'):
            print(f"Год: {info.get('year')}")
        if info.get('category'):
            print(f"Категория: {info.get('category')}")
        if info.get('genres'):
            print(f"Жанры: {', '.join(info.get('genres', []))}")
        if info.get('description'):
            desc = info.get('description')
            print(f"Описание: {desc[:200]}{'...' if len(desc) > 200 else ''}")

        chapters = info.get("chapters", [])
        if not chapters:
            print("Глав нет.")
            print("Нажмите Enter чтобы вернуться к выбору манги...")
            input()
            continue  # Вернуться к выбору манги

        # Выбор главы
        while True:
            max_chapters_to_show = min(15, len(chapters))
            print(f"\nДоступные главы ({len(chapters)}):")
            for i, ch in enumerate(chapters[:max_chapters_to_show], 1):
                date_str = f" ({ch.get('date')})" if ch.get('date') else ""
                print(f"{i}. {ch.get('title')}{date_str}")
            print("0 - Назад к выбору манги")

            chapter_choice = get_int_input(
                f"Выберите главу (1-{max_chapters_to_show})",
                0, max_chapters_to_show, default=1
            )

            if chapter_choice == "exit":
                print("Выход из программы.")
                return True
            elif chapter_choice == "back" or chapter_choice == 0:
                break  # Назад к выбору манги

            chapter = chapters[chapter_choice - 1]

            # Сохраняем в БД
            manga_id = ensure_manga(info.get("title"), chosen["url"])
            chapter_id = ensure_chapter(manga_id, chapter.get("title"), chapter.get("url"))

            print("Получаем ссылки на изображения...")
            images = await parser.get_chapter_images(chapter.get("url"))
            if not images:
                print("Не найдено изображений.")
                print("Нажмите Enter чтобы продолжить...")
                input()
                continue  # Вернуться к выбору главы

            print(f"Найдено {len(images)} изображений")

            # Сохраняем ссылки в БД
            for idx, img_url in enumerate(images, 1):
                save_page(chapter_id, idx, img_url, None)

            # Предлагаем скачать
            download_choice = get_yes_no_input("Скачать главу локально? (y/N)", default=False)

            if download_choice == "exit":
                print("Выход из программы.")
                return True
            elif download_choice == "back":
                continue  # Назад к выбору главы

            if download_choice:
                def slug_from_url(u):
                    p = urlparse(u).path.strip("/").replace("/", "_")
                    return p or "chapter"

                manga_slug = slug_from_url(chosen["url"])
                chap_slug = slug_from_url(chapter.get("url"))
                out_dir = os.path.join(ROOT, "data", "downloads", manga_slug, chap_slug)

                print(f"Скачиваем в {out_dir}...")
                saved_files = await parser.download_chapter(chapter.get("url"), out_dir=out_dir)

                # Обновляем пути в БД
                for i, file_path in enumerate(saved_files, 1):
                    save_page(chapter_id, i, images[i - 1] if i - 1 < len(images) else "", file_path)

                mark_chapter_saved(chapter_id)
                print(f"Скачано {len(saved_files)} файлов")

                # После успешного скачивания предлагаем продолжить
                print("\nГлава успешно скачана!")
                continue_choice = get_yes_no_input("Продолжить работу с этой мангой?", default=True)

                if continue_choice == "exit":
                    print("Выход из программы.")
                    return True
                elif continue_choice == "back" or not continue_choice:
                    break  # Назад к выбору манги
                # Иначе продолжаем с выбором главы этой манги

    return False


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем.")
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")
    finally:
        print("Работа программы завершена.")