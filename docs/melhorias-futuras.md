# Melhorias futuras

Itens conscientemente deixados fora da entrega de 25/11/2026, em ordem sugerida.

| # | Melhoria | Por quê | Como (resumo) |
| --- | --- | --- | --- |
| 1 | **Backup externo** | O backup diário fica no mesmo disco da EC2: não protege contra perda do volume | Snapshot diário do EBS (Data Lifecycle Manager) **ou** `aws s3 cp` do `.db.gz` no `backup.sh` com um IAM role só de escrita no bucket |
| 2 | **Lotes e controle de validade** | Doações de alimentos vencem; hoje o vencimento só aparece como AJUSTE | Tabela `lote` (produto + validade) e `lote_id` em `movimentacao`; data de validade digitada na entrada; saída consome o lote que vence primeiro (FEFO); alertas de vencidos/a vencer no dashboard |
| 3 | **Domínio próprio** | Endereço mais fácil de lembrar que `*.sslip.io` | Registro A para o Elastic IP + `/etc/estoque/dominio` (ver [deploy-aws.md](deploy-aws.md)) |
| 4 | **Produtos sem código de barras** | Doação a granel, hortifrúti, itens sem rótulo | O banco já aceita `codigo_barras` nulo; falta a busca por nome na bancada e etiquetas internas |
| 5 | **Leitor 2D (imager)** | Leitores 1D a laser têm dificuldade com embalagens amassadas | Não muda o banco; só o validador de formato se forem lidos QR/DataMatrix |
| 6 | **Login individual na bancada** | O login compartilhado não diz quem bipou (D10, validar com os voluntários) | Já suportado: basta criar um usuário COMUM por voluntário |
| 7 | **Limite de tentativas de login** | Mitigar tentativa de senha por força bruta | Contador por e-mail/IP com bloqueio temporário (ex.: 5 tentativas / 15 min) |
| 8 | **Troca da própria senha** | Hoje só o ADMIN redefine senhas | `PUT /api/auth/senha` exigindo a senha atual |
| 9 | **Gestão de categorias pela tela** | A API já tem o CRUD (ADMIN); falta a tela | Mesma estrutura da tela de unidades |
| 10 | **Exportação para planilha** | Prestação de contas a doadores | CSV do histórico e do resumo por período |
| 11 | **Indicador de itens a vencer e metas** | Depende do item 2 | Cards no dashboard |
