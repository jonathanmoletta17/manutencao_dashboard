"""
Aplicação FastAPI do backend de Manutenção.
Monta o maintenance_router sob o prefixo já definido no router.
"""
import logging
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import (
    maintenance_stats_router,
    maintenance_ranking_router,
    maintenance_tickets_router,
)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )


def load_env_files() -> None:
    """Carrega variáveis de ambiente de arquivos .env locais, se existirem."""
    here = Path(__file__).parent
    candidates = [here / ".env.local", here / ".env"]
    for p in candidates:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    if not line or line.strip().startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip()
                        if k and v and (k not in os.environ):
                            os.environ[k] = v
            except Exception:
                # Não interrompe startup se falhar
                pass


setup_logging()
load_env_files()
app = FastAPI(title="DTIC Dashboard - Manutenção")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5002",
        "http://127.0.0.1:5002",
        "http://localhost:5003",
        "http://127.0.0.1:5003",
        "http://localhost:5004",
        "http://127.0.0.1:5004",
        "http://localhost:5005",
        "http://127.0.0.1:5005",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(maintenance_stats_router.router)
app.include_router(maintenance_ranking_router.router)
app.include_router(maintenance_tickets_router.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}