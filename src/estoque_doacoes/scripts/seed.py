"""`python -m estoque_doacoes.scripts.seed` — aplica migrações e dados iniciais."""

from estoque_doacoes.migrar import migrar
from estoque_doacoes.seed import semear
from estoque_doacoes.shared.database.db import SessionLocal


def main() -> None:
    migrar()
    with SessionLocal() as session:
        semear(session)
    print("Migrações e dados iniciais aplicados.")


if __name__ == "__main__":
    main()
