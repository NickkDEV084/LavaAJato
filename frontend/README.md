# LavaAjato — frontend

Frontend em HTML, CSS e JavaScript nativo, sem dependências de build. As páginas são servidas pelo próprio FastAPI, na raiz do projeto:

```cmd
uv run uvicorn src.main:app --reload
```

Depois acesse http://127.0.0.1:8000/. As URLs não levam `.html` (`/agenda` entrega `agenda.html`, e `/agenda.html` redireciona com 301 para `/agenda`), então os links internos usam sempre o nome sem extensão. Outros servidores estáticos (Live Server, `python -m http.server`) não fazem essa conversão e não servem para rodar o front.

## Páginas

Cada arquivo abre pela URL sem extensão (`cliente.html` em `/cliente`).

- `index.html`: encaminha para a área do cliente.
- `cliente.html`: área autenticada do cliente, perfil e CRUD de agendamentos.
- `auth.html`: acesso de demonstração.
- `gestao.html`: painel do gestor.
- `clientes.html`, `servicos.html`, `agenda.html`, `pedidos.html`, `produtos.html`, `status.html`, `cancelamentos.html`, `avaliacoes.html` e `relatorios.html`: seções da gestão.

As telas administrativas e seus estilos vieram do pacote `LavaAjato-frontend.zip`. O painel administrativo usa `gestao.html`; a raiz do frontend encaminha para a área do cliente em `cliente.html`.

## Organização

- `css/style.css`: identidade visual e layout responsivo das telas administrativas.
- `js/app.js`: inicialização comum, encaminhamento de páginas e sessão de demonstração.
- `js/features/navigation/manager-navigation.js`: navegação móvel, destaque da página ativa e adaptação das tabelas para cartões em telas estreitas.
- `js/features/customer/customer-service.js`: acesso isolado ao perfil, catálogo de serviços e agendamentos do cliente.
- `js/features/customer/customer-page.js`: interface do perfil e dos agendamentos.
- `js/features/<área>/`: comportamento específico de cada módulo.

Em telas pequenas, a barra inferior mantém Painel, Agenda, Pedidos e Relatórios a um toque. O botão Menu abre as demais seções; o menu e os links laterais do desktop usam os mesmos destinos.

O acesso à raiz do site abre a área do cliente. O link `Login Gestão` encaminha para o painel administrativo. Ambos reaproveitam `/auth`; a autenticação sem destino encaminha para `/gestao` e o cadastro da área do cliente (`/auth?next=cliente`) retorna para `/cliente`. O formato antigo `next=cliente.html` continua aceito.

O serviço `js/features/customer/customer-service.js` guarda o perfil junto ao cadastro existente e os agendamentos em `localStorage`. Cada agendamento recebe `customerId`; a listagem e as ações filtram por esse ID. Remarcação altera data e horário, e cancelamento preserva o registro com status `cancelado`.

O acesso e os dados que já funcionam nesta demonstração usam `localStorage`/`sessionStorage`. As demais telas são protótipos visuais; este frontend não inclui backend nem API.
