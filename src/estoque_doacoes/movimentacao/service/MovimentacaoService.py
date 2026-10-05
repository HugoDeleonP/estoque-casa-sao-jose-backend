from sqlalchemy.orm import Session

from estoque_doacoes.movimentacao.domain.entity.Movimentacao import Movimentacao
from estoque_doacoes.movimentacao.domain.enum.TipoMovimentacao import TipoMovimentacao
from estoque_doacoes.movimentacao.domain.exception.MovimentacaoNaoEncontrada import (
    MovimentacaoNaoEncontrada,
)
from estoque_doacoes.movimentacao.dto.MovimentacaoDTO import (
    MovimentacaoCreate,
    MovimentacaoOut,
    MovimentacaoRegistrada,
)
from estoque_doacoes.movimentacao.repository.MovimentacaoRepository import MovimentacaoRepository
from estoque_doacoes.produto.domain.exception.ProdutoNaoEncontrado import ProdutoNaoEncontrado
from estoque_doacoes.produto.repository.ProdutoRepository import ProdutoRepository


class MovimentacaoService:
    """Regras de negócio de Movimentação e DONO DA TRANSAÇÃO (equivale ao @Transactional).

    Sem atualizar/excluir de propósito: a movimentação é imutável após criada — é a fonte
    da verdade do estoque e o registro de rastreabilidade das doações. Lançamento errado
    se corrige com um novo AJUSTE (com observação) — o histórico nunca é reescrito."""

    def __init__(self, session: Session):
        self.session = session
        self.movimentacoes = MovimentacaoRepository(session)
        self.produtos = ProdutoRepository(session)

    def listar(
        self,
        produto_id: int | None = None,
        tipo: TipoMovimentacao | None = None,
        limite: int = 100,
    ) -> list[MovimentacaoOut]:
        movs = self.movimentacoes.listar(produto_id=produto_id, tipo=tipo, limite=limite)
        return [self._para_saida(m) for m in movs]

    def buscar(self, movimentacao_id: int) -> MovimentacaoOut:
        mov = self.movimentacoes.por_id(movimentacao_id)
        if mov is None:
            raise MovimentacaoNaoEncontrada(movimentacao_id)
        return self._para_saida(mov)

    def registrar(self, dados: MovimentacaoCreate) -> MovimentacaoRegistrada:
        # Só produto ATIVO recebe movimentação
        produto = self.produtos.por_id(dados.produto_id)
        if produto is None:
            raise ProdutoNaoEncontrado.por_id(dados.produto_id)

        mov = Movimentacao(
            produto=produto,
            tipo=dados.tipo,
            quantidade=dados.quantidade,
            observacao=dados.observacao,
        )
        self.movimentacoes.adicionar(mov)
        self.session.flush()  # envia o INSERT (dentro da transação) para o SUM enxergá-lo
        saldo = produto.saldo()
        self.session.commit()

        return MovimentacaoRegistrada(
            **self._para_saida(mov).model_dump(),
            saldo_atual=saldo,
            alerta_saldo_negativo=saldo < 0,  # registra mesmo assim; o frontend avisa
        )

    @staticmethod
    def _para_saida(mov: Movimentacao) -> MovimentacaoOut:
        return MovimentacaoOut(
            id=mov.id,
            produto_id=mov.produto_id,
            produto_nome=mov.produto.nome,
            tipo=mov.tipo,
            quantidade=mov.quantidade,
            observacao=mov.observacao,
            created_at=mov.created_at,
        )
