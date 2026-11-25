#!/usr/bin/env bash
# =============================================================================
# Estoque de Doações — Casa São José · instalação na EC2 (cloud-init / user-data)
#
# Ubuntu 24.04 (t3.micro, sa-east-1). Cole este arquivo INTEIRO no campo "User data"
# ao lançar a instância. Não precisa de SSH: em ~5 min o sistema responde em
#   https://IP-COM-HIFENS.sslip.io   (ex.: https://15-228-10-20.sslip.io)
#
# Arquitetura (plano F6, D2/D13):
#   Internet ─HTTPS─▶ Caddy :443 ─┬─ /api/*, /docs ─▶ uvicorn 127.0.0.1:8000 (1 worker)
#                                 └─ /*            ─▶ build do front (arquivos estáticos)
#   FastAPI ─▶ SQLite em /var/lib/estoque/estoque.db (disco EBS da instância)
#
# Log desta instalação: /var/log/estoque-instalacao.log
# Nenhuma senha aqui: a SECRET_KEY é gerada na própria instância e o primeiro ADMIN é
# criado depois, via EC2 Instance Connect (python -m estoque_doacoes.scripts.criar_admin).
# =============================================================================
set -euxo pipefail
exec > >(tee -a /var/log/estoque-instalacao.log) 2>&1

# Versões implantadas (tag do backend; branch "deploy" do front tem o build pronto)
BACKEND_REPO="https://github.com/HugoDeleonP/estoque-casa-sao-jose-backend.git"
BACKEND_REF="v2.0.0"
FRONT_REPO="https://github.com/HugoDeleonP/estoque-casa-sao-jose-front.git"
FRONT_REF="deploy"

APP=/opt/estoque
DADOS=/var/lib/estoque
BACKUPS=/var/backups/estoque
ETC=/etc/estoque
export DEBIAN_FRONTEND=noninteractive

# ---------- Pacotes ----------
apt-get update
apt-get install -y git sqlite3 curl python3-venv debian-keyring debian-archive-keyring apt-transport-https gnupg
# Caddy pelo repositório oficial (HTTPS automático com Let's Encrypt)
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  > /etc/apt/sources.list.d/caddy-stable.list
apt-get update
apt-get install -y caddy

# ---------- Swap (t3.micro tem 1 GB de RAM; evita OOM em picos) ----------
if [ ! -f /swapfile ]; then
  fallocate -l 1G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# ---------- Usuário de serviço e pastas ----------
id estoque >/dev/null 2>&1 || useradd --system --home-dir "$APP" --shell /usr/sbin/nologin estoque
mkdir -p "$APP" "$DADOS" "$BACKUPS" "$ETC"
chown estoque:estoque "$DADOS" "$BACKUPS"
chmod 750 "$DADOS" "$BACKUPS"

# ---------- Código ----------
[ -d "$APP/backend/.git" ] || git clone --depth 1 --branch "$BACKEND_REF" "$BACKEND_REPO" "$APP/backend"
[ -d "$APP/front/.git" ]   || git clone --depth 1 --branch "$FRONT_REF" "$FRONT_REPO" "$APP/front"

# Dependências com versões e hashes exatos (requirements.lock): nada é resolvido aqui
python3 -m venv "$APP/venv"
"$APP/venv/bin/pip" install --upgrade pip
"$APP/venv/bin/pip" install --require-hashes -r "$APP/backend/requirements.lock"
chown -R estoque:estoque "$APP"

# ---------- Configuração (SECRET_KEY gerada aqui, permissão 600) ----------
if [ ! -f "$ETC/env" ]; then
  umask 077
  cat > "$ETC/env" <<CONF
ESTOQUE_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
ESTOQUE_DB_PATH=$DADOS/estoque.db
ESTOQUE_HOST=127.0.0.1
ESTOQUE_PORT=8000
ESTOQUE_DEBUG=false
ESTOQUE_COOKIE_SECURE=true
PYTHONPATH=$APP/backend/src
CONF
  chmod 600 "$ETC/env"
fi

# ---------- Banco: migrações + dados iniciais (idempotente) ----------
install -m 755 "$APP/backend/deploy/estoque-python.sh" /usr/local/bin/estoque-python
estoque-python -m estoque_doacoes.scripts.seed

# ---------- Serviço da API ----------
cat > /etc/systemd/system/estoque.service <<UNIT
[Unit]
Description=Estoque de Doações — API (FastAPI/uvicorn)
After=network-online.target
Wants=network-online.target

[Service]
User=estoque
Group=estoque
EnvironmentFile=$ETC/env
WorkingDirectory=$APP/backend
# UM worker: o SQLite aceita um escritor por vez; com um processo não há disputa de lock
ExecStart=$APP/venv/bin/uvicorn estoque_doacoes.main:app --host 127.0.0.1 --port 8000 --workers 1 --proxy-headers --forwarded-allow-ips 127.0.0.1
Restart=always
RestartSec=3
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DADOS $BACKUPS
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT

# ---------- Domínio sslip.io + Caddy ----------
install -m 755 "$APP/backend/deploy/configurar-dominio.sh" /usr/local/sbin/estoque-configurar-dominio
cat > /etc/systemd/system/estoque-dominio.service <<UNIT
[Unit]
Description=Estoque — gera o Caddyfile com o IP público atual (sslip.io)
After=network-online.target
Wants=network-online.target
Before=caddy.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/estoque-configurar-dominio

[Install]
WantedBy=multi-user.target
UNIT

# ---------- Backup diário (sqlite3 .backup, 14 cópias) ----------
install -m 755 "$APP/backend/deploy/backup.sh" /usr/local/sbin/estoque-backup
cat > /etc/cron.d/estoque-backup <<CRON
# Backup consistente do SQLite às 03:15 (horário de Brasília), mesmo com o sistema em uso
CRON_TZ=America/Sao_Paulo
15 3 * * * estoque /usr/local/sbin/estoque-backup >> /var/log/estoque-backup.log 2>&1
CRON
touch /var/log/estoque-backup.log && chown estoque:estoque /var/log/estoque-backup.log

systemctl daemon-reload
systemctl enable --now estoque.service
systemctl enable estoque-dominio.service
/usr/local/sbin/estoque-configurar-dominio
systemctl enable caddy
systemctl restart caddy

echo "Instalação concluída. Próximo passo: criar o primeiro ADMIN (ver docs/deploy-aws.md)."
