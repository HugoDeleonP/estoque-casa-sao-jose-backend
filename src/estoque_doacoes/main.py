"""Aplicação FastAPI."""

from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from estoque_doacoes.db import get_session

app = FastAPI(
    title="Estoque de Doações — Casa São José",
    version="0.1.0",
)

SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/api/health", tags=["infra"])
def health(session: SessionDep) -> dict:
    """Confirma que a API está de pé e o SQLite responde."""
    fk = session.execute(text("PRAGMA foreign_keys")).scalar_one()
    journal = session.execute(text("PRAGMA journal_mode")).scalar_one()
    return {"status": "ok", "db": {"foreign_keys": bool(fk), "journal_mode": journal}}


# Quando o build do Vue existir (frontend/dist), ele será servido daqui:
#   from fastapi.staticfiles import StaticFiles
#   app.mount("/", StaticFiles(directory=..., html=True), name="spa")
# Montado POR ÚLTIMO, depois de todas as rotas /api, senão ele as "engole".
