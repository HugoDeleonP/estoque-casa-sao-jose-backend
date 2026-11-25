"""Gestão de usuários: somente ADMIN (o router inteiro exige o perfil)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from estoque_doacoes.auth.dependencies import SomenteAdmin, UsuarioAtual
from estoque_doacoes.shared.database.db import get_session
from estoque_doacoes.usuario.dto.UsuarioDTO import (
    PerfilUpdate,
    SenhaUpdate,
    UsuarioCreate,
    UsuarioOut,
)
from estoque_doacoes.usuario.service.UsuarioService import UsuarioService

router = APIRouter(prefix="/api/usuarios", tags=["usuários"], dependencies=[SomenteAdmin])


def get_service(session: Annotated[Session, Depends(get_session)]) -> UsuarioService:
    return UsuarioService(session)


Service = Annotated[UsuarioService, Depends(get_service)]


@router.get("", response_model=list[UsuarioOut])
def listar(service: Service):
    return service.listar()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UsuarioOut)
def criar(dados: UsuarioCreate, service: Service):
    """ADMIN pode criar outro ADMIN (D11)."""
    return service.criar(dados)


@router.put("/{usuario_id}/perfil", response_model=UsuarioOut)
def alterar_perfil(usuario_id: int, dados: PerfilUpdate, service: Service, autor: UsuarioAtual):
    """409 ao alterar o próprio perfil ou rebaixar o último ADMIN."""
    return service.alterar_perfil(usuario_id, dados.role, autor)


@router.put("/{usuario_id}/senha", status_code=status.HTTP_204_NO_CONTENT)
def redefinir_senha(usuario_id: int, dados: SenhaUpdate, service: Service) -> None:
    """Encerra as sessões abertas do usuário."""
    service.redefinir_senha(usuario_id, dados.senha)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar(usuario_id: int, service: Service, autor: UsuarioAtual) -> None:
    """Exclusão lógica. 409 ao desativar a si mesmo ou o último ADMIN."""
    service.desativar(usuario_id, autor)
