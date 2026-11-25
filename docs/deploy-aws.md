# Deploy na AWS (EC2 + SQLite + Caddy)

Passo a passo para colocar o sistema na internet com HTTPS, numa única EC2 `t3.micro` em
São Paulo. Tempo estimado: **~1 h** na primeira vez.

> ⚠️ **Nunca use "Terminate" (Encerrar) na instância.** O banco fica no disco da instância
> e é **apagado junto**. Para desligar, use **"Stop" (Interromper)**. O Elastic IP mantém o
> endereço e o certificado depois de Stop/Start.

## 0. O que é implantado

| Item | Onde | Versão |
| --- | --- | --- |
| Backend | `/opt/estoque/backend` | tag `v2.0.0` do repositório do backend |
| Front | `/opt/estoque/front/dist` | branch `deploy` do repositório do front (build pronto) |
| Dependências Python | `/opt/estoque/venv` | `requirements.lock` (versões + hashes) |
| Banco | `/var/lib/estoque/estoque.db` | criado por migrações + seed |
| Configuração | `/etc/estoque/env` (600) | `SECRET_KEY` gerada na instância |
| Backups | `/var/backups/estoque/` | diário às 03:15, 14 cópias |

Os scripts estão em [`deploy/`](../deploy): `user-data.sh` (instalação), `atualizar.sh`,
`backup.sh`, `configurar-dominio.sh`, `estoque-python.sh`.

## 1. Conta e alerta de custo (F6.1)

1. Crie a conta em <https://aws.amazon.com> e conclua a verificação.
2. **Billing → Budgets → Create budget → "Zero spend budget"** (ou mensal de US$ 1) com o
   seu e-mail. Assim qualquer cobrança gera aviso.
3. No canto superior direito, selecione a região **América do Sul (São Paulo) `sa-east-1`**.

## 2. Lançar a instância (F6.6)

**EC2 → Instances → Launch instances**

| Campo | Valor |
| --- | --- |
| Name | `estoque-casa-sao-jose` |
| AMI | **Ubuntu Server 24.04 LTS** (x86) |
| Instance type | **t3.micro** |
| Key pair | *Proceed without a key pair* (o acesso é pelo EC2 Instance Connect) |
| Network → Security group | Criar: **SSH 22 — My IP**; **HTTP 80 — Anywhere**; **HTTPS 443 — Anywhere** (e a regra do Instance Connect abaixo) |
| Storage | 8–16 GiB gp3 (padrão serve) |
| Advanced details → **User data** | Cole o conteúdo **inteiro** de [`deploy/user-data.sh`](../deploy/user-data.sh) |

Clique em **Launch instance**.

**Regra extra para o EC2 Instance Connect (pelo navegador).** O Instance Connect do console
conecta a partir dos IPs da AWS, não do seu — só com "My IP" ele falha. Em **Security
Groups → (o grupo criado) → Edit inbound rules → Add rule**: Type **SSH**, Source **Custom**,
digite `com.amazonaws.sa-east-1.ec2-instance-connect` e escolha a *prefix list* sugerida.
Continua fechado para o resto da internet.

## 3. Elastic IP

1. **EC2 → Elastic IPs → Allocate Elastic IP address → Allocate**.
2. Selecione o IP → **Actions → Associate Elastic IP address** → escolha a instância → Associate.
3. **Reinicie a instância** (Instance state → **Reboot**). No boot, o script
   `estoque-configurar-dominio` lê o IP novo e o Caddy emite o certificado para ele.

Endereço do sistema: troque os pontos do Elastic IP por hífens e acrescente `.sslip.io`.
Ex.: IP `15.228.10.20` → **`https://15-228-10-20.sslip.io`**.

## 4. Conferir (F6.7)

Aguarde ~5 minutos após o boot e abra:

- `https://IP-COM-HIFENS.sslip.io/api/health` → `{"status":"ok", ...}` com cadeado válido.
- `https://IP-COM-HIFENS.sslip.io` → tela de login.

Se não abrir, conecte-se (passo 5) e veja:

```bash
sudo tail -n 50 /var/log/estoque-instalacao.log   # instalação
systemctl status estoque caddy                     # serviços
journalctl -u estoque -n 100                       # API
journalctl -u caddy -n 100                         # certificado / HTTPS
```

## 5. Primeiro ADMIN (F6.8)

**EC2 → Instances → selecione → Connect → EC2 Instance Connect → Connect** (abre um terminal
no navegador). Rode:

```bash
sudo estoque-python -m estoque_doacoes.scripts.criar_admin --nome "Seu Nome" --email seu@email.org
```

A senha é pedida no terminal (não aparece ao digitar). Depois, entre no sistema e crie os
demais usuários em **Administração → Usuários** (inclusive o login compartilhado da bancada,
perfil COMUM, ex.: `bancada@casasaojose.local`).

## 6. Atualizar para uma nova versão

No repositório: crie a tag (ex.: `v2.0.1`) no backend e publique o build novo na branch
`deploy` do front. Na instância (Instance Connect):

```bash
sudo /opt/estoque/backend/deploy/atualizar.sh v2.0.1
```

O script faz backup, troca a versão, instala dependências do lock, aplica migrações,
reinicia e confere o `/api/health`.

## 7. Backup e restauração

Automático todo dia às 03:15 (`/etc/cron.d/estoque-backup`), com `sqlite3 .backup`
(consistente mesmo com o sistema em uso) e `PRAGMA integrity_check`; guarda 14 cópias
compactadas.

```bash
sudo -u estoque /usr/local/sbin/estoque-backup     # backup manual agora
ls -lh /var/backups/estoque/                        # listar
```

**Restaurar** um backup:

```bash
sudo systemctl stop estoque
gunzip -k /var/backups/estoque/estoque-AAAAMMDD-HHMM.db.gz
sudo -u estoque cp /var/backups/estoque/estoque-AAAAMMDD-HHMM.db /var/lib/estoque/estoque.db
sudo rm -f /var/lib/estoque/estoque.db-wal /var/lib/estoque/estoque.db-shm
sudo systemctl start estoque
```

**Baixar uma cópia para fora da AWS** (recomendado semanalmente): no Instance Connect,
`sudo cat /var/backups/estoque/<arquivo>.db.gz | base64` e cole num arquivo local, ou
configure o S3 (ver [melhorias futuras](melhorias-futuras.md)).

> O backup fica no **mesmo disco**: protege contra erro lógico (exclusão indevida, dado
> errado), **não** contra perda do volume. Para isso: snapshot do EBS ou cópia para o S3.

## 8. Domínio próprio (opcional)

1. No provedor do domínio, crie um registro **A** apontando para o Elastic IP.
2. Na instância: `echo estoque.seudominio.org.br | sudo tee /etc/estoque/dominio` e
   `sudo estoque-configurar-dominio`.

## 9. Cuidados

| Situação | O que fazer |
| --- | --- |
| Desligar para economizar | **Stop**, nunca Terminate |
| Fim dos créditos / plano gratuito | Definir com a Casa quem fica com a conta (titularidade e cartão) |
| Esqueceu a senha do único ADMIN | `criar_admin` cria outro ADMIN pelo Instance Connect |
| Porta 22 | Só o seu IP e a prefix list do EC2 Instance Connect; nunca "Anywhere" |
| Login nunca por HTTP | O cookie é `Secure`; sem HTTPS válido o login não funciona — apresentar localmente (plano B) |

## Plano B: sem internet

Num notebook com o código: `./run_local.sh` no backend (com o front buildado ao lado) e
acesse `http://127.0.0.1:8000`.
