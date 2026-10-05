"""Aplicação FastAPI."""

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from estoque_doacoes.categoria.controller.CategoriaController import router as categoria_router
from estoque_doacoes.migrar import migrar
from estoque_doacoes.movimentacao.controller.MovimentacaoController import (
    router as movimentacao_router,
)
from estoque_doacoes.produto.controller.ProdutoController import router as produto_router
from estoque_doacoes.shared.database.db import get_session
from estoque_doacoes.shared.exception.GlobalExceptionHandler import GlobalExceptionHandler


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Aplica migrações pendentes ao subir. Banco novo → cria tudo;
    # banco existente → só o que mudou, preservando os dados.
    migrar()
    yield


app = FastAPI(
    title="Estoque de Doações — Casa São José",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(categoria_router)
app.include_router(produto_router)
app.include_router(movimentacao_router)

GlobalExceptionHandler.registrar(app)


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
