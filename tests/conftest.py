import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# Precisa vir ANTES de importar estoque_doacoes: settings e engine são criados no import.
# Variável de ambiente tem prioridade sobre o .env → os testes nunca tocam data/estoque.db.
_tmp = tempfile.TemporaryDirectory()
os.environ["ESTOQUE_DB_PATH"] = str(Path(_tmp.name) / "teste.db")
os.environ["ESTOQUE_DEBUG"] = "false"
os.environ["ESTOQUE_SECRET_KEY"] = "chave-apenas-para-testes"
os.environ["ESTOQUE_COOKIE_SECURE"] = "false"
os.environ["ESTOQUE_BCRYPT_ROUNDS"] = "4"  # bcrypt rápido só nos testes

from fastapi.testclient import TestClient  # noqa: E402

from estoque_doacoes.main import app  # noqa: E402
from estoque_doacoes.seed import semear_unidades  # noqa: E402
from estoque_doacoes.shared.database.db import Base, SessionLocal, engine  # noqa: E402
from estoque_doacoes.usuario.domain.enum.Role import Role  # noqa: E402
from estoque_doacoes.usuario.dto.UsuarioDTO import UsuarioCreate  # noqa: E402
from estoque_doacoes.usuario.service.UsuarioService import UsuarioService  # noqa: E402

# Senhas de exemplo, só para testes
SENHA_ADMIN = "senha-admin-123"
SENHA_COMUM = "senha-comum-123"
ADMIN_EMAIL = "chefe@teste.org"
COMUM_EMAIL = "bancada@teste.org"


def _criar_usuarios() -> dict[str, int]:
    with SessionLocal() as s:
        svc = UsuarioService(s)
        admin = svc.criar(
            UsuarioCreate(nome="Chefe", email=ADMIN_EMAIL, senha=SENHA_ADMIN, role=Role.ADMIN)
        )
        comum = svc.criar(
            UsuarioCreate(nome="Bancada", email=COMUM_EMAIL, senha=SENHA_COMUM, role=Role.COMUM)
        )
        return {"admin": admin.id, "comum": comum.id}


def login(c: TestClient, email: str, senha: str) -> None:
    r = c.post("/api/auth/login", json={"email": email, "senha": senha})
    assert r.status_code == 200, r.json()


@pytest.fixture
def ids() -> Iterator[dict[str, int]]:
    # `with` executa o lifespan → aplica as migrações no banco temporário
    with TestClient(app):
        pass
    yield _criar_usuarios()
    # Banco limpo para o próximo teste (filhas antes das mães por causa das FKs);
    # as unidades do seed voltam, como num banco recém-migrado
    with engine.begin() as conn:
        for tabela in reversed(Base.metadata.sorted_tables):
            conn.execute(tabela.delete())
    with SessionLocal() as s:
        semear_unidades(s)
        s.commit()


@pytest.fixture
def anonimo(ids) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client(ids) -> Iterator[TestClient]:
    """Logado como ADMIN (acesso total)."""
    with TestClient(app) as c:
        login(c, ADMIN_EMAIL, SENHA_ADMIN)
        yield c


@pytest.fixture
def comum(ids) -> Iterator[TestClient]:
    """Logado como COMUM (bancada)."""
    with TestClient(app) as c:
        login(c, COMUM_EMAIL, SENHA_COMUM)
        yield c
