"""
Регистрация раздачи статики frontend и SPA fallback.
"""

import os
import shutil
from pathlib import Path

from aiohttp import web
from loguru import logger


def setup_frontend_static(app: web.Application, root_dir: Path) -> None:
    """Настройка раздачи статических файлов frontend. root_dir — корень проекта."""
    frontend_dist = root_dir / "frontend" / "dist"
    if frontend_dist.exists():
        static_files = [
            "logo.png",
            "favicon.ico",
            "favicon.svg",
            "robots.txt",
            "sitemap.xml",
            "security.txt",
            "panda-happy-in-game.png",
            "panda-sad-in-game.png",
            "yandex_3f9e35f6d79cfb2f.html",
        ]
        tamagotchi_files = [
            "panda-neutral.png",
            "panda-happy.png",
            "panda-sad.png",
            "panda-bored.png",
            "panda-hungry.png",
            "panda-full.png",
            "panda-played.png",
            "panda-sleepy.png",
            "panda-sleeping.png",
            "panda-wants_bamboo.png",
            "panda-no_bamboo.png",
            "panda-questioning.png",
            "panda-offended.png",
            "panda-eating.png",
            "panda-excited.png",
        ]
        panda_chat_reactions_files = [
            "panda-happy.png",
            "panda-eating.png",
            "panda-offended.png",
            "panda-questioning.png",
        ]
        favicon_ico_path = frontend_dist / "favicon.ico"
        if not favicon_ico_path.exists():
            logo_png_path = frontend_dist / "logo.png"
            if logo_png_path.exists():
                shutil.copy2(logo_png_path, favicon_ico_path)
                logger.info("✅ Создан favicon.ico из logo.png")
        for static_file in static_files:
            file_path = frontend_dist / static_file
            if file_path.exists():
                content_type = "application/octet-stream"
                if static_file.endswith(".svg"):
                    content_type = "image/svg+xml"
                elif static_file.endswith(".png"):
                    content_type = "image/png"
                elif static_file.endswith(".ico"):
                    content_type = "image/x-icon"
                elif static_file.endswith(".json"):
                    content_type = "application/json"
                elif static_file.endswith(".txt"):
                    content_type = "text/plain"
                elif static_file.endswith(".xml"):
                    content_type = "text/xml; charset=utf-8"
                elif static_file.endswith(".js"):
                    content_type = "application/javascript"
                elif static_file.endswith(".html"):
                    content_type = "text/html"

                async def serve_static_file(
                    _request: web.Request,
                    fp=file_path,
                    ct=content_type,
                    sf=static_file,
                ) -> web.Response:
                    headers = {"Content-Type": ct}
                    if not sf.endswith(".html"):
                        headers["Cache-Control"] = "public, max-age=31536000, immutable"
                    return web.FileResponse(fp, headers=headers)

                app.router.add_get(f"/{static_file}", serve_static_file)

        tamagotchi_dir = frontend_dist / "panda-tamagotchi"
        for tf in tamagotchi_files:
            file_path = tamagotchi_dir / tf
            if file_path.exists():

                async def serve_tamagotchi(
                    _request: web.Request,
                    fp=file_path,
                ) -> web.Response:
                    return web.FileResponse(
                        fp,
                        headers={
                            "Content-Type": "image/png",
                            "Cache-Control": "public, max-age=31536000, immutable",
                        },
                    )

                app.router.add_get(f"/panda-tamagotchi/{tf}", serve_tamagotchi)

        panda_chat_reactions_dir = frontend_dist / "panda-chat-reactions"
        for pcrf in panda_chat_reactions_files:
            pcr_path = panda_chat_reactions_dir / pcrf
            if pcr_path.exists():

                async def serve_chat_reaction(
                    _request: web.Request,
                    fp=pcr_path,
                ) -> web.Response:
                    return web.FileResponse(
                        fp,
                        headers={
                            "Content-Type": "image/png",
                            "Cache-Control": "public, max-age=31536000, immutable",
                        },
                    )

                app.router.add_get(f"/panda-chat-reactions/{pcrf}", serve_chat_reaction)

        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():

            async def serve_asset(request: web.Request) -> web.Response:
                filename = request.match_info.get("filename", "")
                if not filename:
                    return web.Response(status=404, text="Asset filename required")
                file_path = assets_dir / filename
                if not file_path.exists() or not file_path.is_file():
                    available_js = [f for f in os.listdir(assets_dir) if f.endswith(".js")]
                    logger.warning(
                        f"⚠️ Assets файл не найден: /assets/{filename} | "
                        f"Доступные JS: {', '.join(available_js[:3])}{'...' if len(available_js) > 3 else ''}"
                    )
                    return web.Response(status=404, text=f"Asset not found: {filename}")
                content_type = "application/octet-stream"
                if filename.endswith(".js"):
                    content_type = "application/javascript"
                elif filename.endswith(".css"):
                    content_type = "text/css"
                elif filename.endswith(".map"):
                    content_type = "application/json"
                elif filename.endswith(".png"):
                    content_type = "image/png"
                elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
                    content_type = "image/jpeg"
                elif filename.endswith(".svg"):
                    content_type = "image/svg+xml"
                elif filename.endswith(".woff") or filename.endswith(".woff2"):
                    content_type = "font/woff2"
                elif filename.endswith(".webp"):
                    content_type = "image/webp"
                headers = {"Content-Type": content_type}
                if any(
                    filename.endswith(ext)
                    for ext in [
                        ".js",
                        ".css",
                        ".woff",
                        ".woff2",
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".webp",
                        ".svg",
                    ]
                ):
                    headers["Cache-Control"] = "public, max-age=31536000, immutable"
                return web.FileResponse(file_path, headers=headers)

            app.router.add_get("/assets/{filename:.*}", serve_asset)
            all_files = os.listdir(assets_dir)
            js_files = [f for f in all_files if f.endswith(".js")]
            logger.info(f"✅ Assets директория зарегистрирована: {assets_dir}")
            logger.info(f"📦 Найдено файлов в assets: {len(all_files)}")
            logger.info(f"📦 Найдено JS файлов: {len(js_files)}")
            if js_files:
                logger.info(
                    f"📦 JS файлы: {', '.join(js_files[:5])}{'...' if len(js_files) > 5 else ''}"
                )

        security_txt_path = frontend_dist / "security.txt"
        if security_txt_path.exists():

            async def serve_security_txt(_request: web.Request) -> web.Response:
                return web.FileResponse(
                    security_txt_path,
                    headers={"Content-Type": "text/plain; charset=utf-8"},
                )

            app.router.add_get("/.well-known/security.txt", serve_security_txt)
            logger.info("✅ Security.txt зарегистрирован по пути /.well-known/security.txt")

        app.router.add_get("/", lambda _: web.FileResponse(frontend_dist / "index.html"))

        # Расширения, при которых запрос считается к несуществующему файлу — отдаём 404 (рекомендация Яндекса)
        _STATIC_LIKE_EXTENSIONS = (".html", ".htm", ".php", ".pdf", ".asp", ".aspx")

        async def spa_fallback(request: web.Request) -> web.Response:
            path = request.path.rstrip("/") or "/"
            if (
                path.startswith("/api/")
                or path.startswith("/assets/")
                or path == "/webhook"
                or path.startswith("/webhook/")
                or path == "/health"
                or path.startswith("/health/")
                or path.startswith("/test/")
                or path.startswith("/.well-known/")
            ):
                if path.startswith("/assets/"):
                    logger.warning(f"⚠️ Assets файл не найден: {path}")
                return web.Response(status=404, text="Not Found")
            # Запрос к несуществующей странице с расширением файла — 404 для корректной индексации
            if any(path.endswith(ext) for ext in _STATIC_LIKE_EXTENSIONS):
                return web.Response(status=404, text="Not Found")
            return web.FileResponse(frontend_dist / "index.html")

        app.router.add_get("/{tail:.*}", spa_fallback)
        logger.info(f"✅ Frontend настроен: {frontend_dist}")
    else:

        async def root_handler(_request: web.Request) -> web.Response:
            return web.json_response(
                {"status": "ok", "service": "pandapal-bot", "mode": "webhook"},
                status=200,
            )

        app.router.add_get("/", root_handler)
        logger.warning("⚠️ Frontend не найден, используется fallback")
