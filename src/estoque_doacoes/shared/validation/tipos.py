"""Tipos de validação usados por mais de um módulo."""

from typing import Annotated, Any

from pydantic import BeforeValidator, StringConstraints


def _vazio_para_none(v: Any) -> Any:
    # Formulário manda "" em campo opcional não preenchido; para a API isso é "sem valor"
    return None if isinstance(v, str) and not v.strip() else v


# Campo opcional: "" / "   " viram None antes das demais validações
VazioComoNulo = BeforeValidator(_vazio_para_none)

# EAN-8, UPC-A (12), EAN-13 e ITF-14: só dígitos, 8 a 14
CodigoBarras = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{8,14}$")]
