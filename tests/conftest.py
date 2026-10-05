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

from fastapi.testclient import TestClient  # noqa: E402

from estoque_doacoes.main import app  # noqa: E402
from estoque_doacoes.shared.database.db import Base, engine  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    # `with` executa o lifespan → aplica as migrações no banco temporário
    with TestClient(app) as c:
        yield c
    # Banco limpo para o próximo teste (filhas antes das mães por causa das FKs)
    with engine.begin() as conn:
        for tabela in reversed(Base.metadata.sorted_tables):
            conn.execute(tabela.delete())
