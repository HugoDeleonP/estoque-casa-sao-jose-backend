#!/usr/bin/env bash
# Backup consistente do SQLite (API rodando, modo WAL): usa a API de backup do SQLite,
# nunca uma cópia simples do arquivo. Mantém as 14 cópias mais recentes.
#
# Restaurar (ver docs/deploy-aws.md):
#   sudo systemctl stop estoque
#   sudo -u estoque cp /var/backups/estoque/estoque-AAAAMMDD-HHMM.db /var/lib/estoque/estoque.db
#   sudo rm -f /var/lib/estoque/estoque.db-wal /var/lib/estoque/estoque.db-shm
#   sudo systemctl start estoque
set -euo pipefail
DB="${ESTOQUE_DB_PATH:-/var/lib/estoque/estoque.db}"
DESTINO="${ESTOQUE_BACKUP_DIR:-/var/backups/estoque}"
MANTER="${ESTOQUE_BACKUP_MANTER:-14}"

ARQ="$DESTINO/estoque-$(date +%Y%m%d-%H%M).db"
sqlite3 "$DB" ".timeout 10000" ".backup '$ARQ'"
# Confere o backup antes de apagar os antigos
[ "$(sqlite3 "$ARQ" 'PRAGMA integrity_check;')" = "ok" ] || { echo "Backup corrompido: $ARQ"; exit 1; }
gzip -f "$ARQ"
ls -1t "$DESTINO"/estoque-*.db.gz | tail -n +$((MANTER + 1)) | xargs -r rm -f
echo "$(date -Is) backup ok: $ARQ.gz"
