# src/web/server.py
import os
import asyncio
from urllib.parse import urlparse, quote
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response
import aiohttp

from src.core.database import (
    init_db, ensure_manga, ensure_chapter,
    save_page, mark_chapter_saved, get_manga_list
)
from src.core.parser_manager import get_parser, get_parser_by_url, get_all_parsers, search_all_parsers

app = FastAPI(title="MangaMonitor API")

# Инициализация базы данных
init_db()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
templates = Jinja2Templates(directory="src/web/templates")


@app.get("/")
def root():
    return {"message": "MangaMonitor API работает. Перейдите на /docs для документации."}



@app.get("/api/proxy")
async def proxy_image(url: str):
    """Прокси изображений с Desu.city для обхода защиты Referer"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Referer": "https://desu.city/",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            content = await resp.read()
            return Response(content=content, media_type=resp.headers.get("Content-Type", "image/jpeg"))



@app.get("/api/parsers")
def list_parsers():
    """Вернуть список доступных парсеров"""
    from src.core.parser_manager import list_parsers as get_parsers
    return {"parsers": get_parsers()}


@app.get("/api/manga")
def list_manga():
    """Вернуть список манги из базы"""
    return {"manga": get_manga_list()}


@app.get("/api/search")
async def search(
        q: str = Query(..., description="Название манги"),
        parser: str = Query("all", description="Парсер (all, seimanga, selfmanga, etc)"),
        max_pages: int = Query(1, description="Количество страниц для поиска")
):
    """Поиск манги через парсер(ы)"""
    try:
        if parser == "all":
            # Поиск по всем парсерам
            parsers = get_all_parsers()
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(p.search_manga(q, max_pages=max_pages)) for p in parsers]

            # Собираем все результаты
            all_results = []
            for task in tasks:
                try:
                    results = task.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"Ошибка при поиске: {e}")

            # Сортируем по релевантности
            all_results.sort(key=lambda x: (x.get("similarity", 0), x.get("rating", 0)), reverse=True)
            return {"results": all_results}
        else:
            # Поиск через конкретный парсер
            parser_obj = get_parser(parser)
            if parser_obj is None:
                raise HTTPException(status_code=400, detail=f"Парсер '{parser}' не найден")

            async with parser_obj:
                results = await parser_obj.search_manga(q, max_pages=max_pages)
            return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске: {str(e)}")


@app.get("/api/info")
async def manga_info(url: str):
    """Информация о выбранной манге (название, описание, главы)"""
    try:
        parser = get_parser_by_url(url)
        if parser is None:
            raise HTTPException(status_code=400, detail="Не удалось определить подходящий парсер для URL")

        async with parser:
            info = await parser.get_manga_info(url)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении информации: {str(e)}")


@app.get("/api/chapter")
async def chapter_images(url: str, index: int = None):
    """
    API для получения изображений главы:
    - без index → вернёт список картинок
    - с index → вернёт одну картинку (номер начинается с 1)
    """
    try:
        parser = get_parser_by_url(url)
        if parser is None:
            raise HTTPException(status_code=400, detail="Не удалось определить подходящий парсер для URL")

        async with parser:
            images = await parser.get_chapter_images(url)
            images = [f"/api/proxy?url={img}" for img in images]

        if index is not None:
            if 1 <= index <= len(images):
                return {
                    "image": images[index - 1],
                    "index": index,
                    "total": len(images),
                    "parser": parser.name
                }
            else:
                return {
                    "error": "Index out of range",
                    "total": len(images),
                    "available_range": f"1-{len(images)}"
                }

        return {
            "images": images,
            "total": len(images),
            "parser": parser.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении изображений: {str(e)}")


@app.post("/api/download")
async def download_chapter(manga_url: str, chapter_url: str):
    """Скачивание главы локально + сохранение в БД"""
    try:
        parser = get_parser_by_url(chapter_url)
        if parser is None:
            raise HTTPException(status_code=400, detail="Не удалось определить подходящий парсер для URL")

        async with parser:
            # Получаем информацию о манге
            info = await parser.get_manga_info(manga_url)
            manga_id = ensure_manga(info.get("title"), manga_url)

            # Ищем выбранную главу
            chap = None
            for c in info.get("chapters", []):
                if c["url"] == chapter_url:
                    chap = c
                    break

            if chap is None:
                raise HTTPException(status_code=404, detail="Глава не найдена")

            chapter_id = ensure_chapter(manga_id, chap["title"], chap["url"])

            # Получаем изображения
            images = await parser.get_chapter_images(chapter_url)

            # Путь для сохранения
            def slug_from_url(u):
                p = urlparse(u).path.strip("/").replace("/", "_")
                return p or "chapter"

            manga_slug = slug_from_url(manga_url)
            chap_slug = slug_from_url(chapter_url)
            out_dir = os.path.join("data", "downloads", manga_slug, chap_slug)
            os.makedirs(out_dir, exist_ok=True)

            # Скачиваем
            saved = await parser.download_chapter(chapter_url, out_dir=out_dir)

            # Сохраняем страницы в БД
            for i, path in enumerate(saved, 1):
                img_url = images[i - 1] if i - 1 < len(images) else ""
                save_page(chapter_id, i, img_url, path)

            mark_chapter_saved(chapter_id)

        return {
            "status": "ok",
            "saved_files": saved,
            "total_files": len(saved),
            "parser": parser.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при скачивании: {str(e)}")


# HTML интерфейсы
@app.get("/search/view", response_class=HTMLResponse)
async def search_view(
        q: str = "",
        parser: str = "all",
        max_pages: int = 100
):
    """Веб-интерфейс для поиска манги"""
    results = []
    error_message = None
    if q:
        try:
            if parser == "all":
                parsers = get_all_parsers()
                async with asyncio.TaskGroup() as tg:
                    tasks = [tg.create_task(p.search_manga(q, max_pages=max_pages)) for p in parsers]

                for task in tasks:
                    try:
                        results.extend(task.result())
                    except Exception as e:
                        print(f"Ошибка поиска: {e}")

                results.sort(key=lambda x: (x.get("similarity", 0), x.get("rating", 0)), reverse=True)
            else:
                parser_obj = get_parser(parser)
                if parser_obj:
                    async with parser_obj:
                        results = await parser_obj.search_manga(q, max_pages=max_pages)
        except Exception as e:
            error_message = f"Ошибка поиска: {str(e)}"

    available_parsers = ["all"] + [p.name for p in get_all_parsers()]

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Поиск MangaMonitor</title>
        <style>
            body {{ background:#111; color:#eee; font-family:sans-serif; margin:0; padding:20px; }}
            h1 {{ color:#6cf; text-align:center; }}
            .search-form {{ 
                background: #1a1a1a; 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px;
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                align-items: end;
            }}
            .form-group {{ display: flex; flex-direction: column; }}
            label {{ color: #6cf; margin-bottom: 5px; font-size: 14px; }}
            input, select, button {{
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #444;
                background: #222;
                color: #eee;
                font-size: 14px;
            }}
            button {{
                background: #2a2a2a;
                cursor: pointer;
                border: 1px solid #6cf;
            }}
            button:hover {{ background: #333; }}
            .results {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; }}
            .card {{
                background: #1a1a1a;
                padding: 20px;
                border-radius: 12px;
                border-left: 4px solid #6cf;
                transition: all 0.3s ease;
                text-decoration: none;
                display: block;
                color: inherit;
                cursor: pointer;
            }}
            .card:hover {{
                background: #222;
                transform: translateY(-5px);
                box-shadow: 0 8px 20px rgba(0,0,0,0.3);
                border-left: 4px solid #8df;
            }}
            .card h3 {{ 
                margin: 0 0 12px 0; 
                color: #6cf; 
                font-size: 18px;
                line-height: 1.4;
            }}
            .card .meta {{ 
                color: #bbb; 
                font-size: 14px; 
                margin-bottom: 15px;
                line-height: 1.5;
            }}
            .card .parser {{ 
                display: inline-block; 
                background: #333; 
                padding: 4px 10px; 
                border-radius: 15px; 
                font-size: 12px; 
                color: #6cf;
                margin-bottom: 10px;
            }}
            .card .open-link {{
                display: inline-block;
                color: #8df;
                font-size: 14px;
                text-decoration: none;
                border: 1px solid #6cf;
                padding: 6px 12px;
                border-radius: 5px;
                transition: all 0.2s ease;
            }}
            .card .open-link:hover {{
                background: #6cf;
                color: #111;
            }}
            .error {{ color: #f66; background: #2a1a1a; padding: 10px; border-radius: 5px; }}
            .no-results {{ 
                text-align: center; 
                color: #888; 
                font-size: 18px; 
                margin: 40px 0;
                grid-column: 1 / -1;
            }}
            .results-count {{
                color: #6cf;
                margin: 20px 0;
                font-size: 18px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>Поиск манги</h1>

        <form method="get" action="/search/view" class="search-form">
            <div class="form-group">
                <label for="q">Название манги:</label>
                <input type="text" id="q" name="q" value="{q}" placeholder="Введите название..." required>
            </div>

            <div class="form-group">
                <label for="parser">Парсер:</label>
                <select id="parser" name="parser">
    """

    for p in available_parsers:
        selected = "selected" if p == parser else ""
        html += f'<option value="{p}" {selected}>{p}</option>'

    html += f"""
                </select>
            </div>



            <button type="submit">Искать</button>
        </form>
    """

    # Добавляем отображение количества найденных манг
    if q:
        if error_message:
            html += f'<div class="error">{error_message}</div>'
        else:
            html += f'<div class="results-count">Найдено манг: {len(results)}</div>'

    html += '<div class="results">'

    if q and not results and not error_message:
        html += f'<div class="no-results">По запросу "{q}" ничего не найдено</div>'

    for item in results:
        parser_badge = f'<span class="parser">{item.get("parser", "unknown")}</span>'
        rating = item.get('rating', 'N/A')
        year = item.get('year', 'N/A')


        html += f"""
        <a class='card' href='/manga/view?url={quote(item['url'], safe='')}'>
            {parser_badge}
            <h3>{item['title']}</h3>
            <div class='meta'>
                <div><strong>Рейтинг:</strong> {rating}</div>
                <div><strong>Год:</strong> {year}</div>
            </div>
            <span class="open-link">Открыть →</span>
        </a>
        """

    html += "</div></body></html>"
    return HTMLResponse(html)


@app.get("/manga/view", response_class=HTMLResponse)
async def manga_view(url: str):
    """Веб-интерфейс для просмотра информации о манге и глав"""
    try:
        parser = get_parser_by_url(url)
        if parser is None:
            return HTMLResponse(f"<html><body>Не удалось определить парсер для URL: {url}</body></html>")

        async with parser:
            info = await parser.get_manga_info(url)
    except Exception as e:
        return HTMLResponse(f"<html><body>Ошибка: {str(e)}</body></html>")

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{info['title']}</title>
        <style>
            body {{ background:#111; color:#eee; font-family:sans-serif; margin:0; padding:20px; }}
            .container {{ max-width:900px; margin:0 auto; }}
            h1 {{ color:#6cf; }}
            .meta {{ color: #888; margin: 10px 0; }}
            .description {{ line-height:1.6; margin:20px 0; padding: 15px; background: #1a1a1a; border-radius: 8px; }}
            h2 {{ margin-top:30px; color:#6cf; border-bottom: 1px solid #333; padding-bottom: 10px; }}
            .chapters {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap:12px; }}
            .chapter {{
                background:#1a1a1a;
                padding:12px;
                border-radius:8px;
                border-left: 3px solid #6cf;
            }}
            .chapter:hover {{ background:#222; }}
            .chapter a {{ color:#6cf; text-decoration:none; font-size:16px; display: block; }}
            .chapter a:hover {{ text-decoration:underline; }}
            .chapter .date {{ color: #666; font-size: 12px; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{info['title']}</h1>
            <div class="meta">
    """

    if info.get('eng_name'):
        html += f"<div><strong>Английское название:</strong> {info['eng_name']}</div>"
    if info.get('orig_name'):
        html += f"<div><strong>Оригинальное название:</strong> {info['orig_name']}</div>"
    if info.get('author'):
        html += f"<div><strong>Автор:</strong> {info['author']}</div>"
    if info.get('year'):
        html += f"<div><strong>Год:</strong> {info['year']}</div>"
    if info.get('category'):
        html += f"<div><strong>Категория:</strong> {info['category']}</div>"
    if info.get('genres'):
        html += f"<div><strong>Жанры:</strong> {', '.join(info['genres'])}</div>"

    html += f"""
            </div>
            <div class="description">
                {info.get('description', 'Описание отсутствует')}
            </div>
            <h2>Главы ({len(info.get('chapters', []))})</h2>
            <div class="chapters">
    """

    for chap in info.get("chapters", []):
        date_html = f'<div class="date">{chap["date"]}</div>' if chap.get("date") else ""
        html += f"""
        <div class='chapter'>
            <a href='/chapter/view?url={quote(chap['url'], safe='')}'>{chap['title']}</a>
            {date_html}
        </div>
        """

    html += "</div></div></body></html>"
    return HTMLResponse(html)


@app.get("/chapter/view", response_class=HTMLResponse)
async def chapter_view(url: str):
    """Веб-читалка манги"""
    safe_url = quote(url, safe="")

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Читалка MangaMonitor</title>
        <style>
            body {{
                background: #111;
                color: #eee;
                margin: 0;
                font-family: sans-serif;
                overflow-x: hidden;
            }}
            .header {{
                background: #1a1a1a;
                padding: 15px;
                text-align: center;
                border-bottom: 1px solid #333;
                position: sticky;
                top: 0;
                z-index: 100;
            }}
            h1 {{
                color: #6cf;
                margin: 0;
                font-size: 18px;
            }}
            .reader-container {{
                max-width: 100%;
                margin: 0 auto;
                padding: 20px;
                text-align: center;
            }}
            img {{
                max-width: 100%;
                height: auto;
                margin: 10px auto;
                display: block;
                border-radius: 8px;
                transition: transform 0.2s ease;
                transform-origin: top center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            }}
            .controls {{
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                display: flex;
                justify-content: center;
                gap: 15px;
                align-items: center;
                background: rgba(0,0,0,0.9);
                padding: 15px 0;
                border-top: 1px solid #444;
                backdrop-filter: blur(10px);
            }}
            button {{
                background: #222;
                color: #eee;
                border: 1px solid #444;
                padding: 10px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.2s;
            }}
            button:hover {{
                background: #333;
                border-color: #6cf;
            }}
            button:disabled {{
                opacity: 0.4;
                cursor: not-allowed;
            }}
            #counter {{
                color: #6cf;
                font-weight: bold;
                min-width: 80px;
                text-align: center;
            }}
            .zoom-controls {{
                display: flex;
                gap: 8px;
                margin-left: 20px;
            }}
            .loading {{
                color: #6cf;
                font-size: 18px;
                text-align: center;
                padding: 50px;
            }}
            @media (max-width: 768px) {{
                .controls {{
                    flex-wrap: wrap;
                    gap: 10px;
                }}
                button {{
                    padding: 8px 12px;
                    font-size: 12px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Читалка MangaMonitor</h1>
        </div>

        <div class="reader-container">
            <div id="loading" class="loading">Загрузка...</div>
            <img id="page" style="display: none;" />
        </div>

        <div class="controls">
            <button id="prev" onclick="prevPage()">⬅ Назад</button>
            <span id="counter">- / -</span>
            <button id="next" onclick="nextPage()">Вперёд ➡</button>

            <div class="zoom-controls">
                <button onclick="zoomOut()">➖</button>
                <button onclick="resetZoom()">🔍</button>
                <button onclick="zoomIn()">➕</button>
            </div>

            <button onclick="fullscreen()">⛶ Полный экран</button>
        </div>

        <script>
            const url = decodeURIComponent("{safe_url}");
            let index = 1;
            let total = 0;
            let zoom = 1;
            const img = document.getElementById("page");
            const loading = document.getElementById("loading");

            async function loadPage(i) {{
                loading.style.display = 'block';
                img.style.display = 'none';

                try {{
                    const res = await fetch(`/api/chapter?url=${{encodeURIComponent(url)}}&index=${{i}}`);
                    const data = await res.json();

                    if (data.image) {{
                        img.src = data.image;
                        img.onload = () => {{
                            loading.style.display = 'none';
                            img.style.display = 'block';
                            applyZoom();
                        }};
                        document.getElementById("counter").textContent = data.index + " / " + data.total;
                        index = data.index;
                        total = data.total;
                        updateButtons();
                        window.scrollTo(0,0);
                    }} else {{
                        loading.textContent = 'Ошибка загрузки страницы';
                    }}
                }} catch (error) {{
                    loading.textContent = 'Ошибка: ' + error.message;
                }}
            }}

            function updateButtons() {{
                document.getElementById("prev").disabled = index === 1;
                document.getElementById("next").disabled = index === total;
            }}

            function nextPage() {{ if (index < total) loadPage(index + 1); }}
            function prevPage() {{ if (index > 1) loadPage(index - 1); }}

            function applyZoom() {{
                img.style.transform = `scale(${{zoom}})`;
            }}

            function zoomIn() {{ 
                if (zoom < 3) {{
                    zoom += 0.1; 
                    applyZoom(); 
                }}
            }}

            function zoomOut() {{ 
                if (zoom > 0.3) {{
                    zoom -= 0.1; 
                    applyZoom(); 
                }}
            }}

            function resetZoom() {{ 
                zoom = 1; 
                applyZoom(); 
            }}

            function fullscreen() {{
                if (img.requestFullscreen) {{
                    img.requestFullscreen();
                }} else if (img.webkitRequestFullscreen) {{
                    img.webkitRequestFullscreen();
                }}
            }}

            // Обработка клавиатуры
            document.addEventListener("keydown", (e) => {{
                if (e.key === "ArrowRight") nextPage();
                if (e.key === "ArrowLeft") prevPage();
                if (e.key === "+" || e.key === "=") zoomIn();
                if (e.key === "-") zoomOut();
                if (e.key === "0") resetZoom();
                if (e.key === "f") fullscreen();
            }});

            // Обработка колесика мыши с Ctrl для зума
            document.addEventListener("wheel", (e) => {{
                if (e.ctrlKey) {{
                    e.preventDefault();
                    if (e.deltaY < 0) zoomIn(); 
                    else zoomOut();
                }}
            }}, {{ passive: false }});

            // Загружаем первую страницу
            loadPage(1);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)