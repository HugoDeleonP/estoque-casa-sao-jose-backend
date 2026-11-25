"""F3: login, sessão, matriz de permissões (D7, D8, D9) e gestão de usuários."""

import pytest
from fastapi.testclient import TestClient

from estoque_doacoes.main import app
from tests.conftest import ADMIN_EMAIL, COMUM_EMAIL, SENHA_ADMIN, SENHA_COMUM, login
from tests.test_crud import _categoria, _mov, _produto

# ---------- Login / sessão ----------


def test_login_logout_me(anonimo: TestClient) -> None:
    assert anonimo.get("/api/auth/me").status_code == 401
    r = anonimo.post("/api/auth/login", json={"email": " CHEFE@teste.org ", "senha": SENHA_ADMIN})
    assert r.status_code == 200
    assert r.json()["role"] == "ADMIN"
    assert "senha" not in r.text and "hash" not in r.text

    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie

    assert anonimo.get("/api/auth/me").json()["email"] == ADMIN_EMAIL
    assert anonimo.post("/api/auth/logout").status_code == 204
    assert anonimo.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize(
    ("email", "senha"),
    [(ADMIN_EMAIL, "senha-errada"), ("ninguem@teste.org", SENHA_ADMIN), (ADMIN_EMAIL, "")],
)
def test_login_invalido(anonimo: TestClient, email: str, senha: str) -> None:
    r = anonimo.post("/api/auth/login", json={"email": email, "senha": senha})
    assert r.status_code == 401
    assert r.json()["mensagem"] == "E-mail ou senha inválidos"


def test_cookie_adulterado_nao_autentica(anonimo: TestClient) -> None:
    anonimo.cookies.set("csj_sessao", "eyJ1c3VhcmlvIjogeyJpZCI6IDF9fQ==.forjado.assinatura")
    assert anonimo.get("/api/auth/me").status_code == 401


# ---------- Matriz de permissões ----------

ROTAS_PROTEGIDAS = [
    ("GET", "/api/produtos"),
    ("GET", "/api/categorias"),
    ("GET", "/api/unidades"),
    ("GET", "/api/movimentacoes"),
    ("POST", "/api/movimentacoes"),
    ("GET", "/api/dashboard/resumo"),
    ("GET", "/api/usuarios"),
]

SOMENTE_ADMIN = [
    ("GET", "/api/dashboard/resumo"),
    ("GET", "/api/dashboard/series"),
    ("GET", "/api/dashboard/pendencias"),
    ("GET", "/api/usuarios"),
    ("POST", "/api/usuarios"),
    ("PUT", "/api/usuarios/1/perfil"),
    ("PUT", "/api/usuarios/1/senha"),
    ("DELETE", "/api/usuarios/1"),
    ("POST", "/api/unidades"),
    ("PUT", "/api/unidades/1"),
    ("DELETE", "/api/unidades/1"),
    ("PUT", "/api/produtos/1"),
    ("DELETE", "/api/produtos/1"),
    ("POST", "/api/produtos/1/reativar"),
    ("POST", "/api/categorias"),
    ("DELETE", "/api/categorias/1"),
]


@pytest.mark.parametrize(("metodo", "rota"), ROTAS_PROTEGIDAS)
def test_sem_login_401(anonimo: TestClient, metodo: str, rota: str) -> None:
    assert anonimo.request(metodo, rota, json={}).status_code == 401


@pytest.mark.parametrize(("metodo", "rota"), SOMENTE_ADMIN)
def test_comum_em_rota_admin_403(comum: TestClient, metodo: str, rota: str) -> None:
    """RNF05: bloqueado também por URL direta, antes até de validar o corpo."""
    r = comum.request(metodo, rota, json={})
    assert r.status_code == 403, (metodo, rota, r.json())


def test_comum_opera_a_bancada(client: TestClient, comum: TestClient) -> None:
    """D8: todos cadastram produto e registram ENTRADA, SAÍDA e AJUSTE (com motivo)."""
    cid = _categoria(client)
    p = _produto(comum, cid)
    assert _mov(comum, p["id"], "ENTRADA", 3).status_code == 201
    assert _mov(comum, p["id"], "SAIDA", -1).status_code == 201
    assert _mov(comum, p["id"], "AJUSTE", -1, "avaria").status_code == 201
    assert _mov(comum, p["id"], "AJUSTE", -1).status_code == 422  # motivo obrigatório
    assert comum.get(f"/api/produtos/{p['id']}").json()["saldo"] == 1

    # F3.6: autoria registrada
    hist = comum.get("/api/movimentacoes", params={"produto_id": p["id"]}).json()
    assert {m["usuario_nome"] for m in hist} == {"Bancada"}


def test_admin_edita_codigo_de_barras(client: TestClient) -> None:
    """D9: ADMIN pode trocar o código de barras."""
    p = _produto(client, _categoria(client))
    dados = {
        "codigo_barras": "12345678",
        "nome": p["nome"],
        "conteudo_valor": 1,
        "unidade_medida_id": p["unidade_medida"]["id"],
        "categoria_id": p["categoria"]["id"],
    }
    r = client.put(f"/api/produtos/{p['id']}", json=dados)
    assert r.status_code == 200
    assert r.json()["codigo_barras"] == "12345678"


# ---------- Gestão de usuários ----------


def test_admin_cria_usuarios_inclusive_admin(client: TestClient) -> None:
    r = client.post(
        "/api/usuarios",
        json={
            "nome": "Outra chefe",
            "email": "Outra@Teste.org",
            "senha": "12345678",
            "role": "ADMIN",
        },
    )
    assert r.status_code == 201
    assert r.json()["email"] == "outra@teste.org"
    assert len(client.get("/api/usuarios").json()) == 3

    with TestClient(app) as c:
        login(c, "outra@teste.org", "12345678")
        assert c.get("/api/dashboard/resumo").status_code == 200

    dup = {"nome": "Xavier", "email": "outra@teste.org", "senha": "12345678"}
    assert client.post("/api/usuarios", json=dup).status_code == 409


@pytest.mark.parametrize(
    "dados",
    [
        {"nome": "A", "email": "a@b.c", "senha": "12345678"},  # nome curto
        {"nome": "Ana", "email": "sem-arroba", "senha": "12345678"},
        {"nome": "Ana", "email": "a@b.c", "senha": "1234567"},  # senha < 8
        {"nome": "Ana", "email": "a@b.c", "senha": "12345678", "role": "ROOT"},
    ],
)
def test_usuario_invalido_422(client: TestClient, dados: dict) -> None:
    assert client.post("/api/usuarios", json=dados).status_code == 422


def test_protecoes_do_admin(client: TestClient, ids: dict[str, int]) -> None:
    """F3.8: não desativa/rebaixa a si mesmo; sempre resta um ADMIN ativo."""
    eu = ids["admin"]
    r = client.delete(f"/api/usuarios/{eu}")
    assert r.status_code == 409
    assert "próprio" in r.json()["mensagem"]
    r = client.put(f"/api/usuarios/{eu}/perfil", json={"role": "COMUM"})
    assert r.status_code == 409

    # Com um segundo ADMIN, esse pode rebaixar o primeiro...
    client.post(
        "/api/usuarios",
        json={"nome": "Segunda", "email": "seg@teste.org", "senha": "12345678", "role": "ADMIN"},
    )
    with TestClient(app) as seg:
        login(seg, "seg@teste.org", "12345678")
        assert seg.put(f"/api/usuarios/{eu}/perfil", json={"role": "COMUM"}).status_code == 200
        # ...e a sessão antiga do primeiro perde o perfil na hora
        assert client.get("/api/usuarios").status_code == 401
        login(client, ADMIN_EMAIL, SENHA_ADMIN)
        assert client.get("/api/usuarios").status_code == 403

        # Último ADMIN não pode ser removido (nem por ele mesmo)
        segunda = next(u for u in seg.get("/api/usuarios").json() if u["email"] == "seg@teste.org")
        assert seg.delete(f"/api/usuarios/{segunda['id']}").status_code == 409


def test_ultimo_admin_nao_e_rebaixado(client: TestClient, ids: dict[str, int]) -> None:
    from estoque_doacoes.shared.database.db import SessionLocal
    from estoque_doacoes.shared.exception.Erros import Conflito
    from estoque_doacoes.usuario.domain.enum.Role import Role
    from estoque_doacoes.usuario.service.UsuarioService import UsuarioService

    with SessionLocal() as s:
        svc = UsuarioService(s)
        autor = svc.buscar(ids["comum"])  # mesmo que outro usuário tente
        with pytest.raises(Conflito, match="ao menos um ADMIN"):
            svc.alterar_perfil(ids["admin"], Role.COMUM, autor)


def test_desativado_perde_acesso_na_hora(client: TestClient, comum: TestClient, ids) -> None:
    assert comum.get("/api/produtos").status_code == 200
    assert client.delete(f"/api/usuarios/{ids['comum']}").status_code == 204
    assert comum.get("/api/produtos").status_code == 401
    r = comum.post("/api/auth/login", json={"email": COMUM_EMAIL, "senha": SENHA_COMUM})
    assert r.status_code == 401


def test_redefinir_senha(client: TestClient, comum: TestClient, ids) -> None:
    r = client.put(f"/api/usuarios/{ids['comum']}/senha", json={"senha": "nova-senha-99"})
    assert r.status_code == 204
    assert comum.get("/api/produtos").status_code == 401  # sessão encerrada
    r = comum.post("/api/auth/login", json={"email": COMUM_EMAIL, "senha": SENHA_COMUM})
    assert r.status_code == 401
    login(comum, COMUM_EMAIL, "nova-senha-99")
