# LavaAjato — frontend

Frontend em HTML, CSS e JavaScript nativo, sem dependências de build. Para abrir as páginas, sirva a pasta `frontend` com o Live Server ou execute `python -m http.server 5500` na raiz e acesse `http://localhost:5500/frontend/`. Os módulos JavaScript precisam ser servidos por HTTP.

## Páginas

- `index.html`: página pública do cliente, catálogo, agendamento e consulta de pedidos.
- `cliente.html`: área autenticada do cliente, perfil e CRUD de agendamentos.
- `auth.html`: acesso de demonstração.
- `gestao.html`: painel do gestor.
- `clientes.html`, `servicos.html`, `agenda.html`, `pedidos.html`, `produtos.html`, `status.html`, `cancelamentos.html`, `avaliacoes.html` e `relatorios.html`: seções da gestão.

As telas administrativas e seus estilos vieram do pacote `LavaAjato-frontend.zip`. `gestao.html` usa esse nome para coexistir com a página pública que já ocupava `index.html`.

## Organização

- `css/style.css`: identidade visual e layout responsivo das telas administrativas.
- `js/app.js`: inicialização comum, encaminhamento de páginas e sessão de demonstração.
- `js/features/navigation/manager-navigation.js`: navegação móvel, destaque da página ativa e adaptação das tabelas para cartões em telas estreitas.
- `js/features/customer/customer-service.js`: acesso isolado ao perfil, catálogo de serviços e agendamentos do cliente.
- `js/features/customer/customer-page.js`: interface do perfil e dos agendamentos.
- `js/features/<área>/`: comportamento específico de cada módulo.

Em telas pequenas, a barra inferior mantém Painel, Agenda, Pedidos e Relatórios a um toque. O botão Menu abre as demais seções; o menu e os links laterais do desktop usam os mesmos destinos.

Os acessos à conta a partir do site público reaproveitam `auth.html` e direcionam para `cliente.html` após login/cadastro. A tela de autenticação sem esse destino continua encaminhando para a Gestão.

O serviço `js/features/customer/customer-service.js` guarda o perfil junto ao cadastro existente e os agendamentos em `localStorage`. Cada agendamento recebe `customerId`; a listagem e as ações filtram por esse ID. Remarcação altera data e horário, e cancelamento preserva o registro com status `cancelado`.

O acesso e os dados que já funcionam nesta demonstração usam `localStorage`/`sessionStorage`. As demais telas são protótipos visuais; este frontend não inclui backend nem API.
