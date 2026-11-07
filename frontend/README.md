# LavaAjato — início, login e agendamento

Esta pasta reúne as telas públicas do cliente:

- `index.html`: página inicial, catálogo de serviços, formulário de agendamento e consulta de solicitações.
- `auth.html`: tela de login e cadastro de demonstração.

O catálogo e os pedidos ficam temporariamente no `localStorage` deste navegador. Não há banco de dados nem conexão com API; essa integração pode ser feita depois.

## Abrir no navegador

Sirva a pasta `frontend` com a extensão Live Server do VS Code ou, no terminal, execute `python -m http.server 5500` na raiz do projeto e acesse `http://localhost:5500/frontend/`.

A tela de login também está em `http://localhost:5500/frontend/auth.html`. Os módulos JavaScript precisam ser servidos por HTTP; abrir o HTML diretamente pelo caminho `file://` não funciona.