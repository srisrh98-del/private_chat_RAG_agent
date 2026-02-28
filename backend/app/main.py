from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles

from .config import CORS_ORIGINS, HOST, PORT, STATIC_DIR
from .routes import health, pdf_routes, chat_routes, admin_routes

app = FastAPI(title="Chat Agent", description="Local-only PDF chat with citations")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(pdf_routes.router)
app.include_router(chat_routes.router)
app.include_router(admin_routes.router)

# Serve built frontend (for desktop app / single-server mode)
if STATIC_DIR.is_dir():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    index_html = STATIC_DIR / "index.html"
    if index_html.is_file():
        @app.get("/")
        def serve_index():
            return FileResponse(index_html)

        @app.get("/{path:path}")
        def serve_spa(path: str):
            return FileResponse(index_html)


def run():
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    run()
