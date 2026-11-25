from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints

from estoque_doacoes.auth.senha import SENHA_MAX_BYTES, SENHA_MIN
from estoque_doacoes.usuario.domain.enum.Role import Role


def _senha_valida(v: str) -> str:
    if len(v) < SENHA_MIN:
        raise ValueError(f"A senha precisa ter ao menos {SENHA_MIN} caracteres")
    if len(v.encode()) > SENHA_MAX_BYTES:
        raise ValueError(f"A senha pode ter no máximo {SENHA_MAX_BYTES} bytes")
    return v


Nome = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
# Validação simples de propósito: o login compartilhado pode ser "bancada@casasaojose.local"
Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, to_lower=True, max_length=254, pattern=r"^[^@\s]+@[^@\s]+$"
    ),
]
Senha = Annotated[str, AfterValidator(_senha_valida)]


class UsuarioCreate(BaseModel):
    nome: Nome
    email: Email
    senha: Senha
    role: Role = Role.COMUM


class PerfilUpdate(BaseModel):
    role: Role


class SenhaUpdate(BaseModel):
    senha: Senha


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    role: Role
    created_at: datetime
