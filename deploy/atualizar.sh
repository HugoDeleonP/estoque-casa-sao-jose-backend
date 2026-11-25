#!/usr/bin/env bash
# Atualiza o sistema na EC2 para uma versão (tag) do backend e o build mais recente do front.
#   sudo /opt/estoque/backend/deploy/atualizar.sh v2.0.1
# Sem argumento, usa a tag mais recente do repositório.
# Faz backup antes, aplica migrações e reinicia; se o health falhar, avisa (não apaga nada).
set -euo pipefail
[ "$(id -u)" -eq 0 ] || exec sudo "$0" "$@"
APP=/opt/estoque

runuser -u estoque -- /usr/local/sbin/estoque-backup

cd "$APP/backend"
runuser -u estoque -- git fetch --tags --force origin
VERSAO="${1:-$(runuser -u estoque -- git tag --sort=-v:refname | head -n1)}"
runuser -u estoque -- git -c advice.detachedHead=false checkout --force "$VERSAO"
"$APP/venv/bin/pip" install --require-hashes -r requirements.lock
chown -R estoque:estoque "$APP/venv"

cd "$APP/front"
runuser -u estoque -- git fetch origin deploy
runuser -u estoque -- git reset --hard origin/deploy

install -m 755 "$APP/backend/deploy/configurar-dominio.sh" /usr/local/sbin/estoque-configurar-dominio
install -m 755 "$APP/backend/deploy/backup.sh" /usr/local/sbin/estoque-backup
install -m 755 "$APP/backend/deploy/estoque-python.sh" /usr/local/bin/estoque-python

estoque-python -m estoque_doacoes.scripts.seed   # migrações + dados iniciais
systemctl restart estoque
/usr/local/sbin/estoque-configurar-dominio

for _ in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:8000/api/health >/dev/null; then
    echo "Atualizado para $VERSAO. API respondendo."
    exit 0
  fi
  sleep 1
done
echo "ATENÇÃO: a API não respondeu após a atualização. Veja: journalctl -u estoque -n 100" >&2
exit 1
