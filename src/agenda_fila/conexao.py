"""Conexão com o banco da área do cliente: Turso (nuvem) ou arquivo SQLite local.

Regra: com TURSO_DATABASE_URL e TURSO_AUTH_TOKEN preenchidas, a conexão vai para o
Turso (SQLite na nuvem, pelo driver turso_serverless, via HTTP). Sem elas, abre o
arquivo de SQLITE_PATH com o sqlite3, como sempre.

Nos dois modos o resto do código vê a mesma interface do sqlite3: placeholders ?,
linhas acessíveis por nome (linha["coluna"], dict(linha)), lastrowid, rowcount,
`with conexao:` (commit no sucesso, rollback no erro) e erros do tipo sqlite3.Error.
Para o Turso, isso é garantido pelo adaptador ConexaoTurso deste módulo.

Cada requisição abre e fecha a própria conexão (get_conexao): nenhuma conexão é
compartilhada entre requisições ou threads.

Este módulo NUNCA cria ou altera tabelas: isso é feito uma vez, na subida do
servidor, por banco.inicializar_banco().
"""

import sqlite3
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from typing import Any

import turso_serverless

from src.compartilhado.config import settings


@contextmanager
def _erros_como_sqlite3() -> Iterator[None]:
    """Converte os erros do driver do Turso nos equivalentes do sqlite3.

    Assim o tratador de erros da API (sqlite3.Error -> 500 genérico) e o /health/db
    (sqlite3.Error -> 503) funcionam igual nos dois modos. RuntimeError cobre as
    falhas de rede/protocolo do driver (ProtocolError e ServerError herdam dele).
    """
    try:
        yield
    except turso_serverless.IntegrityError as erro:
        raise sqlite3.IntegrityError(str(erro)) from erro
    except turso_serverless.ProgrammingError as erro:
        raise sqlite3.ProgrammingError(str(erro)) from erro
    except (turso_serverless.Error, RuntimeError) as erro:
        raise sqlite3.OperationalError(str(erro)) from erro


class Linha:
    """Linha lida do Turso com o mesmo acesso do sqlite3.Row.

    Aceita linha["coluna"] (sem diferenciar maiúsculas, como o sqlite3.Row),
    linha[0], dict(linha), keys(), len() e desempacotamento.
    """

    __slots__ = ("_colunas", "_indices", "_valores")

    def __init__(
        self, colunas: tuple[str, ...], indices: dict[str, int], valores: Sequence[Any]
    ) -> None:
        self._colunas = colunas
        self._indices = indices
        self._valores = tuple(valores)

    def keys(self) -> list[str]:
        return list(self._colunas)

    def __getitem__(self, chave: int | str | slice) -> Any:
        if isinstance(chave, str):
            try:
                return self._valores[self._indices[chave.lower()]]
            except KeyError:
                raise IndexError("No item with that key") from None
        return self._valores[chave]

    def __iter__(self) -> Iterator[Any]:
        return iter(self._valores)

    def __len__(self) -> int:
        return len(self._valores)

    def __eq__(self, outra: object) -> bool:
        if not isinstance(outra, Linha):
            return NotImplemented
        return self._colunas == outra._colunas and self._valores == outra._valores

    def __hash__(self) -> int:
        return hash((self._colunas, self._valores))

    def __repr__(self) -> str:
        return f"Linha({dict(zip(self._colunas, self._valores, strict=True))!r})"


class CursorTurso:
    """Cursor do Turso que devolve Linha (por nome) e erros do sqlite3."""

    def __init__(self, cursor: Any) -> None:
        self._cursor = cursor
        self._colunas: tuple[str, ...] = tuple(coluna[0] for coluna in (cursor.description or ()))
        self._indices: dict[str, int] = {}
        for posicao, nome in enumerate(self._colunas):
            # Nome repetido: vale a primeira coluna, como no sqlite3.Row.
            self._indices.setdefault(nome.lower(), posicao)

    @property
    def lastrowid(self) -> int | None:
        return self._cursor.lastrowid

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    @property
    def description(self) -> Any:
        return self._cursor.description

    def _para_linha(self, valores: Sequence[Any]) -> Linha:
        return Linha(self._colunas, self._indices, valores)

    def fetchone(self) -> Linha | None:
        with _erros_como_sqlite3():
            valores = self._cursor.fetchone()
        return None if valores is None else self._para_linha(valores)

    def fetchall(self) -> list[Linha]:
        with _erros_como_sqlite3():
            todas = self._cursor.fetchall()
        return [self._para_linha(valores) for valores in todas]

    def __iter__(self) -> Iterator[Linha]:
        return iter(self.fetchall())


class ConexaoTurso:
    """Conexão com o Turso com a parte do sqlite3.Connection que o projeto usa."""

    def __init__(self, conexao: Any) -> None:
        self._conexao = conexao

    def execute(self, sql: str, parametros: Sequence[Any] = ()) -> CursorTurso:
        with _erros_como_sqlite3():
            return CursorTurso(self._conexao.execute(sql, parametros))

    def executemany(self, sql: str, sequencia: Iterable[Sequence[Any]]) -> CursorTurso:
        with _erros_como_sqlite3():
            return CursorTurso(self._conexao.executemany(sql, sequencia))

    def commit(self) -> None:
        with _erros_como_sqlite3():
            self._conexao.commit()

    def rollback(self) -> None:
        with _erros_como_sqlite3():
            self._conexao.rollback()

    def close(self) -> None:
        # Fechar descarta no servidor qualquer transação não confirmada.
        with _erros_como_sqlite3():
            self._conexao.close()

    def __enter__(self) -> "ConexaoTurso":
        return self

    def __exit__(self, tipo: type[BaseException] | None, *_: object) -> bool:
        """Como o sqlite3: commit se o bloco terminou bem, rollback se falhou."""
        if tipo is None:
            self.commit()
        else:
            try:
                self.rollback()
            except sqlite3.Error:
                # Não esconde o erro original; ao fechar, o servidor descarta a transação.
                pass
        return False


Conexao = sqlite3.Connection | ConexaoTurso


def abrir_conexao_turso() -> ConexaoTurso:
    """Abre uma conexão com o Turso de TURSO_DATABASE_URL, com foreign keys ligadas."""
    if not settings.usa_turso or settings.TURSO_AUTH_TOKEN is None:
        raise RuntimeError("TURSO_DATABASE_URL e TURSO_AUTH_TOKEN não estão configuradas")
    conexao = ConexaoTurso(
        turso_serverless.connect(
            str(settings.TURSO_DATABASE_URL),
            auth_token=settings.TURSO_AUTH_TOKEN.get_secret_value(),
        )
    )
    try:
        conexao.execute("PRAGMA foreign_keys = ON")
    except BaseException:
        conexao.close()
        raise
    return conexao


def abrir_conexao(caminho: str | None = None) -> Conexao:
    """Abre uma conexão com foreign keys ligadas e linhas acessíveis por nome.

    Sem `caminho`, usa o Turso se estiver configurado; senão, o arquivo SQLITE_PATH.
    Com `caminho` (URI de um arquivo), abre sempre esse SQLite local: é assim que os
    testes apontam para o banco temporário.

    No SQLite, mode=rw faz a conexão falhar se o arquivo não existir, em vez de criar
    um banco vazio sem as tabelas.
    """
    if caminho is None and settings.usa_turso:
        return abrir_conexao_turso()
    alvo = caminho or settings.SQLITE_PATH.as_uri()
    conexao = sqlite3.connect(f"{alvo}?mode=rw", uri=True, check_same_thread=False)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def get_conexao() -> Iterator[Conexao]:
    """Dependência do FastAPI: uma conexão por requisição, fechada no final."""
    conexao = abrir_conexao()
    try:
        yield conexao
    finally:
        conexao.close()
