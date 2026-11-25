"""Dependências de autenticação/autorização, aplicadas por router (ou por rota).

- `usuario_atual`: exige sessão válida → 401. Relê o usuário do banco a CADA requisição:
  desativado, com senha trocada ou perfil alterado perde o acesso na hora.
- `require_role("ADMIN")`: exige o perfil → 403 (também por URL direta, RNF05).
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from estoque_doacoes.shared.database.db import get_session
from estoque_doacoes.shared.exception.Erros import NaoAutenticado, SemPermissao
from estoque_doacoes.usuario.domain.entity.Usuario import Usuario
from estoque_doacoes.usuario.domain.enum.Role import Role
from estoque_doacoes.usuario.repository.UsuarioRepository import UsuarioRepository

CHAVE_SESSAO = "usuario"


def iniciar_sessao(request: Request, usuario: Usuario) -> None:
    request.session.clear()
    request.session[CHAVE_SESSAO] = {"id": usuario.id, "v": usuario.sessao_versao}


def encerrar_sessao(request: Request) -> None:
    request.session.clear()


def usuario_atual(request: Request, session: Annotated[Session, Depends(get_session)]) -> Usuario:
    dados = request.session.get(CHAVE_SESSAO)
    if not isinstance(dados, dict):
        raise NaoAutenticado()
    usuario = UsuarioRepository(session).por_id(dados.get("id", 0))
    if usuario is None or usuario.sessao_versao != dados.get("v"):
        request.session.clear()
        raise NaoAutenticado("Sessão expirada. Faça login novamente")
    return usuario


UsuarioAtual = Annotated[Usuario, Depends(usuario_atual)]


def require_role(*roles: Role | str) -> Callable[[Usuario], Usuario]:
    permitidos = {Role(r) for r in roles}

    def _verificar(usuario: UsuarioAtual) -> Usuario:
        if usuario.role not in permitidos:
            raise SemPermissao()
        return usuario

    return _verificar


# Atalhos para `dependencies=[...]` de routers e rotas
Autenticado = Depends(usuario_atual)
SomenteAdmin = Depends(require_role(Role.ADMIN))
