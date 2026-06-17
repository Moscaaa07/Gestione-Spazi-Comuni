from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from routers import auth, spaces, bookings
import os

app = FastAPI(title="Gestione Spazi Comuni - API-First")

# Inclusione dei router dei singoli microservizi
app.include_router(auth.router)
app.include_router(spaces.router)
app.include_router(bookings.router)

@app.get("/", response_class=HTMLResponse)
def read_index():
    template_path = os.path.join("templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>File index.html non trovato nella cartella templates/</h3>"