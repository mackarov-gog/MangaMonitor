# src/web/server.py
import os
from urllib.parse import urlparse
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from urllib.parse import quote

from src.core.database import (
    init_db, ensure_manga, ensure_chapter,
    save_page, mark_chapter_saved, get_manga_list
)
from src.core.parser_manager import get_parser

app = FastAPI(title="MangaMonitor API")
init_db()

@app.get("/")
def root():
    return {"message": "MangaMonitor API работает. Перейдите на /docs для документации."}

@app.get("/api/manga")
def list_manga():
    """Вернуть список манги из базы"""
    return {"manga": get_manga_list()}

@app.get("/api/search")
async def search(q: str = Query(..., description="Название манги")):
    """Поиск манги через парсер"""
    parser = get_parser("seimanga")
    if parser is None:
        return JSONResponse(status_code=500, content={"error": "Парсер не найден"})

    async with parser:
        results = await parser.search_manga(q, max_pages=2)
    return {"results": results}


@app.get("/api/info")
async def manga_info(url: str):
    """Информация о выбранной манге (название, описание, главы)"""
    parser = get_parser("seimanga")
    if parser is None:
        return JSONResponse(status_code=500, content={"error": "Парсер не найден"})

    async with parser:
        info = await parser.get_manga_info(url)
    return info

@app.get("/api/chapter2")
async def chapter_images(url: str):
    """Получить список картинок из главы"""
    parser = get_parser("seimanga")
    if parser is None:
        return JSONResponse(status_code=500, content={"error": "Парсер не найден"})

    async with parser:
        images = await parser.get_chapter_images(url)
    return {"images": images}

@app.get("/api/chapter")
async def chapter_images(url: str, index: int | None = None):
    """
    API:
    - без index → вернёт список картинок
    - с index → вернёт одну картинку (номер начинается с 1)
    """
    parser = get_parser("seimanga")
    async with parser:
        images = await parser.get_chapter_images(url)

    if index is not None:
        if 1 <= index <= len(images):
            return {"image": images[index-1], "index": index, "total": len(images)}
        else:
            return {"error": "Index out of range", "total": len(images)}

    return {"images": images, "total": len(images)}




@app.get("/chapter/view", response_class=HTMLResponse)
async def chapter_view(url: str):
    from urllib.parse import quote
    safe_url = quote(url, safe="")

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Читалка MangaMonitor</title>
        <style>
            body {{
                background:#111;
                color:#eee;
                margin:0;
                font-family:sans-serif;
            }}
            h1 {{
                color:#fff;
                text-align:center;
                margin:10px 0;
            }}
            img {{
                max-width:95%;
                margin:20px auto;
                display:block;
                border-radius:8px;
                transition: transform 0.2s ease;
                transform-origin: top center;
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
                background: rgba(0,0,0,0.85);
                padding: 12px 0;
                border-top: 1px solid #444;
            }}
            button {{
                background: #222; color: #eee; border: 1px solid #444;
                padding: 8px 14px; border-radius: 5px; cursor: pointer; font-size: 14px;
            }}
            button:hover {{ background:#333; }}
            button:disabled {{ opacity:0.4; cursor:not-allowed; }}
        </style>
    </head>
    <body>
        <h1>Читалка MangaMonitor</h1>
        <img id="page" />
        <div class="controls">
            <button id="prev" onclick="prevPage()">⬅ Назад</button>
            <span id="counter"></span>
            <button id="next" onclick="nextPage()">Вперёд ➡</button>
            <button onclick="zoomIn()">➕ Увеличить</button>
            <button onclick="zoomOut()">➖ Уменьшить</button>
            <button onclick="resetZoom()">🔄 Сброс</button>
        </div>

        <script>
            const url = decodeURIComponent("{safe_url}");
            let index = 1;
            let total = 0;
            let zoom = 1;
            const img = document.getElementById("page");

            async function loadPage(i) {{
                const res = await fetch(`/api/chapter?url=${{encodeURIComponent(url)}}&index=${{i}}`);
                const data = await res.json();
                if (data.image) {{
                    img.src = data.image;
                    document.getElementById("counter").textContent = data.index + " / " + data.total;
                    index = data.index;
                    total = data.total;
                    document.getElementById("prev").disabled = index === 1;
                    document.getElementById("next").disabled = index === total;
                    
                    window.scrollTo(0,0);
                }}
            }}
            function nextPage() {{ if (index < total) loadPage(index+1); }}
            function prevPage() {{ if (index > 1) loadPage(index-1); }}

            document.addEventListener("keydown", (e) => {{
                if (e.key === "ArrowRight") nextPage();
                if (e.key === "ArrowLeft") prevPage();
                if (e.key === "+") zoomIn();
                if (e.key === "-") zoomOut();
                if (e.key === "0") resetZoom();
            }});

            function applyZoom() {{
                img.style.transform = `scale(${{zoom}})`;
            }}
            function zoomIn() {{ zoom += 0.1; applyZoom(); }}
            function zoomOut() {{ if (zoom > 0.2) {{ zoom -= 0.1; applyZoom(); }} }}
            function resetZoom() {{ zoom = 1; applyZoom(); }}

            document.addEventListener("wheel", (e) => {{
    if (e.ctrlKey) {{
        e.preventDefault();
        if (e.deltaY < 0) zoomIn(); else zoomOut();
    }}
}}, {{ passive: false }});


            loadPage(1);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)



@app.get("/search/view", response_class=HTMLResponse)
async def search_view(q: str = ""):
    parser = get_parser("seimanga")
    results = []
    if q:
        async with parser:
            results = await parser.search_manga(q, max_pages=2)

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Поиск MangaMonitor</title>
        <style>
            body {{ background:#111; color:#eee; font-family:sans-serif; margin:0; padding:20px; }}
            h1 {{ color:#fff; text-align:center; }}
            form {{ text-align:center; margin-bottom:30px; }}
            input[type="text"] {{
                padding:10px; width:300px; border-radius:8px; border:1px solid #444;
                background:#222; color:#eee; font-size:16px;
            }}
            button {{
                background:#222; color:#eee; border:1px solid #444;
                padding:10px 20px; margin-left:10px;
                border-radius:8px; cursor:pointer; font-size:16px;
            }}
            button:hover {{ background:#333; }}
            .list {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap:15px; }}
            .card {{
                background:#1a1a1a; padding:15px; border-radius:10px;
                box-shadow:0 2px 6px rgba(0,0,0,0.4); transition:0.2s;
            }}
            .card:hover {{ background:#222; transform:translateY(-3px); }}
            .card a {{ color:#fff; font-size:18px; text-decoration:none; }}
            .card a:hover {{ text-decoration:underline; }}
        </style>
    </head>
    <body>
        <h1>Поиск манги</h1>
        <form method="get" action="/search/view">
            <input type="text" name="q" value="{q}" placeholder="Введите название..." />
            <button type="submit">Искать</button>
        </form>
        <div class="list">
    """
    for item in results:
        html += f"<div class='card'><a href='/manga/view?url={quote(item['url'], safe='')}'>{item['title']}</a></div>"
    html += "</div></body></html>"
    return HTMLResponse(html)

@app.get("/manga/view", response_class=HTMLResponse)
async def manga_view(url: str):
    parser = get_parser("seimanga")
    async with parser:
        info = await parser.get_manga_info(url)

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{info['title']}</title>
        <style>
            body {{ background:#111; color:#eee; font-family:sans-serif; margin:0; padding:20px; }}
            .container {{ max-width:900px; margin:0 auto; }}
            h1 {{ color:#fff; }}
            p {{ line-height:1.6; margin:20px 0; }}
            h2 {{ margin-top:30px; color:#fff; }}
            .chapters {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap:12px; }}
            .chapter {{
                background:#1a1a1a; padding:12px; border-radius:8px;
                box-shadow:0 2px 6px rgba(0,0,0,0.4); transition:0.2s;
            }}
            .chapter:hover {{ background:#222; transform:translateY(-3px); }}
            .chapter a {{ color:#fff; text-decoration:none; font-size:16px; }}
            .chapter a:hover {{ text-decoration:underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{info['title']}</h1>
            <p>{info.get('description','Описание отсутствует')}</p>
            <h2>Главы</h2>
            <div class="chapters">
    """
    for chap in info.get("chapters", []):
        html += f"<div class='chapter'><a href='/chapter/view?url={quote(chap['url'], safe='')}'>{chap['title']}</a></div>"
    html += "</div></div></body></html>"
    return HTMLResponse(html)







@app.post("/api/download")
async def download_chapter(manga_url: str, chapter_url: str):
    """
    Скачивание главы локально + сохранение в БД
    """
    parser = get_parser("seimanga")
    if parser is None:
        return JSONResponse(status_code=500, content={"error": "Парсер не найден"})

    async with parser:
        info = await parser.get_manga_info(manga_url)
        manga_id = ensure_manga(info.get("title"), manga_url)

        # ищем выбранную главу
        chap = None
        for c in info.get("chapters", []):
            if c["url"] == chapter_url:
                chap = c
                break

        if chap is None:
            return JSONResponse(status_code=404, content={"error": "Глава не найдена"})

        chapter_id = ensure_chapter(manga_id, chap["title"], chap["url"])

        # путь для сохранения
        def slug_from_url(u):
            p = urlparse(u).path.strip("/").replace("/", "_")
            return p or "chapter"

        manga_slug = slug_from_url(manga_url)
        chap_slug = slug_from_url(chapter_url)
        out_dir = os.path.join("data", "downloads", manga_slug, chap_slug)
        os.makedirs(out_dir, exist_ok=True)

        saved = await parser.download_chapter(chapter_url, out_dir=out_dir)

        # сохраняем страницы в БД
        for i, path in enumerate(saved, 1):
            save_page(chapter_id, i, "", path)

        mark_chapter_saved(chapter_id)

    return {"status": "ok", "saved_files": saved}
