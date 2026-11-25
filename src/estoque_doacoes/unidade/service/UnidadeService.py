from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from estoque_doacoes.unidade.domain.entity.UnidadeMedida import UnidadeMedida
from estoque_doacoes.unidade.domain.exception.SiglaDuplicada import SiglaDuplicada
from estoque_doacoes.unidade.domain.exception.UnidadeEmUso import UnidadeEmUso
from estoque_doacoes.unidade.domain.exception.UnidadeNaoEncontrada import UnidadeNaoEncontrada
from estoque_doacoes.unidade.dto.UnidadeDTO import UnidadeIn, UnidadeOut
from estoque_doacoes.unidade.repository.UnidadeRepository import UnidadeRepository
from estoque_doacoes.usuario.domain.entity.Usuario import Usuario


class UnidadeService:
    """Regras de Unidade de Medida e DONO DA TRANSAÇÃO."""

    def __init__(self, session: Session):
        self.session = session
        self.unidades = UnidadeRepository(session)

    def listar(self) -> list[UnidadeOut]:
        unidades = self.unidades.listar()
        usadas = self.unidades.ids_em_uso(u.id for u in unidades)
        return [self._para_saida(u, u.id in usadas) for u in unidades]

    def buscar(self, unidade_id: int) -> UnidadeMedida:
        unidade = self.unidades.por_id(unidade_id)
        if unidade is None:
            raise UnidadeNaoEncontrada(unidade_id)
        return unidade

    def criar(self, dados: UnidadeIn, autor: Usuario) -> UnidadeOut:
        self._sigla_livre(dados.sigla)
        unidade = UnidadeMedida(**dados.model_dump(), created_by=autor.id)
        self.unidades.adicionar(unidade)
        self._commit(dados.sigla)
        return self._para_saida(unidade, em_uso=False)

    def atualizar(self, unidade_id: int, dados: UnidadeIn) -> UnidadeOut:
        unidade = self.buscar(unidade_id)
        em_uso = self.unidades.em_uso(unidade_id)
        if em_uso and (
            dados.sigla != unidade.sigla
            or dados.grandeza != unidade.grandeza
            or abs(dados.fator_base - unidade.fator_base) > 1e-9
        ):
            raise UnidadeEmUso(
                f"A unidade {unidade.sigla} está em uso por produtos: só o nome pode ser alterado"
            )
        self._sigla_livre(dados.sigla, unidade)
        for campo, valor in dados.model_dump().items():
            setattr(unidade, campo, valor)
        self._commit(dados.sigla)
        return self._para_saida(unidade, em_uso)

    def excluir(self, unidade_id: int) -> None:
        unidade = self.buscar(unidade_id)
        if self.unidades.em_uso(unidade_id):
            raise UnidadeEmUso(f"A unidade {unidade.sigla} está em uso por produtos")
        self.unidades.excluir(unidade)
        self.session.commit()

    def _sigla_livre(self, sigla: str, propria: UnidadeMedida | None = None) -> None:
        outra = self.unidades.por_sigla(sigla)
        if outra is not None and outra is not propria:
            raise SiglaDuplicada(sigla)

    def _commit(self, sigla: str) -> None:
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise SiglaDuplicada(sigla) from None

    @staticmethod
    def _para_saida(u: UnidadeMedida, em_uso: bool) -> UnidadeOut:
        return UnidadeOut(
            id=u.id,
            sigla=u.sigla,
            nome=u.nome,
            grandeza=u.grandeza,
            fator_base=u.fator_base,
            em_uso=em_uso,
        )
