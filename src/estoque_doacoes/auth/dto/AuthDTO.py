from typing import Annotated

from pydantic import BaseModel, StringConstraints


class LoginIn(BaseModel):
    email: Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=254)]
    # Sem regra de tamanho aqui: senha errada é "credenciais inválidas", não 422
    senha: Annotated[str, StringConstraints(max_length=200)]
