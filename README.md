# LavaAjato

Sistema de agendamento para lava-jato: o cliente escolhe o serviço e marca o horário, e a gestão acompanha a agenda e atualiza o status de cada lavagem até a retirada do veículo.

![CI](https://github.com/NickkDEV084/LavaAJato/actions/workflows/ci.yml/badge.svg?branch=develop)

## Demonstração online

O sistema está publicado em **https://lavaajato.onrender.com**.

| Caminho | O que é |
|---|---|
| [`/`](https://lavaajato.onrender.com/) | Área do cliente (abre a `cliente.html`) |
| [`/agenda.html`](https://lavaajato.onrender.com/agenda.html) | Agenda da gestão |
| [`/docs`](https://lavaajato.onrender.com/docs) | Documentação interativa da API (Swagger) |

- **A agenda da gestão pede uma chave de acesso.** Ela é configurada no servidor e **não é pública**; quem não tem a chave consegue usar a área do cliente e a documentação da API normalmente. Antes da chave, a página pede o acesso de demonstração (`auth.html`), como as demais telas da gestão.
- **A primeira visita pode levar cerca de 1 minuto.** O serviço está no plano free do Render, que "adormece" depois de um tempo sem acessos.
- **Os dados de teste são reiniciados periodicamente.** O disco do plano free é efêmero: perfis e agendamentos criados na demonstração se perdem quando o serviço reinicia.

## Telas

### Área do cliente

![Área do cliente com o perfil preenchido e agendamentos em diferentes status](docs/imagens/area-cliente.png)

### Agenda da gestão

![Agenda da gestão com a lista de agendamentos, status e botões de ação](docs/imagens/agenda-gestao.png)

### Documentação da API

![Documentação interativa da API (Swagger) com as rotas da área do cliente e da gestão](docs/imagens/documentacao-api.png)

### Área do cliente no celular

<img src="docs/imagens/area-cliente-celular.png" alt="Lista de agendamentos da área do cliente em tela de celular" width="320">

## Funcionalidades

### Área do cliente (`cliente.html`)

- Cadastro e acesso de demonstração, feitos no próprio navegador.
- Perfil com nome, telefone e veículo (carro, marca e placa). É preciso salvar o perfil antes de agendar (o nome é obrigatório).
- Lista dos serviços disponíveis para agendamento.
- Agendamento com data e horário futuros, validados no fuso configurado (`TIMEZONE`). Preço e duração do serviço ficam registrados no momento do agendamento.
- Lista e detalhe dos próprios agendamentos.
- Remarcação e cancelamento, permitidos enquanto o status é `agendado`.
- Registro do pagamento quando o veículo está pronto para retirada (não há pagamento online: a ação só conclui o atendimento).

### Agenda da gestão (`agenda.html`)

- Lista de agendamentos com filtros por data e por status.
- Lista de clientes e de serviços.
- Criação de agendamento para um cliente já cadastrado.
- Confirmação, marcação de "pronto para retirada" e cancelamento.

### Fluxo de status

```
agendado  ->  confirmado  ->  pronto-retirada  ->  concluido
   |              |
   +--------------+------->  cancelado
```

| Transição | Quem faz |
|---|---|
| `agendado` -> `confirmado` | Gestão |
| `confirmado` -> `pronto-retirada` | Gestão |
| `pronto-retirada` -> `concluido` | Cliente, ao registrar o pagamento |
| `agendado` -> `cancelado` | Cliente ou gestão |
| `confirmado` -> `cancelado` | Gestão |

Qualquer outra mudança de status é recusada pela API com `409`.

## Tecnologias

- **Back-end:** Python 3.12+, [FastAPI](https://fastapi.tiangolo.com/), Pydantic / pydantic-settings (validação e configuração via `.env`), Uvicorn.
- **Banco de dados:** SQLite (arquivo `lavaajato.db`, acessado com o módulo `sqlite3` da biblioteca padrão).
- **Front-end:** HTML, CSS e JavaScript nativo (módulos ES), sem framework e sem etapa de build.
- **Ferramentas:** [uv](https://docs.astral.sh/uv/) (dependências e ambiente), pytest + httpx (testes), Ruff (lint e formatação).
- **Infraestrutura:** GitHub Actions (CI) e Render (hospedagem).

## Arquitetura

Um único serviço FastAPI faz as duas coisas: atende a API (`/cliente/*`, `/gestao/*`, `/health*`, `/docs`) e serve os arquivos estáticos de `frontend/` em todos os outros caminhos. Como front e API ficam na mesma origem, não há CORS em produção. As regras de negócio ficam separadas das rotas e do acesso ao banco, e o SQLite é o único banco do projeto.

```
LavaAJato/
├── src/
│   ├── main.py              # cria o app FastAPI, health checks e serve o frontend/
│   ├── agenda_fila/         # rotas, regras, esquemas e acesso ao SQLite (cliente e gestão)
│   └── compartilhado/       # configuração (.env) e tratamento de erros
├── frontend/                # páginas HTML, css/ e js/ (sem build)
├── tests/                   # testes da API, health checks e frontend
├── backend/                 # código original do banco SQLite (referência)
├── lavaajato.db             # banco SQLite com as tabelas servicos, clientes e agendamentos
├── render.yaml              # Blueprint do deploy no Render
└── .github/workflows/ci.yml # pipeline de lint e testes
```

As demais pastas em `src/` (`clientes_veiculos`, `servicos_precos`, `pedidos_pagamentos` etc.) ainda não têm código: cada uma traz só um `README.md` com o planejamento do módulo.

## Rotas da API

A documentação completa, com os formatos de entrada e saída, fica em `/docs` (Swagger) e `/openapi.json`.

### Área do cliente: `/cliente/*`

Todas exigem o header `X-Usuario-Id` com o identificador do cliente; sem ele, `401`. A API só devolve e altera os dados desse cliente (agendamento de outro cliente responde `404`).

| Método | Rota | Descrição |
|---|---|---|
| GET | `/cliente/servicos` | Lista os serviços disponíveis para agendar |
| GET | `/cliente/perfil` | Retorna o perfil do cliente |
| PUT | `/cliente/perfil` | Cria ou atualiza o perfil do cliente |
| GET | `/cliente/agendamentos` | Lista os agendamentos do cliente |
| GET | `/cliente/agendamentos/{agendamento_id}` | Retorna um agendamento do cliente |
| POST | `/cliente/agendamentos` | Cria um agendamento (`201`) |
| PATCH | `/cliente/agendamentos/{agendamento_id}` | Remarca data e horário |
| POST | `/cliente/agendamentos/{agendamento_id}/cancelar` | Cancela um agendamento |
| POST | `/cliente/agendamentos/{agendamento_id}/pagar` | Registra o pagamento e conclui o agendamento |

### Gestão: `/gestao/*`

Todas exigem o header `X-Chave-Gestao` igual à `GESTAO_CHAVE` do servidor. Sem `GESTAO_CHAVE` configurada, `503`; sem o header, `401`; com a chave errada, `403`.

| Método | Rota | Descrição |
|---|---|---|
| GET | `/gestao/servicos` | Lista os serviços |
| GET | `/gestao/clientes` | Lista os clientes |
| GET | `/gestao/agendamentos` | Lista os agendamentos (filtros opcionais `?data=AAAA-MM-DD&status=...`) |
| POST | `/gestao/agendamentos` | Cria um agendamento para um cliente cadastrado (`201`) |
| POST | `/gestao/agendamentos/{agendamento_id}/confirmar` | Confirma um agendamento |
| POST | `/gestao/agendamentos/{agendamento_id}/pronto-retirada` | Marca o veículo como pronto para retirada |
| POST | `/gestao/agendamentos/{agendamento_id}/cancelar` | Cancela um agendamento |

### Health checks

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Indica que a API está no ar |
| GET | `/health/db` | Verifica se o `lavaajato.db` abre e tem as tabelas `servicos`, `clientes` e `agendamentos` (`503` se não) |

## Como rodar localmente

### Pré-requisitos

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (ele baixa o Python 3.12+ se precisar).
- Git.

Não precisa de Docker nem de servidor de banco: o `lavaajato.db` já vem no repositório com as tabelas criadas.

### 1. Instalar as dependências

Na raiz do projeto (cria a `.venv`):

```cmd
uv sync
```

### 2. Criar o `.env`

```cmd
copy .env.example .env
```

Depois revise as variáveis no `.env`:

| Variável | Para que serve | Valor do exemplo |
|---|---|---|
| `SECRET_KEY` | Chave secreta da aplicação. Obrigatória: sem ela a API não sobe. Troque o valor de exemplo por uma chave gerada | `troque-por-uma-chave-aleatoria` |
| `GESTAO_CHAVE` | Chave da agenda da gestão, enviada pelo front no header `X-Chave-Gestao`. Vazia, as rotas `/gestao/*` respondem `503` | (vazia) |
| `SQLITE_PATH` | Caminho do banco SQLite. Caminho relativo é resolvido a partir da raiz do projeto | `lavaajato.db` |
| `TIMEZONE` | Fuso (nome IANA) das regras de horário dos agendamentos, independente do fuso do servidor | `America/Recife` |
| `CORS_ORIGINS` | Origens que podem chamar a API, separadas por vírgula. Só é necessária no modo de dev do front (porta 5500) | `http://localhost:5500,http://127.0.0.1:5500` |

Para gerar valores para `SECRET_KEY` e `GESTAO_CHAVE` (rode uma vez para cada):

```cmd
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
```

O `.env` não vai para o Git. Os testes não dependem dele.

### 3. Subir a API e o front

```cmd
uv run uvicorn src.main:app --reload
```

Abra http://127.0.0.1:8000/. O mesmo servidor atende o front e a API:

- http://127.0.0.1:8000/: área do cliente
- http://127.0.0.1:8000/agenda.html: agenda da gestão (use a `GESTAO_CHAVE` do seu `.env`)
- http://127.0.0.1:8000/docs: documentação da API
- http://127.0.0.1:8000/health/db: checagem do banco

### Modo de dev do front (porta 5500)

Também dá para servir o `frontend/` à parte (por exemplo, com o Live Server do VS Code ou com o servidor do Python), mantendo a API rodando no terminal anterior:

```cmd
cd frontend
python -m http.server 5500
```

Abra http://127.0.0.1:5500/cliente.html. Quando a página está na porta 5500, o `frontend/js/core/config.js` chama a API em `http://127.0.0.1:8000`; em qualquer outra porta, usa a mesma origem da página. Nesse modo, a `CORS_ORIGINS` do `.env` precisa incluir a origem do front.

## Testes e qualidade

Os testes usam um SQLite temporário com o mesmo schema do `lavaajato.db` (nunca alteram o arquivo real) e definem as próprias variáveis de ambiente, então não precisam do `.env`. Hoje são 205 testes.

```cmd
uv run pytest
uv run ruff check .
uv run ruff format .
```

O CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) roda a cada Pull Request e a cada push na `develop` e na `Principal!`: instala as dependências com `uv sync --locked` (falha se o `uv.lock` estiver desatualizado), roda `ruff check .`, `ruff format --check .` e `pytest`.

## Deploy (Render)

### Como está montado

Um único **web service** Python no Render (plano free) roda o FastAPI, que serve **a API e o front no mesmo domínio**:

- `/cliente/*`, `/gestao/*`, `/health`, `/health/db`, `/docs`, `/openapi.json`: API
- qualquer outro caminho: arquivos de `frontend/` (`/` abre o `index.html`, que redireciona para `cliente.html`)

Fora da porta 5500, o front chama a API pela mesma origem da página, então não há CORS envolvido e `CORS_ORIGINS` não precisa ser configurada no Render.

A configuração fica no [`render.yaml`](render.yaml) (Blueprint), na raiz:

- build: `uv sync --locked --no-dev` (o Render instala o uv sozinho porque há um `uv.lock` na raiz)
- start: `uv run --no-sync uvicorn src.main:app --host 0.0.0.0 --port $PORT`
- health check: `/health/db`
- Python `3.12.16` (variável `PYTHON_VERSION`), região `virginia`, deploy da branch `Principal!`

### Criar o serviço pelo Blueprint

1. No painel do Render: **New → Blueprint** e escolha este repositório (branch `Principal!`).
2. O Render lê o `render.yaml` e pede os valores marcados com `sync: false`:
   - **`GESTAO_CHAVE`**: chave da agenda da gestão. Gere uma com o comando da seção [Criar o `.env`](#2-criar-o-env). Sem ela, as rotas `/gestao/*` respondem `503`.
3. Confirme. A `SECRET_KEY` é gerada automaticamente pelo Render; `SQLITE_PATH`, `TIMEZONE` e `PYTHON_VERSION` já vêm do arquivo.

O Render só pede os valores `sync: false` na **criação** do Blueprint. Para trocar a `GESTAO_CHAVE` depois, use **Environment** no painel do serviço. A cada push na `Principal!`, o Render faz um novo deploy.

### Avisos do plano free

- **O banco volta ao original a cada reinício ou deploy.** O disco é efêmero: tudo que for gravado no `lavaajato.db` em produção (perfis, agendamentos) se perde quando o serviço reinicia, dorme ou recebe deploy, e ele volta ao `lavaajato.db` versionado no repositório. Para uma demonstração isso é aceitável.
- **A primeira visita pode demorar cerca de 1 minuto.** Depois de 15 minutos sem acessos o Render "adormece" o serviço; a próxima requisição o acorda.

## Como o Git funciona aqui

Usamos Git Flow com três níveis:

```
feature/*  ->  develop  ->  Principal!
```

- **`Principal!`** é a branch de produção: tem as versões fechadas e é dela que o Render faz o deploy. Ninguém commita direto nela.
- **`develop`** junta o trabalho pronto da equipe. Também não recebe commit direto.
- Cada tarefa nasce de uma branch criada a partir da `develop` (`feature/`, `fix/`, `docs/`, `ci/`...):

  ```cmd
  git checkout develop
  git pull
  git checkout -b feature/nome-da-tarefa
  ```

- Ao terminar, abra um Pull Request da sua branch para a `develop`. O CI precisa passar antes do merge.
- Quando uma versão fecha, a `develop` vai para a `Principal!` por Pull Request, e isso dispara um novo deploy.
- Commits no padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/), em português: `tipo(modulo): descrição` (ex.: `feat(agenda): bloquear horário em conflito`).
- Mais detalhes em [CONTRIBUTING.md](CONTRIBUTING.md).

## Limitações conhecidas e próximos passos

- **Autenticação de demonstração.** Não há login real no servidor: o cadastro e o acesso ficam no navegador, e a API identifica o cliente só pelo header `X-Usuario-Id`, sem verificação (quem enviar o id de outro cliente age como ele). A gestão usa uma chave compartilhada (`GESTAO_CHAVE`) em vez de usuários. Próximo passo: login no servidor com token assinado e perfis de acesso.
- **`servicos.html` ainda usa o `localStorage`.** O cadastro de serviços da gestão não está ligado à API; a área do cliente e a agenda leem os serviços do banco.
- **Painel (`gestao.html`) e `pedidos.html` estão no fluxo antigo.** Ainda trabalham com dados do `localStorage`, não com os agendamentos da API. As outras telas da gestão (clientes, produtos, status, cancelamentos, avaliações, relatórios) são protótipos visuais.
- **O veículo vem do perfil atual.** O agendamento não guarda uma cópia do veículo: se o cliente muda carro ou placa no perfil, os agendamentos antigos passam a mostrar os dados novos.
- **Banco efêmero no plano free.** Os dados gravados em produção se perdem a cada reinício ou deploy (ver [Avisos do plano free](#avisos-do-plano-free)).
- **Módulos planejados sem código.** Pedidos e pagamentos, estoque, avaliações e relatórios ainda estão só no planejamento (`src/*/README.md`). Escopo completo em [docs/escopo.pdf](docs/escopo.pdf), com [requisitos](docs/requisitos.md) e [regras de negócio](docs/regras-de-negocio.md).

## Equipe

| Integrante | Papel | GitHub |
|---|---|---|
| Kaiky Jefferson | Back-end, integração, CI e deploy | [github.com/kaikyjefferson0](https://github.com/kaikyjefferson0) |
| Nicolas Gabriel | Banco de dados, back-end e front-end | [github.com/NickkDEV084](https://github.com/NickkDEV084) |
| David Dias | Design e front-end | - |
| Leonardo Novaes | Back-end | - |
| Vanderson Lucas | Back-end | - |
