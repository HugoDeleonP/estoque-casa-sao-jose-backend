# Backend — Estoque de Doações (Casa São José)

FastAPI + SQLAlchemy 2.0 + SQLite, gerenciado com **[uv](https://docs.astral.sh/uv/)**.

## Setup (uma vez por máquina)

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

cd backend
cp .env.example .env      # Windows: copy .env.example .env
uv sync                   # cria .venv, baixa Python 3.12 se preciso, instala tudo do uv.lock
```

## Dia a dia

| Tarefa | Comando |
| --- | --- |
| Subir a API (reload ligado se `ESTOQUE_DEBUG=true`) | `uv run estoque-doacoes` |
| Swagger | http://127.0.0.1:8000/docs |
| Testes | `uv run pytest` |
| Lint / formatação | `uv run ruff check . --fix` · `uv run ruff format .` |
| Adicionar lib de runtime | `uv add <pacote>` |
| Adicionar lib só de dev | `uv add --dev <pacote>` |
| Ligar autenticação (pós-MVP) | `uv sync --extra auth` |

**Regra da equipe:** nunca `pip install` dentro do `.venv`. Sempre `uv add` — senão o
`pyproject.toml`/`uv.lock` não registram a dependência e a máquina do colega quebra.
`uv.lock` **vai para o Git**; `.venv/` e `.env` não.

## Instalação na máquina da ONG

```bash
uv sync --no-dev --frozen   # só runtime (~22 pacotes, ~30 MB), versões exatas do lock
uv run estoque-doacoes
```

`--frozen` falha se o lock estiver desatualizado em vez de resolver versões novas na hora —
o que roda na bancada é byte a byte o que foi testado.

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
- **Auth como extra opcional, com `pwdlib[argon2]` em vez de `passlib`** — o `passlib` não é
  mantido desde 2020 e quebra com `bcrypt>=4.1`. *Implicação:* o doc de viabilidade cita
  `passlib`/bcrypt; atualizar a stack documentada.
- **`httpx2` no dev** — o Starlette 1.x deprecou o `httpx` clássico no `TestClient`.

## Estrutura do código

Arquitetura modular: uma pasta por funcionalidade, todas com as mesmas camadas.

```
src/estoque_doacoes/
├── main.py                 # cria o app, registra routers e o handler global de erros
├── migrar.py               # aplica migrações do Alembic ao subir
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
