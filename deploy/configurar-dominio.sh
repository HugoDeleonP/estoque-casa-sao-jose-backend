#!/usr/bin/env bash
# Gera /etc/caddy/Caddyfile para o endereço público atual.
#
# Padrão (D13): IP-COM-HIFENS.sslip.io, lido do serviço de metadados da EC2 (IMDSv2) a
# cada boot — assim, depois de associar o Elastic IP, basta reiniciar a instância (ou
# rodar este script) e o Caddy emite o certificado para o endereço novo.
# Domínio próprio: escreva-o em /etc/estoque/dominio (ex.: estoque.casasaojose.org.br).
set -euo pipefail

if [ -s /etc/estoque/dominio ]; then
  DOMINIO="$(tr -d '[:space:]' < /etc/estoque/dominio)"
else
  TOKEN="$(curl -fsS -X PUT http://169.254.169.254/latest/api/token \
    -H 'X-aws-ec2-metadata-token-ttl-seconds: 60')"
  IP="$(curl -fsS -H "X-aws-ec2-metadata-token: $TOKEN" \
    http://169.254.169.254/latest/meta-data/public-ipv4)"
  DOMINIO="${IP//./-}.sslip.io"
fi

NOVO="$(mktemp)"
cat > "$NOVO" <<CADDY
# Gerado por estoque-configurar-dominio — não editar à mão
$DOMINIO {
	encode zstd gzip

	header {
		Strict-Transport-Security "max-age=31536000"
		X-Content-Type-Options "nosniff"
		X-Frame-Options "DENY"
		Referrer-Policy "same-origin"
		-Server
	}

	# API e documentação interativa (Swagger) → FastAPI
	@api path /api/* /docs /docs/* /openapi.json
	handle @api {
		reverse_proxy 127.0.0.1:8000
	}

	# Front (Vue, history mode): arquivo existente ou index.html
	handle {
		root * /opt/estoque/front/dist
		try_files {path} /index.html
		file_server
		@assets path /assets/*
		header @assets Cache-Control "public, max-age=31536000, immutable"
	}

	log {
		output file /var/log/caddy/estoque.log {
			roll_keep 5
		}
	}
}
CADDY

if ! cmp -s "$NOVO" /etc/caddy/Caddyfile 2>/dev/null; then
  install -m 644 "$NOVO" /etc/caddy/Caddyfile
  systemctl reload caddy 2>/dev/null || true
fi
rm -f "$NOVO"
echo "Endereço público: https://$DOMINIO"
