#!/usr/bin/env bash
# Plano B (F7.4): o sistema inteiro num notebook, sem internet.
#   ./run_local.sh            → http://127.0.0.1:8000
# Requisitos: uv; o front ao lado (../estoque-casa-sao-jose-front) com dist/ pronto
# (npm run build, ou git clone --branch deploy). Primeiro ADMIN local:
#   uv run python -m estoque_doacoes.scripts.criar_admin --nome "..." --email ...
set -euo pipefail
cd "$(dirname "$0")"
FRONT_DIST="${ESTOQUE_FRONT_DIST:-$(cd .. && pwd)/estoque-casa-sao-jose-front/dist}"
if [ ! -f "$FRONT_DIST/index.html" ]; then
  echo "Build do front não encontrado em $FRONT_DIST" >&2
  echo "Rode 'npm ci && npm run build' no repositório do front." >&2
  exit 1
fi
export ESTOQUE_FRONT_DIST="$FRONT_DIST" ESTOQUE_DEBUG=false ESTOQUE_COOKIE_SECURE=false
uv sync --frozen --no-dev --inexact  # não remove ferramentas de dev já instaladas
uv run --no-dev python -m estoque_doacoes.scripts.seed
# Porta real: variável de ambiente, senão o .env, senão 8000
PORTA="$(uv run --no-dev python -c 'from estoque_doacoes.shared.database.config import settings; print(settings.port)')"
echo "Abra http://127.0.0.1:$PORTA"
exec uv run --no-dev estoque-doacoes
