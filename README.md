# Backend — Estoque de Doações (Casa São José)

API do sistema de gestão e rastreabilidade de doações da Casa São José: voluntários bipam as
embalagens na bancada, cada leitura vira uma movimentação imutável e o voluntário chefe
acompanha os indicadores no dashboard. Login com perfis ADMIN/COMUM, unidades de medida
configuráveis e implantação numa EC2 com SQLite.

FastAPI + SQLAlchemy 2.0 + SQLite, gerenciado com **[uv](https://docs.astral.sh/uv/)**.
Front: [estoque-casa-sao-jose-front](https://github.com/HugoDeleonP/estoque-casa-sao-jose-front).

## Documentação

| Documento | Conteúdo |
| --- | --- |
| [docs/arquitetura.md](docs/arquitetura.md) | Visão geral, stack, decisões e diagrama |
| [docs/modelo-de-dados.md](docs/modelo-de-dados.md) | Entidades, regras, diagramas de classes e ER |
| [docs/api.md](docs/api.md) | Endpoints, permissões por perfil, exemplos (Swagger em `/docs`) |
| [docs/deploy-aws.md](docs/deploy-aws.md) | Console AWS passo a passo, atualização, backup e restauração |
| [docs/manual-do-usuario.md](docs/manual-do-usuario.md) | Guia para voluntários e voluntário chefe |
| [docs/melhorias-futuras.md](docs/melhorias-futuras.md) | Lotes e validade, backup externo, domínio próprio… |

## Setup (uma vez por máquina)

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

cd estoque-casa-sao-jose-backend
cp .env.example .env      # Windows: copy .env.example .env
uv sync                   # cria .venv, baixa Python 3.12 se preciso, instala tudo do uv.lock
uv run python -m estoque_doacoes.scripts.seed        # migrações + unidades e categorias iniciais
uv run python -m estoque_doacoes.scripts.criar_admin --nome "Seu Nome" --email voce@exemplo.org
```

O `criar_admin` pede a senha no terminal (nunca por argumento). Os demais usuários são
criados pela tela **Usuários**.

## Dia a dia

| Tarefa | Comando |
| --- | --- |
| Subir a API (reload ligado se `ESTOQUE_DEBUG=true`) | `uv run estoque-doacoes` |
| Swagger | http://127.0.0.1:8000/docs |
| Testes da API | `uv run pytest` |
| Teste ponta a ponta (leitor simulado) | no front: `npm run build && npm run test:e2e` |
| Sistema completo local (plano B) | `./run_local.sh` → http://127.0.0.1:8000 |
| Lint / formatação | `uv run ruff check . --fix` · `uv run ruff format .` |
| Adicionar lib de runtime | `uv add <pacote>` |
| Adicionar lib só de dev | `uv add --dev <pacote>` |
| Atualizar o lock de produção | `uv export --no-dev --frozen --no-emit-project -o requirements.lock` |

**Regra da equipe:** nunca `pip install` dentro do `.venv`. Sempre `uv add` — senão o
`pyproject.toml`/`uv.lock` não registram a dependência e a máquina do colega quebra.
`uv.lock` **vai para o Git**; `.venv/` e `.env` não.

## Configuração (variáveis `ESTOQUE_*`)

| Variável | Padrão | Para quê |
| --- | --- | --- |
| `ESTOQUE_DB_PATH` | `data/estoque.db` | Arquivo SQLite |
| `ESTOQUE_SECRET_KEY` | aleatória por processo | Assina o cookie de sessão. **Obrigatória em produção** (gerada pelo `user-data.sh`) |
| `ESTOQUE_COOKIE_SECURE` | `false` | `true` em produção (HTTPS) |
| `ESTOQUE_SESSAO_HORAS` | `12` | Validade da sessão |
| `ESTOQUE_BCRYPT_ROUNDS` | `12` | Custo do hash de senha |
| `ESTOQUE_FRONT_DIST` | — | Pasta do build do front a servir pela API (dev/plano B) |
| `ESTOQUE_HOST` / `ESTOQUE_PORT` / `ESTOQUE_DEBUG` | `127.0.0.1` / `8000` / `false` | Servidor |

## Produção

AWS EC2 `t3.micro` (`sa-east-1`) com SQLite no disco, Caddy (HTTPS automático via
sslip.io) e backup diário — ver [docs/deploy-aws.md](docs/deploy-aws.md). A instância
instala as dependências de `requirements.lock` (versões e hashes exatos) sem resolver nada.

## Decisões e implicações

- **uv em vez de venv + pip + requirements.txt** — um binário só, cria/gerencia o `.venv`,
  gera lockfile multiplataforma (Windows/Linux com o mesmo `uv.lock`) e instala Python se a
  máquina não tiver. *Implicação:* cada dev precisa instalar o `uv`; o `.venv` gerado ainda é
  um venv padrão, então VS Code/PyCharm enxergam normalmente. Saída de emergência: `uv export
  --no-dev > requirements.txt` gera um requirements para usar com pip puro.
- **Sem `fastapi[standard]`** — o extra traz CLI, Jinja2, email-validator, uvloop, watchfiles,
  websockets… que o projeto não usa na bancada. Em runtime fica só `uvicorn` puro; o
  `uvicorn[standard]` (com `--reload`) está só no grupo `dev`. *Implicação:* em produção o
  servidor usa asyncio/h11 puros — mais lento em benchmark, irrelevante para 1–3 usuários.
- **Python `>=3.12,<3.14`** — teto evita que uma versão nova sem wheels quebre a instalação.
- **SQLite com `foreign_keys=ON`, WAL e `busy_timeout`** (em `shared/database/db.py`) — sem o PRAGMA, o
  SQLite ignora FOREIGN KEY silenciosamente. WAL cria arquivos `estoque.db-wal`/`-shm` ao
  lado do banco: **backup = copiar com o servidor parado** (ou `sqlite3 estoque.db ".backup x.db"`).
- **Alembic desde já** — o schema vai mudar (Usuário/Role pós-MVP, validade). SQLite não
  suporta a maioria dos `ALTER TABLE`; o Alembic precisa de `render_as_batch=True` no `env.py`.
- **`bcrypt` direto, sem `passlib`** — o `passlib` não é mantido desde 2020 e quebra com
  `bcrypt>=4.1`. Sessão em cookie assinado (`itsdangerous`, via `SessionMiddleware`).
- **`httpx2` no dev** — o Starlette 1.x deprecou o `httpx` clássico no `TestClient`.

## Estrutura do código

Arquitetura modular: uma pasta por funcionalidade, todas com as mesmas camadas.

```
src/estoque_doacoes/
├── main.py                 # cria o app, sessão, routers e o handler global de erros
├── migrar.py               # aplica migrações do Alembic ao subir
├── seed.py                 # dados iniciais idempotentes (unidades, categorias)
├── scripts/                # criar_admin (primeiro ADMIN), seed
├── auth/                   # login/logout/me, usuario_atual, require_role, bcrypt
├── usuario/  unidade/  dashboard/   # mesmo padrão de camadas
├── migrations/             # scripts do Alembic (env.py importa a entidade de cada módulo)
├── shared/                 # usado por vários módulos; NÃO importa módulos de negócio
│   ├── database/           # config.py (settings/.env), db.py (engine, Base, get_session, agora)
│   ├── exception/          # Erros.py, ErroDTO.py, GlobalExceptionHandler.py (@RestControllerAdvice)
│   └── validation/         # tipos.py (CodigoBarras)
├── categoria/
│   ├── domain/
│   │   ├── entity/         # Categoria.py
│   │   └── exception/      # CategoriaDuplicada, CategoriaEmUso, CategoriaNaoEncontrada
│   ├── controller/         # CategoriaController.py
│   ├── dto/                # CategoriaDTO.py
│   ├── repository/         # CategoriaRepository.py
│   └── service/            # CategoriaService.py
├── produto/                # mesmo padrão (domain/entity, domain/exception, controller, …)
└── movimentacao/           # mesmo padrão + domain/enum/TipoMovimentacao.py
```

Módulo novo com tabela → criar a pasta no mesmo padrão, registrar o router no `main.py` e
importar a entidade no `migrations/env.py`.
