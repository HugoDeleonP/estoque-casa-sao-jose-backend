from fastapi.testclient import TestClient

ARROZ = "7891234567890"


def _categoria(client: TestClient, nome: str = "Alimentos") -> int:
    r = client.post("/api/categorias", json={"nome": nome})
    assert r.status_code == 201
    return r.json()["id"]


def _produto(client: TestClient, categoria_id: int, **campos) -> dict:
    dados = {
        "codigo_barras": ARROZ,
        "nome": "Arroz",
        "unidade": "1 kg",
        "categoria_id": categoria_id,
    }
    r = client.post("/api/produtos", json=dados | campos)
    assert r.status_code == 201, r.json()
    return r.json()


def _mov(client: TestClient, produto_id: int, tipo: str, quantidade: int, obs: str | None = None):
    return client.post(
        "/api/movimentacoes",
        json={"produto_id": produto_id, "tipo": tipo, "quantidade": quantidade, "observacao": obs},
    )


# ---------- Categoria ----------


def test_categoria_crud(client: TestClient) -> None:
    cid = _categoria(client)
    assert client.get(f"/api/categorias/{cid}").json() == {"id": cid, "nome": "Alimentos"}

    r = client.put(f"/api/categorias/{cid}", json={"nome": "Higiene"})
    assert r.status_code == 200
    assert r.json()["nome"] == "Higiene"
    assert [c["nome"] for c in client.get("/api/categorias").json()] == ["Higiene"]

    assert client.delete(f"/api/categorias/{cid}").status_code == 204
    assert client.get(f"/api/categorias/{cid}").status_code == 404
    assert client.get("/api/categorias").json() == []
    # Soft delete libera o nome para uma nova categoria
    _categoria(client, "Higiene")


def test_categoria_nome_duplicado(client: TestClient) -> None:
    _categoria(client, "Alimentos")
    outra = _categoria(client, "Higiene")
    assert client.post("/api/categorias", json={"nome": "Alimentos"}).status_code == 409
    assert client.put(f"/api/categorias/{outra}", json={"nome": "Alimentos"}).status_code == 409


def test_categoria_com_produto_ativo_nao_exclui(client: TestClient) -> None:
    cid = _categoria(client)
    p = _produto(client, cid)
    r = client.delete(f"/api/categorias/{cid}")
    assert r.status_code == 409
    assert r.json()["mensagem"] == f"Categoria {cid} possui produtos ativos vinculados"
    # Com o produto excluído, a categoria pode ser excluída
    assert client.delete(f"/api/produtos/{p['id']}").status_code == 204
    assert client.delete(f"/api/categorias/{cid}").status_code == 204


# ---------- Produto ----------


def test_produto_crud(client: TestClient) -> None:
    cid = _categoria(client)
    criado = _produto(client, cid, marca="Tio João")
    assert criado["saldo"] == 0
    assert criado["categoria"] == {"id": cid, "nome": "Alimentos"}
    assert criado["marca"] == "Tio João"
    pid = criado["id"]
    assert client.get(f"/api/produtos/{pid}").json() == criado
    assert client.get(f"/api/produtos/codigo/{ARROZ}").json() == criado

    outra = _categoria(client, "Grãos")
    r = client.put(
        f"/api/produtos/{pid}",
        json={
            "codigo_barras": ARROZ,
            "nome": "Arroz integral",
            "unidade": "5 kg",
            "categoria_id": outra,
        },
    )
    assert r.status_code == 200
    atualizado = r.json()
    assert atualizado["nome"] == "Arroz integral"
    assert atualizado["marca"] is None  # PUT substitui: campo omitido vira vazio
    assert atualizado["categoria"]["nome"] == "Grãos"
    assert atualizado["created_at"] == criado["created_at"]
    assert atualizado["updated_at"] > criado["updated_at"]
    assert len(client.get("/api/produtos", params={"categoria_id": outra}).json()) == 1

    assert client.delete(f"/api/produtos/{pid}").status_code == 204
    assert client.get(f"/api/produtos/{pid}").status_code == 404
    assert client.get(f"/api/produtos/codigo/{ARROZ}").status_code == 404
    assert client.get("/api/produtos").json() == []
    # Soft delete libera o código para recadastro
    _produto(client, cid)


def test_produto_sem_codigo_de_barras(client: TestClient) -> None:
    cid = _categoria(client)
    # "" vindo de formulário vira None; vários produtos podem ficar sem código
    a = _produto(client, cid, codigo_barras="", nome="Feijão a granel", unidade="", marca="  ")
    b = _produto(client, cid, codigo_barras=None, nome="Fubá a granel")
    assert a["codigo_barras"] is None and a["unidade"] is None and a["marca"] is None
    assert b["codigo_barras"] is None
    # Depois ganha um código
    r = client.put(
        f"/api/produtos/{a['id']}",
        json={"codigo_barras": ARROZ, "nome": "Feijão", "categoria_id": cid},
    )
    assert r.json()["codigo_barras"] == ARROZ


def test_produto_erros(client: TestClient) -> None:
    cid = _categoria(client)
    assert client.get(f"/api/produtos/codigo/{ARROZ}").status_code == 404
    pid = _produto(client, cid)["id"]
    dup = {"codigo_barras": ARROZ, "nome": "Outro", "categoria_id": cid}
    assert client.post("/api/produtos", json=dup).status_code == 409
    # Trocar para o código de OUTRO produto ativo também é conflito
    outro = _produto(client, cid, codigo_barras="12345678", nome="Leite")["id"]
    r = client.put(f"/api/produtos/{outro}", json=dup)
    assert r.status_code == 409

    r = client.put(f"/api/produtos/{pid}", json={"nome": "Arroz", "categoria_id": 999})
    assert r.status_code == 404

    r = client.get("/api/produtos/codigo/abc")
    assert r.status_code == 422
    assert r.json()["campos"][0]["campo"] == "path.codigo_barras"


def test_produto_com_saldo_nao_exclui(client: TestClient) -> None:
    cid = _categoria(client)
    pid = _produto(client, cid)["id"]
    _mov(client, pid, "ENTRADA", 3)
    r = client.delete(f"/api/produtos/{pid}")
    assert r.status_code == 409
    assert "saldo 3" in r.json()["mensagem"]
    # Zera com AJUSTE e então pode excluir
    assert _mov(client, pid, "AJUSTE", -3, "doado para outra instituição").status_code == 201
    assert client.delete(f"/api/produtos/{pid}").status_code == 204
    # Produto excluído não recebe movimentação
    assert _mov(client, pid, "ENTRADA", 1).status_code == 404


# ---------- Movimentação ----------


def test_movimentacao_registro_e_historico(client: TestClient) -> None:
    cid = _categoria(client)
    pid = _produto(client, cid)["id"]

    r = _mov(client, pid, "ENTRADA", 5)
    assert r.status_code == 201
    assert r.json()["saldo_atual"] == 5
    assert r.json()["produto_nome"] == "Arroz"
    entrada_id = r.json()["id"]

    r = _mov(client, pid, "SAIDA", -7, "cesta")
    assert r.json()["quantidade"] == -7
    assert r.json()["saldo_atual"] == -2
    assert r.json()["alerta_saldo_negativo"] is True

    historico = client.get("/api/movimentacoes", params={"produto_id": pid}).json()
    assert [m["tipo"] for m in historico] == ["SAIDA", "ENTRADA"]  # mais recente primeiro
    assert historico[0]["observacao"] == "cesta"
    assert len(client.get("/api/movimentacoes", params={"tipo": "ENTRADA"}).json()) == 1

    assert client.get(f"/api/movimentacoes/{entrada_id}").json()["quantidade"] == 5
    assert client.get("/api/movimentacoes/999").status_code == 404
    assert client.get(f"/api/produtos/{pid}").json()["saldo"] == -2
    assert client.get("/api/produtos").json()[0]["saldo"] == -2  # caminho da consulta agregada


def test_movimentacao_regras_de_quantidade(client: TestClient) -> None:
    assert _mov(client, 999, "ENTRADA", 1).status_code == 404
    pid = _produto(client, _categoria(client))["id"]

    invalidas = [
        ("ENTRADA", 0, None, "ENTRADA exige quantidade positiva"),
        ("ENTRADA", -1, None, "ENTRADA exige quantidade positiva"),
        ("SAIDA", 2, None, "SAIDA exige quantidade negativa"),
        ("AJUSTE", 0, "motivo", "AJUSTE não pode ter quantidade zero"),
        ("AJUSTE", 1, None, "AJUSTE exige observação"),
        ("AJUSTE", 1, "   ", "AJUSTE exige observação"),
    ]
    for tipo, qtd, obs, msg in invalidas:
        r = _mov(client, pid, tipo, qtd, obs)
        assert r.status_code == 422, (tipo, qtd, obs)
        assert msg in r.json()["campos"][0]["mensagem"]

    assert _mov(client, pid, "AJUSTE", 4, "contagem física").status_code == 201
    # Imutável: não existe PUT/DELETE
    assert client.delete("/api/movimentacoes/1").status_code == 405
    assert client.put("/api/movimentacoes/1", json={}).status_code == 405
