from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from estoque_doacoes.categoria.domain.entity.Categoria import Categoria
from estoque_doacoes.categoria.domain.exception.CategoriaDuplicada import CategoriaDuplicada
from estoque_doacoes.categoria.domain.exception.CategoriaEmUso import CategoriaEmUso
from estoque_doacoes.categoria.domain.exception.CategoriaNaoEncontrada import CategoriaNaoEncontrada
from estoque_doacoes.categoria.repository.CategoriaRepository import CategoriaRepository


class CategoriaService:
    """Regras de negócio de Categoria e DONO DA TRANSAÇÃO (equivale ao @Transactional)."""

    def __init__(self, session: Session):
        self.session = session
        self.categorias = CategoriaRepository(session)

    def listar(self) -> list[Categoria]:
        return self.categorias.listar()

    def buscar(self, categoria_id: int) -> Categoria:
        categoria = self.categorias.por_id(categoria_id)
        if categoria is None:
            raise CategoriaNaoEncontrada(categoria_id)
        return categoria

    def criar(self, nome: str) -> Categoria:
        categoria = Categoria(nome=nome)
        self.categorias.adicionar(categoria)
        self._commit(nome)
        return categoria

    def atualizar(self, categoria_id: int, nome: str) -> Categoria:
        categoria = self.buscar(categoria_id)
        categoria.nome = nome
        self._commit(nome)
        return categoria

    def excluir(self, categoria_id: int) -> None:
        categoria = self.buscar(categoria_id)
        # Soft delete; não pode deixar produto ATIVO numa categoria excluída
        if self.categorias.possui_produtos_ativos(categoria_id):
            raise CategoriaEmUso(categoria_id)
        self.categorias.excluir(categoria)
        self.session.commit()

    def _commit(self, nome: str) -> None:
        try:
            self.session.commit()
        except IntegrityError:
            # Garantia no índice único parcial do banco (nome entre categorias ativas)
            self.session.rollback()
            raise CategoriaDuplicada(nome) from None
