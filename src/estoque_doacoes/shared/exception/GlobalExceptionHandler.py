"""Tratamento GLOBAL de erros (equivale ao @RestControllerAdvice do Spring Boot).

Cada método é um @ExceptionHandler: o service lança erro de DOMÍNIO e só aqui ele
vira status HTTP. Controllers não têm try/except."""

import logging
from datetime import UTC, datetime
from http import HTTPStatus

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from estoque_doacoes.shared.exception.ErroDTO import CampoInvalido, ErroResposta
from estoque_doacoes.shared.exception.Erros import Conflito, ErroDominio, NaoEncontrado

log = logging.getLogger(__name__)


class GlobalExceptionHandler:
    @classmethod
    def registrar(cls, app: FastAPI) -> None:
        # O FastAPI escolhe o handler da classe MAIS ESPECÍFICA na hierarquia
        # (igual ao Spring): NaoEncontrado vence ErroDominio, que vence Exception.
        app.add_exception_handler(NaoEncontrado, cls.nao_encontrado)
        app.add_exception_handler(Conflito, cls.conflito)
        app.add_exception_handler(ErroDominio, cls.erro_dominio)
        app.add_exception_handler(RequestValidationError, cls.validacao)
        app.add_exception_handler(Exception, cls.erro_inesperado)

    @staticmethod
    def nao_encontrado(request: Request, exc: NaoEncontrado) -> JSONResponse:
        return _resposta(request, status.HTTP_404_NOT_FOUND, str(exc))

    @staticmethod
    def conflito(request: Request, exc: Conflito) -> JSONResponse:
        return _resposta(request, status.HTTP_409_CONFLICT, str(exc))

    @staticmethod
    def erro_dominio(request: Request, exc: ErroDominio) -> JSONResponse:
        # Regra de negócio violada que não tem handler mais específico
        return _resposta(request, status.HTTP_400_BAD_REQUEST, str(exc))

    @staticmethod
    def validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Equivale ao MethodArgumentNotValidException: um item por campo inválido
        campos = [
            CampoInvalido(
                campo=".".join(str(p) for p in erro["loc"] if p != "body"),
                mensagem=erro["msg"],
            )
            for erro in exc.errors()
        ]
        return _resposta(
            request,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Dados inválidos",
            campos,
        )

    @staticmethod
    def erro_inesperado(request: Request, exc: Exception) -> JSONResponse:
        # Bug ou falha de infraestrutura: loga o stack trace e NÃO expõe detalhes ao cliente
        log.exception("Erro inesperado em %s %s", request.method, request.url.path)
        return _resposta(request, status.HTTP_500_INTERNAL_SERVER_ERROR, "Erro interno no servidor")


def _resposta(
    request: Request,
    codigo: int,
    mensagem: str,
    campos: list[CampoInvalido] | None = None,
) -> JSONResponse:
    corpo = ErroResposta(
        timestamp=datetime.now(UTC),
        status=codigo,
        erro=HTTPStatus(codigo).phrase,
        mensagem=mensagem,
        caminho=request.url.path,
        campos=campos,
    )
    return JSONResponse(
        status_code=codigo,
        content=corpo.model_dump(mode="json", exclude_none=True),
    )
