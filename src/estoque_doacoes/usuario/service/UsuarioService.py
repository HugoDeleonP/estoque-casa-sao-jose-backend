from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from estoque_doacoes.auth.senha import gerar_hash
from estoque_doacoes.usuario.domain.entity.Usuario import Usuario
from estoque_doacoes.usuario.domain.enum.Role import Role
from estoque_doacoes.usuario.domain.exception.EmailDuplicado import EmailDuplicado
from estoque_doacoes.usuario.domain.exception.OperacaoSobreSiMesmo import OperacaoSobreSiMesmo
from estoque_doacoes.usuario.domain.exception.UltimoAdmin import UltimoAdmin
from estoque_doacoes.usuario.domain.exception.UsuarioNaoEncontrado import UsuarioNaoEncontrado
from estoque_doacoes.usuario.dto.UsuarioDTO import UsuarioCreate
from estoque_doacoes.usuario.repository.UsuarioRepository import UsuarioRepository


class UsuarioService:
    """Gestão de usuários (somente ADMIN) e DONO DA TRANSAÇÃO.

    Proteções (F3.8): o ADMIN não desativa nem rebaixa a si mesmo, e o sistema sempre
    mantém ao menos um ADMIN ativo — senão ninguém mais conseguiria administrar."""

    def __init__(self, session: Session):
        self.session = session
        self.usuarios = UsuarioRepository(session)

    def listar(self) -> list[Usuario]:
        return self.usuarios.listar()

    def buscar(self, usuario_id: int) -> Usuario:
        usuario = self.usuarios.por_id(usuario_id)
        if usuario is None:
            raise UsuarioNaoEncontrado(usuario_id)
        return usuario

    def criar(self, dados: UsuarioCreate) -> Usuario:
        if self.usuarios.por_email(dados.email) is not None:
            raise EmailDuplicado(dados.email)
        usuario = Usuario(
            nome=dados.nome,
            email=dados.email,
            senha_hash=gerar_hash(dados.senha),
            role=dados.role,
        )
        self.usuarios.adicionar(usuario)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise EmailDuplicado(dados.email) from None
        return usuario

    def alterar_perfil(self, usuario_id: int, role: Role, autor: Usuario) -> Usuario:
        usuario = self.buscar(usuario_id)
        if usuario.role == role:
            return usuario
        if usuario.id == autor.id:
            raise OperacaoSobreSiMesmo("Você não pode alterar o próprio perfil")
        if usuario.is_admin() and self.usuarios.total_admins_ativos() <= 1:
            raise UltimoAdmin()
        usuario.role = role
        usuario.sessao_versao += 1  # o perfil antigo não vale mais nas sessões abertas
        self.session.commit()
        return usuario

    def redefinir_senha(self, usuario_id: int, senha: str) -> None:
        usuario = self.buscar(usuario_id)
        usuario.senha_hash = gerar_hash(senha)
        usuario.sessao_versao += 1
        self.session.commit()

    def desativar(self, usuario_id: int, autor: Usuario) -> None:
        usuario = self.buscar(usuario_id)
        if usuario.id == autor.id:
            raise OperacaoSobreSiMesmo("Você não pode desativar o próprio usuário")
        if usuario.is_admin() and self.usuarios.total_admins_ativos() <= 1:
            raise UltimoAdmin()
        self.usuarios.desativar(usuario)
        self.session.commit()
