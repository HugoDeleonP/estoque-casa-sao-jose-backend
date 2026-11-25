"""Cria o PRIMEIRO ADMIN (bootstrap): pela tela não há quem o crie.

    python -m estoque_doacoes.scripts.criar_admin --nome "Fulano" --email fulano@exemplo.org

A senha é pedida no terminal (sem eco) — nunca por argumento, para não ficar no histórico
do shell nem na lista de processos. Os demais usuários são criados pela tela "Usuários".
"""

import argparse
import getpass
import sys

from pydantic import ValidationError

from estoque_doacoes.migrar import migrar
from estoque_doacoes.shared.database.db import SessionLocal
from estoque_doacoes.shared.exception.Erros import Conflito
from estoque_doacoes.usuario.domain.enum.Role import Role
from estoque_doacoes.usuario.dto.UsuarioDTO import UsuarioCreate
from estoque_doacoes.usuario.service.UsuarioService import UsuarioService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cria um usuário ADMIN")
    parser.add_argument("--nome", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args(argv)

    senha = getpass.getpass("Senha (mín. 8 caracteres): ")
    if getpass.getpass("Repita a senha: ") != senha:
        print("As senhas não conferem.", file=sys.stderr)
        return 1

    try:
        dados = UsuarioCreate(nome=args.nome, email=args.email, senha=senha, role=Role.ADMIN)
    except ValidationError as e:
        for erro in e.errors():
            print(f"{'.'.join(map(str, erro['loc']))}: {erro['msg']}", file=sys.stderr)
        return 1

    migrar()
    with SessionLocal() as session:
        try:
            usuario = UsuarioService(session).criar(dados)
        except Conflito as e:
            print(e, file=sys.stderr)
            return 1
    print(f"ADMIN criado: {usuario.nome} <{usuario.email}> (id {usuario.id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
