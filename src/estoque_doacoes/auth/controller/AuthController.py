"""Login por cookie de sessão assinado (HttpOnly, SameSite=Lax, Secure em produção).
Front e API no mesmo domínio: sem CORS e sem token guardado no navegador."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from estoque_doacoes.auth.dependencies import (
    UsuarioAtual,
    encerrar_sessao,
    iniciar_sessao,
)
from estoque_doacoes.auth.dto.AuthDTO import LoginIn
from estoque_doacoes.auth.senha import conferir
from estoque_doacoes.shared.database.db import get_session
from estoque_doacoes.shared.exception.Erros import NaoAutenticado
from estoque_doacoes.usuario.dto.UsuarioDTO import UsuarioOut
from estoque_doacoes.usuario.repository.UsuarioRepository import UsuarioRepository

router = APIRouter(prefix="/api/auth", tags=["autenticação"])


@router.post("/login", response_model=UsuarioOut)
def login(dados: LoginIn, request: Request, session: Annotated[Session, Depends(get_session)]):
    usuario = UsuarioRepository(session).por_email(dados.email)
    # Mesma mensagem para e-mail inexistente e senha errada; conferir() gasta o mesmo tempo
    if not conferir(dados.senha, usuario.senha_hash if usuario else None):
        raise NaoAutenticado("E-mail ou senha inválidos")
    iniciar_sessao(request, usuario)
    return usuario


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> None:
    encerrar_sessao(request)


@router.get("/me", response_model=UsuarioOut)
def me(usuario: UsuarioAtual):
    return usuario
