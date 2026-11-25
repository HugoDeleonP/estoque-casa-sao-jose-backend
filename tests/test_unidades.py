"""F1: unidades de medida e conteúdo da embalagem."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from estoque_doacoes.shared.database.db import engine
from tests.test_crud import _categoria, _produto, unidade_id


def test_seed_de_unidades(comum: TestClient) -> None:
    unidades = {u["sigla"]: u for u in comum.get("/api/unidades").json()}
    assert set(unidades) == {"kg", "g", "L", "mL", "un", "dz"}
    assert unidades["g"]["fator_base"] == 0.001
    assert unidades["dz"] == unidades["dz"] | {"grandeza": "CONTAGEM", "fator_base": 12}


@pytest.mark.parametrize("valor", [0, -1, None, "abc"])
def test_conteudo_invalido_422(client: TestClient, valor) -> None:
    cid = _categoria(client)
    r = client.post(
        "/api/produtos",
        json={
            "nome": "Arroz",
            "conteudo_valor": valor,
            "unidade_medida_id": unidade_id(client, "kg"),
            "categoria_id": cid,
        },
    )
    assert r.status_code == 422


def test_conteudo_obrigatorio_422(client: TestClient) -> None:
    cid = _categoria(client)
    r = client.post("/api/produtos", json={"nome": "Arroz", "categoria_id": cid})
    assert r.status_code == 422
    campos = {c["campo"] for c in r.json()["campos"]}
    assert campos == {"conteudo_valor", "unidade_medida_id"}


def test_unidade_inexistente_ou_excluida_422(client: TestClient) -> None:
    cid = _categoria(client)
    r = client.post(
        "/api/unidades",
        json={"sigla": "cx", "nome": "caixa", "grandeza": "CONTAGEM", "fator_base": 1},
    )
    cx = r.json()["id"]
    assert client.delete(f"/api/unidades/{cx}").status_code == 204
    for uid in (999, cx):
        r = client.post(
            "/api/produtos",
            json={
                "nome": "Arroz",
                "conteudo_valor": 1,
                "unidade_medida_id": uid,
                "categoria_id": cid,
            },
        )
        assert r.status_code == 422


def test_check_do_banco_impede_conteudo_zero(client: TestClient) -> None:
    p = _produto(client, _categoria(client))
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text("UPDATE produto SET conteudo_valor = 0 WHERE id = :id"), {"id": p["id"]})


def test_crud_de_unidade(client: TestClient, comum: TestClient) -> None:
    nova = {"sigla": "fd", "nome": "fardo", "grandeza": "CONTAGEM", "fator_base": 6}
    r = client.post("/api/unidades", json=nova)
    assert r.status_code == 201
    uid = r.json()["id"]
    assert r.json()["em_uso"] is False
    # aparece no seletor de qualquer perfil
    assert "fd" in {u["sigla"] for u in comum.get("/api/unidades").json()}

    # sigla duplicada (sem diferenciar maiúsculas)
    assert client.post("/api/unidades", json=nova | {"sigla": "FD"}).status_code == 409
    assert client.post("/api/unidades", json=nova | {"fator_base": 0}).status_code == 422
    assert client.post("/api/unidades", json=nova | {"grandeza": "TEMPO"}).status_code == 422

    # sem uso: tudo editável
    r = client.put(f"/api/unidades/{uid}", json=nova | {"fator_base": 12, "nome": "fardo 12"})
    assert r.status_code == 200 and r.json()["fator_base"] == 12


def test_unidade_em_uso_protegida(client: TestClient) -> None:
    """F1.4: em uso, só o nome muda; não pode ser excluída."""
    cid = _categoria(client)
    kg = unidade_id(client, "kg")
    _produto(client, cid)
    base = {"sigla": "kg", "nome": "quilo", "grandeza": "MASSA", "fator_base": 1}

    assert client.put(f"/api/unidades/{kg}", json=base).json()["nome"] == "quilo"
    for mudanca in ({"fator_base": 2}, {"grandeza": "VOLUME"}, {"sigla": "KG2"}):
        r = client.put(f"/api/unidades/{kg}", json=base | mudanca)
        assert r.status_code == 409, mudanca
    assert client.delete(f"/api/unidades/{kg}").status_code == 409
    assert next(u for u in client.get("/api/unidades").json() if u["id"] == kg)["em_uso"] is True


def test_produto_exibe_conteudo(client: TestClient) -> None:
    p = _produto(
        client, _categoria(client), conteudo_valor=0.5, unidade_medida_id=unidade_id(client, "L")
    )
    assert p["conteudo_valor"] == 0.5
    assert p["unidade_medida"]["sigla"] == "L"
