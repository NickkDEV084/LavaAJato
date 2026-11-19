"""Tipos padronizados para as colunas dos modelos.

Use estes aliases nos modelos de todos os módulos para que os tipos fiquem iguais
no banco inteiro:

    from src.compartilhado.database import Base
    from src.compartilhado.tipos import Dinheiro, Texto, TextoCurto, TextoLongo

    class Servico(Base):
        __tablename__ = "servicos"

        id: Mapped[int] = mapped_column(primary_key=True)
        nome: Mapped[TextoCurto]
        descricao: Mapped[TextoLongo | None]
        preco: Mapped[Dinheiro]

- São tipos genéricos do SQLAlchemy: funcionam no PostgreSQL (banco da aplicação)
  e no SQLite em memória usado nos testes. No PostgreSQL os textos já são UTF-8,
  então acentos e "ç" funcionam sem tipo especial.
- Valores em dinheiro usam Numeric(10, 2) e são lidos como Decimal no Python.
  Nunca use float para dinheiro.
"""

from decimal import Decimal
from typing import Annotated

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import mapped_column

# Tipos do SQLAlchemy (para usar direto em Column/mapped_column, se precisar).
TIPO_TEXTO_CURTO = String(100)
TIPO_TEXTO = String(255)
TIPO_TEXTO_LONGO = Text()
TIPO_DINHEIRO = Numeric(10, 2)

# Aliases para usar com Mapped[...].
TextoCurto = Annotated[str, mapped_column(TIPO_TEXTO_CURTO)]
"""VARCHAR(100): nomes, placas, telefones etc."""

Texto = Annotated[str, mapped_column(TIPO_TEXTO)]
"""VARCHAR(255): textos de tamanho médio (e-mail, endereço etc.)."""

TextoLongo = Annotated[str, mapped_column(TIPO_TEXTO_LONGO)]
"""TEXT (sem limite): observações, descrições e comentários."""

Dinheiro = Annotated[Decimal, mapped_column(TIPO_DINHEIRO)]
"""NUMERIC(10, 2): preços, valores de pedidos e pagamentos."""
