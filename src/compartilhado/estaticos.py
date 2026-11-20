"""Entrega do front estático com URLs limpas (sem ".html" no final).

- /agenda entrega agenda.html (equivalente ao `extensions: ['html']` do express.static).
- /agenda.html responde 301 para /agenda, para os links antigos continuarem funcionando.
- /index.html responde 301 para /, e / continua abrindo o index.html.
"""

import stat
from pathlib import PurePath

import anyio
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

EXTENSAO_HTML = ".html"


class FrontendSemExtensao(StaticFiles):
    """StaticFiles que aceita /pagina para pagina.html e redireciona /pagina.html para /pagina."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        caminho_url: str = scope["path"]

        if caminho_url.endswith(EXTENSAO_HTML) and scope["method"] in ("GET", "HEAD"):
            if await self._arquivo_existe(path):
                return RedirectResponse(_url_sem_extensao(scope), status_code=301)

        try:
            return await super().get_response(path, scope)
        except HTTPException as erro:
            # Só tenta "<caminho>.html" para caminhos sem extensão e sem barra no final
            # (/agenda/ abriria a página com os caminhos relativos de CSS/JS quebrados).
            tenta_html = (
                erro.status_code == 404
                and not caminho_url.endswith("/")
                and PurePath(path).suffix == ""
                and path != "."
            )
            if not tenta_html:
                raise
            try:
                return await super().get_response(path + EXTENSAO_HTML, scope)
            except HTTPException:
                raise erro from None

    async def _arquivo_existe(self, path: str) -> bool:
        try:
            _, stat_result = await anyio.to_thread.run_sync(self.lookup_path, path)
        except (OSError, ValueError):
            return False
        return stat_result is not None and stat.S_ISREG(stat_result.st_mode)


def _url_sem_extensao(scope: Scope) -> str:
    """Caminho do pedido sem ".html" (e /index.html vira /), mantendo a query string."""
    caminho = scope["path"].removesuffix(EXTENSAO_HTML)
    if caminho.endswith("/index"):
        caminho = caminho.removesuffix("index")
    query = scope.get("query_string", b"").decode("latin-1")
    return f"{caminho}?{query}" if query else caminho
