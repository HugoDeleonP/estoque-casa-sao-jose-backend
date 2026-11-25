"""Hash de senha com bcrypt (direto, sem passlib). A senha em texto puro só existe na
memória durante a requisição: nunca é gravada nem registrada em log."""

import bcrypt

from estoque_doacoes.shared.database.config import settings

SENHA_MIN = 8
# bcrypt só considera os primeiros 72 bytes; acima disso, rejeitamos no DTO
SENHA_MAX_BYTES = 72

# Hash fixo para comparar quando o e-mail não existe: o tempo de resposta do login
# não revela se o e-mail está cadastrado.
_HASH_FALSO = bcrypt.hashpw(b"senha-inexistente", bcrypt.gensalt(settings.bcrypt_rounds))


def gerar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt(settings.bcrypt_rounds)).decode()


def conferir(senha: str, senha_hash: str | None) -> bool:
    alvo = senha_hash.encode() if senha_hash else _HASH_FALSO
    ok = bcrypt.checkpw(senha.encode()[:SENHA_MAX_BYTES], alvo)
    return ok and senha_hash is not None
