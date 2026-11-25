# Manual do usuário

Guia para os voluntários da **Casa São José**. Há dois perfis:

| Perfil | Quem | O que faz |
| --- | --- | --- |
| **Voluntário (COMUM)** | Bancada de triagem | Bipa doações e entregas, cadastra produtos novos, consulta o catálogo e o histórico, registra ajustes |
| **Voluntário chefe (ADMIN)** | Coordenação | Tudo acima + edita/exclui/reativa produtos, gerencia unidades de medida e usuários e vê o dashboard |

## 1. Entrar

1. Abra o endereço do sistema no navegador.
2. Digite **e-mail** e **senha** e clique em **Entrar**.
3. Esqueceu a senha? Peça ao voluntário chefe para redefini-la em *Usuários*.

A sessão dura 12 horas. Se ela expirar no meio do trabalho, o sistema pede o login de novo
e **volta para a mesma tela**. Ao terminar, clique em **Sair** (no menu lateral).

## 2. Bancada: bipar doações e entregas

1. No menu, **Bancada (leitor)**.
2. Escolha **Entrada** (doação recebida) ou **Saída** (entregue às famílias). A borda do
   quadro muda de cor para lembrar o modo.
3. Passe a embalagem no leitor. Pronto: a linha aparece em *Leituras desta sessão* com o
   saldo atualizado.

Dicas:

- **Várias embalagens iguais?** Digite a quantidade em *Embalagens* antes de bipar. Ela
  volta para 1 depois de cada leitura.
- **Não precisa clicar no campo**: ele fica sempre pronto para o leitor
  (*● Leitor pronto*). Se aparecer *○ Clique aqui para ativar o leitor*, clique nessa faixa.
- **Bip duplo** do leitor (o mesmo código duas vezes em menos de 0,3 s) é ignorado.
- **"Não registrado — leia novamente"** em vermelho: a leitura **não** foi gravada (sem
  internet, por exemplo). Bipe de novo quando a conexão voltar.
- **Saldo negativo** (aviso amarelo): a saída foi registrada, mas o sistema não tinha
  entrada desse produto. Avise o voluntário chefe — ele regulariza com uma entrada ou ajuste.

### Produto novo

Se o código não está no catálogo, abre o quadro **Produto novo**:

1. **Nome** (ex.: *Feijão carioca*) e, se quiser, **Marca**.
2. **Conteúdo da embalagem**: o número e a unidade do que vem **dentro de uma** embalagem.
   Ex.: pacote de arroz de 5 kg → `5` e `kg`; caixa de leite de 1 litro → `1` e `L`;
   bandeja com 30 ovos → `30` e `un`. O sistema lembra a última unidade usada.
3. **Categoria**.
4. **Cadastrar e registrar**: o produto é criado e a entrada/saída é registrada.

O estoque sempre conta **embalagens**; o conteúdo serve para o dashboard mostrar quantos
quilos e litros há.

### Produto excluído

Se o código pertence a um produto excluído do catálogo, o sistema oferece **reativar**
(voluntário chefe). Para o perfil COMUM, separe a embalagem e avise o chefe.

## 3. Ajuste de estoque

Para corrigir o saldo sem contar como doação ou entrega (vencimento, avaria, contagem física,
leitura errada).

1. Menu **Ajuste de estoque** → escolha o produto.
2. Informe a **contagem física** (quanto há na prateleira) **ou** a diferença (+/−).
3. Escreva o **motivo** (obrigatório) ou use um dos botões prontos.
4. **Registrar ajuste**.

Registros **nunca são apagados nem editados**: um erro se corrige com um novo ajuste. O
*Histórico* mostra quem registrou cada movimentação.

## 4. Catálogo e histórico

- **Catálogo**: produtos ativos, conteúdo (ex.: *5 kg*) e saldo em embalagens. Busca por
  nome, marca ou código; filtro por categoria e "só saldo negativo".
- **Histórico**: todas as movimentações, filtráveis por produto e tipo, com o autor.

## 5. Voluntário chefe

### Dashboard (Indicadores)

- **Período**: 7, 30 (padrão) ou 90 dias, ou **Outro** para escolher as datas.
- **Categoria**: todas ou uma específica.
- Cards: **saldo em estoque** (embalagens), **entradas** e **saídas** do período (ajustes não
  entram), **peso** em kg e **volume** em L (calculados pelo conteúdo de cada embalagem), e
  **produtos com saldo negativo**.
- Gráfico de entradas e saídas por dia (botão *Ver tabela* para os números).
- **Pendências**: produtos com saldo negativo, com atalhos para *Histórico* e *Ajustar*.
- Atualiza sozinho a cada 30 segundos.

### Editar, excluir e reativar produtos

No **Catálogo**, botão **Editar**. É possível mudar tudo, inclusive o código de barras.
Excluir só é possível com **saldo zero** (zere antes com um ajuste); o histórico é mantido.

### Unidades de medida

Menu **Unidades de medida**. Já vêm cadastradas: kg, g, L, mL, un, dz. Para criar uma nova
(ex.: *fardo com 6 unidades*): sigla `fd`, nome `fardo`, grandeza **Contagem**, fator `6`.

- **Fator** = quanto 1 unidade vale na base da grandeza (kg, L ou un). Ex.: g → 0,001 kg.
- Unidade **em uso** por algum produto: só o nome pode mudar, e ela não pode ser excluída —
  mudar o fator alteraria os totais já registrados.

### Usuários

Menu **Usuários**:

- **Criar**: nome, e-mail, senha inicial (mínimo 8 caracteres) e perfil. Entregue a senha
  pessoalmente.
- **Perfil**: trocar entre voluntário e voluntário chefe.
- **Redefinir senha**: encerra as sessões abertas daquele usuário.
- **Desativar**: o usuário perde o acesso imediatamente; o histórico dele é mantido.

Proteções: você não pode desativar nem rebaixar a si mesmo, e o sistema sempre mantém ao
menos um voluntário chefe ativo.

**Login compartilhado da bancada.** Pode-se criar um usuário COMUM único para a bancada
(ex.: *Bancada*). É prático, mas o histórico não identifica **qual** voluntário bipou. Com
logins individuais, cada registro mostra o nome de quem o fez.
