# 🚗 LavaAjato

Sistema de gestão para lava-jato. Controla todo o ciclo: o cliente é cadastrado, agenda (ou entra na fila), o veículo é lavado acompanhando o status, o pedido é pago e, no fim, o cliente avalia.

> **Status:** 🚧 em construção. Por enquanto o repositório tem só a estrutura de pastas.

## Fluxo do atendimento

```
Cadastro -> Agendamento ou fila -> Em lavagem -> Pronto p/ retirada -> Pedido e pagamento -> Avaliação
```

## Os 8 módulos

| # | Módulo | Pasta |
|---|---|---|
| 1 | Cadastro de clientes e veículos | `src/clientes_veiculos` |
| 2 | Serviços e preços | `src/servicos_precos` |
| 3 | Agenda, reagendamentos e fila | `src/agenda_fila` |
| 4 | Pedidos e pagamentos | `src/pedidos_pagamentos` |
| 5 | Produtos e estoque | `src/produtos_estoque` |
| 6 | Status do serviço | `src/status_servico` |
| 7 | Cancelamentos | `src/cancelamentos` |
| 8 | Avaliações e relatórios | `src/avaliacoes_relatorios` |

Cada pasta tem um `README.md` com o que adicionar e como o módulo deve funcionar.

## Perfis de usuário

| Perfil | O que faz |
|---|---|
| Atendente | Cadastra clientes e veículos, agenda, gerencia a fila, abre pedidos e recebe pagamentos |
| Lavador | Vê a fila do dia, muda o status do serviço e registra observações |
| Gerente / Admin | Tudo acima + preços, estoque, cancelamentos tardios, estornos e relatórios |

**Fora do escopo (por enquanto):** app mobile, nota fiscal, pagamento online, várias lojas.

## Estrutura de pastas

```
LavaAjato/
|--- README.md
├── LICENSE
├── .gitignore
├── CONTRIBUTING.md        # regras de branch, commit e PR
├── .github/               # CI, modelos de issue e de PR
├── docs/                  # escopo, requisitos, regras e diagramas
├── src/                   # um módulo por pasta + compartilhado
├── frontend/              # telas do sistema
├── tests/                 # uma subpasta de testes por módulo
└── scripts/               # scripts de apoio (ex.: dados de exemplo)
```

## Como rodar o backend

Stack: Python 3.12+, FastAPI e SQLite, gerenciado com [uv](https://docs.astral.sh/uv/). O banco é o arquivo `lavaajato.db`, na raiz do projeto, que já vem com as tabelas `servicos`, `clientes` e `agendamentos`. Não precisa de Docker nem de servidor de banco.

> A API fica em `src/` (rotas em `src/agenda_fila`). O código antigo da pasta `backend/` serve só de referência.

### Pré-requisitos (Windows)

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (ele baixa o Python se precisar)

### Configurar o `.env` (cmd, na raiz do projeto)

```cmd
copy .env.example .env
```

Depois revise as variáveis no `.env`:

| Variável | Para que serve | Exemplo |
|---|---|---|
| `SECRET_KEY` | Chave secreta da aplicação (obrigatória). Gere uma com `uv run python -c "import secrets; print(secrets.token_urlsafe(32))"` e cole no lugar do valor de exemplo | `troque-por-uma-chave-aleatoria` |
| `CORS_ORIGINS` | Origens do front que podem chamar a API, separadas por vírgula. Sem a origem do front, o navegador bloqueia as chamadas | `http://localhost:5500,http://127.0.0.1:5500` |
| `SQLITE_PATH` | Caminho do banco SQLite. Um caminho relativo é resolvido a partir da raiz do projeto | `lavaajato.db` |
| `TIMEZONE` | Fuso (nome IANA) usado nas regras de horário dos agendamentos, independente do fuso do servidor | `America/Recife` |
| `GESTAO_CHAVE` | Chave da área de gestão, enviada pelo front no header `X-Chave-Gestao`. Vazia, a API recusa as rotas `/gestao/*` com `503`. Gere uma com o mesmo comando da `SECRET_KEY` | (vazia no exemplo) |

### Subir a API e o front

Terminal 1, na raiz do projeto:

```cmd
:: Instalar as dependências (cria a .venv)
uv sync

:: Rodar a API
uv run uvicorn src.main:app --reload
```

Terminal 2, dentro de `frontend/`:

```cmd
cd frontend
python -m http.server 5500
```

Depois abra http://127.0.0.1:5500/cliente.html. O endereço da API usado pelo front fica em `frontend/js/core/config.js` (`API_BASE_URL`).

Com a API rodando:

- http://127.0.0.1:8000/health: a API está no ar
- http://127.0.0.1:8000/health/db: o `lavaajato.db` abre e tem as tabelas `servicos`, `clientes` e `agendamentos` (responde `503` se não)
- http://127.0.0.1:8000/docs: documentação interativa (Swagger)

### Rotas `/cliente/*`

Todas as rotas exigem o header `X-Usuario-Id` com o identificador do cliente. Sem ele a API responde `401`. A API só devolve e altera os dados do cliente desse header (agendamento de outro cliente responde `404`).

> **Atenção:** o `X-Usuario-Id` ainda não é verificado. Quem enviar o id de outro cliente age como ele. Serve para desenvolvimento e demonstração; antes de produção precisa virar um token assinado.

| Método | Rota | O que faz |
|---|---|---|
| GET | `/cliente/servicos` | Lista os serviços disponíveis para agendar |
| GET | `/cliente/perfil` | Retorna o perfil do cliente |
| PUT | `/cliente/perfil` | Cria ou atualiza o perfil do cliente |
| GET | `/cliente/agendamentos` | Lista os agendamentos do cliente |
| GET | `/cliente/agendamentos/{agendamento_id}` | Retorna um agendamento do cliente |
| POST | `/cliente/agendamentos` | Cria um agendamento (responde `201`) |
| PATCH | `/cliente/agendamentos/{agendamento_id}` | Remarca a data/hora de um agendamento |
| POST | `/cliente/agendamentos/{agendamento_id}/cancelar` | Cancela um agendamento |
| POST | `/cliente/agendamentos/{agendamento_id}/pagar` | Marca um agendamento como pago |

### Rotas `/gestao/*`

Todas as rotas exigem o header `X-Chave-Gestao` igual à `GESTAO_CHAVE` do `.env`. Sem a `GESTAO_CHAVE` configurada a API responde `503`; sem o header, `401`; com a chave errada, `403`.

| Método | Rota | O que faz |
|---|---|---|
| GET | `/gestao/servicos` | Lista os serviços |
| GET | `/gestao/clientes` | Lista os clientes |
| GET | `/gestao/agendamentos` | Lista os agendamentos (filtros opcionais `?data=AAAA-MM-DD&status=...`) |
| POST | `/gestao/agendamentos` | Cria um agendamento (responde `201`) |
| POST | `/gestao/agendamentos/{agendamento_id}/confirmar` | Confirma um agendamento |
| POST | `/gestao/agendamentos/{agendamento_id}/pronto-retirada` | Marca o veículo como pronto para retirada |
| POST | `/gestao/agendamentos/{agendamento_id}/cancelar` | Cancela um agendamento |

### Testes e lint

Os testes usam um SQLite temporário com o mesmo schema do `lavaajato.db` (nunca mexem no arquivo real) e definem as próprias variáveis, então **não precisam** do `.env`.

```cmd
uv run pytest
uv run ruff check .
uv run ruff format .
```

## Deploy (Render)

### Arquitetura

Um único **web service** Python no Render (plano free) roda o FastAPI, que serve **a API e o front no mesmo domínio**:

- `/cliente/*`, `/gestao/*`, `/health`, `/health/db`, `/docs`, `/openapi.json`: API
- qualquer outro caminho: arquivos de `frontend/` (`/` abre o `index.html`, que redireciona para `cliente.html`)

Fora da porta 5500 (dev), o `frontend/js/core/config.js` chama a API pela mesma origem da página, então não há CORS envolvido e `CORS_ORIGINS` não precisa ser configurada no Render.

A configuração fica no `render.yaml` (Blueprint), na raiz:

- build: `uv sync --locked --no-dev` (o Render instala o uv sozinho porque há um `uv.lock` na raiz)
- start: `uv run --no-sync uvicorn src.main:app --host 0.0.0.0 --port $PORT`
- health check: `/health/db`
- Python `3.12.16` (variável `PYTHON_VERSION`), região `virginia`, deploy da branch `Principal!`

### Criar o serviço pelo Blueprint

1. No painel do Render: **New → Blueprint** e escolha este repositório (branch `Principal!`).
2. O Render lê o `render.yaml` e pede os valores marcados com `sync: false`:
   - **`GESTAO_CHAVE`**: chave da área de gestão. Gere uma com `uv run python -c "import secrets; print(secrets.token_urlsafe(32))"`. Sem ela, as rotas `/gestao/*` respondem `503`.
3. Confirme. `SECRET_KEY` é gerada automaticamente pelo Render; `SQLITE_PATH`, `TIMEZONE` e `PYTHON_VERSION` já vêm do arquivo.

O Render só pede os valores `sync: false` na **criação** do Blueprint. Para trocar a `GESTAO_CHAVE` depois, use **Environment** no painel do serviço. A cada push na `Principal!` o Render faz um novo deploy.

### Avisos do plano free

- **O banco volta ao original a cada reinício ou deploy.** O disco do plano free é efêmero: tudo que for gravado no `lavaajato.db` em produção (perfis, agendamentos) se perde quando o serviço reinicia, dorme ou recebe deploy, e ele volta ao `lavaajato.db` versionado no repositório. Para uma demonstração isso é aceitável.
- **A primeira visita pode demorar cerca de 1 minuto.** Depois de 15 minutos sem acessos o Render "adormece" o serviço; a próxima requisição o acorda.

## Como o Git funciona aqui

Usamos Git Flow com três níveis:

```
feature/*  ->  develop  ->  Principal!
```

- `Principal!` é a branch principal (versões fechadas). Ninguém commita direto nela.
- `develop` junta o trabalho pronto da equipe. Também não recebe commit direto.
- Cada tarefa nasce de uma branch criada a partir da `develop`:

  ```cmd
  git checkout develop
  git pull
  git checkout -b feature/nome-da-tarefa
  ```

- Ao terminar, abra um Pull Request de `feature/...` para a `develop`. Quando uma versão fecha, a `develop` vai para a `Principal!` por Pull Request.
- Commits no padrão Conventional Commits, em português: `tipo(modulo): descrição` (ex.: `feat(clientes_veiculos): cadastro de veículos`).
- Detalhes em [CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap

| Fase | Entrega | Módulos | Tag |
|---|---|---|---|
| 0 - Fundação | Repositório, README, estrutura, CI | - | - |
| 1 - Base | Clientes e serviços | 1, 2 | v0.1.0 |
| 2 - Operação | Agendar, fila e status | 3, 6 | v0.2.0 |
| 3 - Financeiro | Pagamento, caixa e cancelamento | 4, 7 | v0.3.0 |
| 4 - Apoio | Estoque, avaliações e relatórios | 5, 8 | v0.4.0 |
| 5 - Entrega | Testes finais e documentação | Todos | v1.0.0 |

## Equipe

| Área | Integrantes |
|---|---|
| Backend | Nicolas Gabriel, Leonardo Novaes, Kayke Jefferson, Vanderson Lucas |
| Design | David Dias |
| Frontend | David Dias, Nicolas Gabriel, Kayke Jefferson |

Escopo completo em [docs/escopo.pdf](docs/escopo.pdf).
