"""
main.py — Entry point dell'applicazione FastAPI.

Avvio:
    uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from database import create_tables
from routers import auth, spaces, bookings

# Crea le tabelle SQLite al primo avvio
create_tables()

app = FastAPI(title="Gestione Spazi Comuni", version="1.0.0")

# ─── Router ─────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(spaces.router)
app.include_router(bookings.router)

# ─── File statici (HTML, CSS, JS) ───────────────────────────────────────────
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return {"error": "index.html non trovato nella cartella static/"}
    return FileResponse(str(index_path))
