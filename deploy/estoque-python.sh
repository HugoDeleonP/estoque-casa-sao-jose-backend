#!/usr/bin/env bash
# Roda o Python da aplicação como o usuário de serviço, com a mesma configuração da API.
#   sudo estoque-python -m estoque_doacoes.scripts.criar_admin --nome "..." --email ...
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then exec sudo "$0" "$@"; fi
set -a
# shellcheck disable=SC1091
source /etc/estoque/env
set +a
cd /opt/estoque/backend
exec runuser -u estoque -- /opt/estoque/venv/bin/python "$@"
