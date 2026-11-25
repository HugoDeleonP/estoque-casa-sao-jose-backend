"""Aplicação FastAPI."""

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from estoque_doacoes.categoria.controller.CategoriaController import router as categoria_router
from estoque_doacoes.migrar import migrar
from estoque_doacoes.movimentacao.controller.MovimentacaoController import (
    router as movimentacao_router,
)
from estoque_doacoes.produto.controller.ProdutoController import router as produto_router
from estoque_doacoes.shared.database.config import settings
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


# Build do Vue (ESTOQUE_FRONT_DIST) servido pela mesma origem: sem CORS, um processo só.
# Registrado POR ÚLTIMO, depois de todas as rotas /api, senão ele as "engole".
if settings.front_dist is not None and (settings.front_dist / "index.html").is_file():
    FRONT_DIST = settings.front_dist.resolve()

    @app.get("/{caminho:path}", include_in_schema=False)
    def spa(caminho: str) -> FileResponse:
        if caminho == "api" or caminho.startswith("api/"):
            raise HTTPException(status_code=404, detail="Rota não encontrada")
        arquivo = (FRONT_DIST / caminho).resolve()
        if arquivo.is_file() and arquivo.is_relative_to(FRONT_DIST):
            return FileResponse(arquivo)
        # Rotas do vue-router (createWebHistory): /bancada, /catalogo… → index.html
        return FileResponse(FRONT_DIST / "index.html")
