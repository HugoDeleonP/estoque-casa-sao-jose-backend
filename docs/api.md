# API

Base: `/api` (mesmo domínio do front). Documentação interativa gerada pelo FastAPI em
**`/docs`** (Swagger) — este arquivo resume permissões e regras que o Swagger não mostra.

## Autenticação

Sessão por **cookie assinado** `csj_sessao` (`HttpOnly`, `SameSite=Lax`, `Secure` em
produção, validade de 12 h). O navegador envia o cookie sozinho; não há token.

```http
POST /api/auth/login
Content-Type: application/json

{"email": "chefe@exemplo.org", "senha": "********"}
```

| Rota | Descrição |
| --- | --- |
| `POST /api/auth/login` | 200 + usuário; 401 "E-mail ou senha inválidos" (mesma resposta para e-mail inexistente) |
| `POST /api/auth/logout` | 204; encerra a sessão |
| `GET /api/auth/me` | Usuário logado; 401 sem sessão |

Sessão de usuário desativado, com senha redefinida ou perfil alterado é recusada (401) já na
requisição seguinte.

## Permissões por perfil

**COMUM** = voluntário da bancada · **ADMIN** = voluntário chefe. Sem login → **401**; perfil
sem acesso → **403** (inclusive acessando a URL diretamente).

| Recurso | COMUM | ADMIN |
| --- | :-: | :-: |
| Listar/consultar produtos, categorias, unidades, movimentações | ✅ | ✅ |
| Cadastrar produto | ✅ | ✅ |
| Registrar ENTRADA, SAÍDA e AJUSTE (motivo obrigatório) | ✅ | ✅ |
| Consultar produto excluído pelo código | ✅ | ✅ |
| Editar produto (inclusive o código de barras), excluir, reativar | — | ✅ |
| Criar/editar/excluir unidades e categorias | — | ✅ |
| Gestão de usuários | — | ✅ |
| Dashboard | — | ✅ |
| `GET /api/health` | público | público |

## Endpoints

### Produtos — `/api/produtos`

| Método e rota | Perfil | Notas |
| --- | :-: | --- |
| `GET /api/produtos?categoria_id=` | todos | Ativos, com `saldo` |
| `GET /api/produtos/{id}` | todos | 404 se excluído |
| `GET /api/produtos/codigo/{codigo}` | todos | Chamado a cada bip; 404 → cadastro |
| `GET /api/produtos/excluidos/codigo/{codigo}` | todos | Último excluído com o código (oferecer reativação) |
| `POST /api/produtos` | todos | 201; 409 código duplicado; 422 conteúdo ≤ 0 ou unidade inexistente |
| `PUT /api/produtos/{id}` | ADMIN | Substitui todos os campos |
| `DELETE /api/produtos/{id}` | ADMIN | 204; 409 se saldo ≠ 0 |
| `POST /api/produtos/{id}/reativar` | ADMIN | 409 se o código já está em outro produto ativo |

```json
// POST /api/produtos
{
  "codigo_barras": "7891000315507",
  "nome": "Feijão carioca",
  "marca": "Camil",
  "conteudo_valor": 1,
  "unidade_medida_id": 1,
  "categoria_id": 1
}
// 201
{
  "id": 7, "codigo_barras": "7891000315507", "nome": "Feijão carioca", "marca": "Camil",
  "conteudo_valor": 1.0,
  "unidade_medida": {"id": 1, "sigla": "kg", "nome": "quilograma", "grandeza": "MASSA", "fator_base": 1.0},
  "categoria": {"id": 1, "nome": "Alimentos"},
  "saldo": 0, "created_at": "...", "updated_at": "..."
}
```

### Movimentações — `/api/movimentacoes`

Imutáveis: não há `PUT` nem `DELETE` (405).

| Método e rota | Perfil | Notas |
| --- | :-: | --- |
| `GET /api/movimentacoes?produto_id=&tipo=&limite=` | todos | Mais recentes primeiro; `usuario_nome` = autor |
| `GET /api/movimentacoes/{id}` | todos | — |
| `POST /api/movimentacoes` | todos | Retorna `saldo_atual` e `alerta_saldo_negativo` |

```json
// POST — saída de 2 embalagens (quantidade NEGATIVA)
{"produto_id": 7, "tipo": "SAIDA", "quantidade": -2}
// AJUSTE exige observação (motivo)
{"produto_id": 7, "tipo": "AJUSTE", "quantidade": -1, "observacao": "Avaria"}
```

| Tipo | Quantidade | Observação |
| --- | --- | --- |
| ENTRADA | > 0 | opcional |
| SAIDA | < 0 | opcional |
| AJUSTE | ≠ 0 | **obrigatória** |

### Unidades de medida — `/api/unidades`

| Método e rota | Perfil | Notas |
| --- | :-: | --- |
| `GET /api/unidades` | todos | Ativas, com `em_uso` |
| `POST /api/unidades` | ADMIN | `{sigla, nome, grandeza, fator_base}`; 409 sigla repetida (sem diferenciar maiúsculas) |
| `PUT /api/unidades/{id}` | ADMIN | Em uso: só `nome` muda (409 para sigla, grandeza ou fator) |
| `DELETE /api/unidades/{id}` | ADMIN | 409 se em uso |

### Categorias — `/api/categorias`

`GET` (todos) · `POST`, `PUT /{id}`, `DELETE /{id}` (ADMIN; 409 com produto ativo).

### Usuários — `/api/usuarios` (ADMIN)

| Método e rota | Notas |
| --- | --- |
| `GET /api/usuarios` | Ativos |
| `POST /api/usuarios` | `{nome, email, senha (≥ 8), role}`; ADMIN pode criar ADMIN; 409 e-mail em uso |
| `PUT /api/usuarios/{id}/perfil` | `{role}`; 409 no próprio perfil ou ao rebaixar o último ADMIN |
| `PUT /api/usuarios/{id}/senha` | `{senha}`; encerra as sessões do usuário |
| `DELETE /api/usuarios/{id}` | Desativa; 409 em si mesmo ou no último ADMIN |

### Dashboard — `/api/dashboard` (ADMIN)

Parâmetros: `inicio`, `fim` (AAAA-MM-DD, fuso de Brasília; padrão: últimos 30 dias, máx. 366)
e `categoria_id`. AJUSTE nunca entra em entradas/saídas.

| Rota | Retorno |
| --- | --- |
| `GET /api/dashboard/resumo` | `saldo_total`, `total_produtos`, `produtos_saldo_negativo` (estoque atual) · `total_entradas`, `total_saidas` (embalagens no período) · `estoque_grandeza`, `entradas_grandeza`, `saidas_grandeza` (`massa_kg`, `volume_l`, `contagem_un`) |
| `GET /api/dashboard/series` | Um ponto por dia: `{data, entradas, saidas}` |
| `GET /api/dashboard/pendencias` | Produtos ativos com saldo negativo |

Entradas e saídas do período incluem produtos excluídos depois (a doação aconteceu); o
estoque atual considera só produtos ativos.

## Formato de erro

Todo erro tem o mesmo corpo:

```json
{
  "timestamp": "2026-11-25T19:02:11Z",
  "status": 422,
  "erro": "Unprocessable Content",
  "mensagem": "Dados inválidos",
  "caminho": "/api/produtos",
  "campos": [{"campo": "conteudo_valor", "mensagem": "Input should be greater than 0"}]
}
```

| Status | Quando |
| --- | --- |
| 401 | Sem sessão, sessão expirada ou credenciais inválidas |
| 403 | Perfil sem acesso |
| 404 | Recurso inexistente ou excluído |
| 409 | Conflito de regra (código duplicado, saldo ≠ 0, último ADMIN, unidade em uso…) |
| 422 | Dados inválidos (campos) ou referência inválida (unidade inexistente) |
