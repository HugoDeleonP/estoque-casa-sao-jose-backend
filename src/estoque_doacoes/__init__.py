"""Ponto de entrada: `uv run estoque-doacoes`."""


def main() -> None:
    import uvicorn

    from estoque_doacoes.config import settings

    uvicorn.run(
        "estoque_doacoes.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
