"""Formato ÚNICO de erro da API (equivale ao ErrorResponse do Spring Boot).
O frontend trata todo erro do mesmo jeito: lê `mensagem` e, se houver, `campos`."""

from datetime import datetime

from pydantic import BaseModel


class CampoInvalido(BaseModel):
    campo: str
    mensagem: str


class ErroResposta(BaseModel):
    timestamp: datetime
    status: int
    erro: str  # frase padrão do status HTTP, ex.: "Not Found"
    mensagem: str
    caminho: str
    campos: list[CampoInvalido] | None = None  # só em erro de validação (422)
