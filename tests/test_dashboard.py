"""F2: indicadores calculados das movimentações, com conversão de unidades."""

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import text

from estoque_doacoes.dashboard.service.DashboardService import hoje_local
from estoque_doacoes.shared.database.db import engine
from tests.test_crud import _categoria, _mov, _produto, unidade_id


def _cenario(client: TestClient) -> dict:
    alimentos = _categoria(client, "Alimentos")
    higiene = _categoria(client, "Higiene")
    # Arroz 5 kg, Leite 1 L, Café 500 g, Sabonete em dúzia (12 un)
    arroz = _produto(client, alimentos, codigo_barras="11111111", nome="Arroz", conteudo_valor=5)
    leite = _produto(
        client,
        alimentos,
        codigo_barras="22222222",
        nome="Leite",
        conteudo_valor=1,
        unidade_medida_id=unidade_id(client, "L"),
    )
    cafe = _produto(
        client,
        alimentos,
        codigo_barras="33333333",
        nome="Café",
        conteudo_valor=500,
        unidade_medida_id=unidade_id(client, "g"),
    )
    sabonete = _produto(
        client,
        higiene,
        codigo_barras="44444444",
        nome="Sabonete",
        conteudo_valor=1,
        unidade_medida_id=unidade_id(client, "dz"),
    )
    _mov(client, arroz["id"], "ENTRADA", 10)  # 50 kg
    _mov(client, arroz["id"], "SAIDA", -4)  # −20 kg
    _mov(client, arroz["id"], "AJUSTE", 1, "contagem")  # +5 kg (fora de entradas/saídas)
    _mov(client, leite["id"], "ENTRADA", 6)  # 6 L
    _mov(client, cafe["id"], "ENTRADA", 2)  # 1 kg
    _mov(client, sabonete["id"], "SAIDA", -2)  # −24 un → pendência
    return {"alimentos": alimentos, "higiene": higiene, "sabonete": sabonete}


def test_resumo_com_conversao(client: TestClient) -> None:
    c = _cenario(client)
    r = client.get("/api/dashboard/resumo").json()
    assert r["fim"] == hoje_local().isoformat()
    assert r["inicio"] == (hoje_local() - timedelta(days=29)).isoformat()
    assert r["saldo_total"] == 7 + 6 + 2 - 2
    assert r["total_produtos"] == 4
    assert r["produtos_saldo_negativo"] == 1
    assert r["total_entradas"] == 18  # AJUSTE não conta
    assert r["total_saidas"] == 6
    # kg, L e un nunca se misturam
    assert r["estoque_grandeza"] == {"massa_kg": 36.0, "volume_l": 6.0, "contagem_un": -24.0}
    assert r["entradas_grandeza"] == {"massa_kg": 51.0, "volume_l": 6.0, "contagem_un": 0}
    assert r["saidas_grandeza"] == {"massa_kg": 20.0, "volume_l": 0, "contagem_un": 24.0}

    so_alimentos = client.get(
        "/api/dashboard/resumo", params={"categoria_id": c["alimentos"]}
    ).json()
    assert so_alimentos["produtos_saldo_negativo"] == 0
    assert so_alimentos["total_saidas"] == 4


def test_resumo_confere_com_sql_manual(client: TestClient) -> None:
    _cenario(client)
    r = client.get("/api/dashboard/resumo").json()
    with engine.connect() as conn:
        entradas = conn.execute(
            text("SELECT SUM(quantidade) FROM movimentacao WHERE tipo = 'ENTRADA'")
        ).scalar_one()
        saidas = conn.execute(
            text("SELECT -SUM(quantidade) FROM movimentacao WHERE tipo = 'SAIDA'")
        ).scalar_one()
        saldo = conn.execute(text("SELECT SUM(quantidade) FROM movimentacao")).scalar_one()
    assert (r["total_entradas"], r["total_saidas"], r["saldo_total"]) == (entradas, saidas, saldo)


def test_series_e_periodo(client: TestClient) -> None:
    _cenario(client)
    # uma entrada antiga, fora dos últimos 30 dias
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE movimentacao SET created_at = '2020-01-01 12:00:00.000000'"
                " WHERE quantidade = 6"
            )
        )
    serie = client.get("/api/dashboard/series").json()
    assert len(serie) == 30
    assert serie[-1]["data"] == hoje_local().isoformat()
    assert sum(p["entradas"] for p in serie) == 12
    assert sum(p["saidas"] for p in serie) == 6

    antigo = client.get(
        "/api/dashboard/series", params={"inicio": "2020-01-01", "fim": "2020-01-01"}
    )
    assert antigo.json() == [{"data": "2020-01-01", "entradas": 6, "saidas": 0}]

    assert (
        client.get(
            "/api/dashboard/resumo", params={"inicio": "2026-02-01", "fim": "2026-01-01"}
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/api/dashboard/series", params={"inicio": "2020-01-01", "fim": "2026-01-01"}
        ).status_code
        == 422
    )


def test_pendencias(client: TestClient) -> None:
    c = _cenario(client)
    pend = client.get("/api/dashboard/pendencias").json()
    assert pend == [
        {
            "produto_id": c["sabonete"]["id"],
            "nome": "Sabonete",
            "marca": None,
            "categoria": "Higiene",
            "saldo": -2,
        }
    ]
    assert (
        client.get("/api/dashboard/pendencias", params={"categoria_id": c["alimentos"]}).json()
        == []
    )
