from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from server_routes.static import setup_frontend_static


def _prepare_dist(root_dir: Path) -> None:
    dist_dir = root_dir / "frontend" / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    (dist_dir / "index.html").write_text("<!doctype html><html><body>PandaPal</body></html>", encoding="utf-8")
    (dist_dir / "favicon.ico").write_bytes(b"ico")
    (dist_dir / "favicon-16.png").write_bytes(b"png16")
    (dist_dir / "favicon-32.png").write_bytes(b"png32")
    (dist_dir / "favicon-48.png").write_bytes(b"png48")
    (dist_dir / "favicon-192.png").write_bytes(b"png192")
    (dist_dir / "favicon-512.png").write_bytes(b"png512")
    (dist_dir / "manifest.json").write_text('{"name":"PandaPal"}', encoding="utf-8")
    (dist_dir / "sw.js").write_text("self.addEventListener('install', () => {});", encoding="utf-8")
    (dist_dir / "offline.html").write_text("<!doctype html><html><body>Offline</body></html>", encoding="utf-8")
    (dist_dir / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    (dist_dir / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><urlset><url><loc>https://pandapal.ru/</loc></url></urlset>',
        encoding="utf-8",
    )
    (dist_dir / "security.txt").write_text("Contact: mailto:Pandapal.ru@yandex.ru\n", encoding="utf-8")
    (dist_dir / "llms.txt").write_text(
        "Official website: https://pandapal.ru/\nOfficial Telegram bot: https://t.me/PandaPalBot\n",
        encoding="utf-8",
    )


@pytest.mark.asyncio
async def test_frontend_static_files_have_expected_headers(tmp_path: Path) -> None:
    _prepare_dist(tmp_path)
    app = web.Application()
    setup_frontend_static(app, tmp_path)

    async with TestServer(app) as server:
        async with TestClient(server) as client:
            checks = [
                ("/favicon-16.png", "image/png", "public, max-age=31536000, immutable"),
                ("/manifest.json", "application/json", "public, max-age=31536000, immutable"),
                ("/sw.js", "application/javascript", "public, max-age=31536000, immutable"),
                ("/robots.txt", "text/plain; charset=utf-8", "public, max-age=3600"),
                ("/sitemap.xml", "application/xml; charset=utf-8", "public, max-age=3600"),
                ("/.well-known/security.txt", "text/plain; charset=utf-8", None),
                ("/.well-known/llms.txt", "text/plain; charset=utf-8", "public, max-age=3600"),
            ]
            for path, content_type, cache_control in checks:
                response = await client.get(path)
                assert response.status == 200
                assert response.headers["Content-Type"].startswith(content_type)
                if cache_control:
                    assert response.headers.get("Cache-Control") == cache_control


@pytest.mark.asyncio
async def test_spa_fallback_returns_404_for_unknown_static_extension(tmp_path: Path) -> None:
    _prepare_dist(tmp_path)
    app = web.Application()
    setup_frontend_static(app, tmp_path)

    async with TestServer(app) as server:
        async with TestClient(server) as client:
            response = await client.get("/missing.json")
            body = await response.text()
            assert response.status == 404
            assert body == "Not Found"


@pytest.mark.asyncio
async def test_spa_fallback_serves_index_for_non_file_paths(tmp_path: Path) -> None:
    _prepare_dist(tmp_path)
    app = web.Application()
    setup_frontend_static(app, tmp_path)

    async with TestServer(app) as server:
        async with TestClient(server) as client:
            response = await client.get("/education-ai-for-kids")
            body = await response.text()
            assert response.status == 200
            assert "PandaPal" in body
