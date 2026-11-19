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

Stack: Python 3.12+, FastAPI, SQLAlchemy 2, Alembic e PostgreSQL 16 (no Docker), gerenciado com [uv](https://docs.astral.sh/uv/). O driver do banco é o `psycopg` 3 (já vem compilado; não precisa instalar nada além do Docker).

> A API fica em `src/`. O código antigo em SQLite (pasta `backend/` da branch `teste-juncao`) serve só de referência.

### Pré-requisitos (Windows)

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (ele baixa o Python se precisar)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Passo a passo (cmd, na raiz do projeto)

```cmd
:: 1. Subir o PostgreSQL e esperar o STATUS ficar "healthy"
::    (o próprio container cria o banco "lavaajato")
docker compose up -d
docker compose ps

:: 2. Criar o .env a partir do exemplo
copy .env.example .env

:: 3. Gerar uma SECRET_KEY e colar no .env (no lugar do valor de exemplo)
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"

:: 4. Instalar as dependências (cria a .venv)
uv sync

:: 5. Criar/atualizar as tabelas com as migrations
uv run alembic upgrade head

:: 6. Rodar a API
uv run uvicorn src.main:app --reload
```

Com a API rodando:

- http://127.0.0.1:8000/health: a API está no ar
- http://127.0.0.1:8000/health/db: a API está conseguindo falar com o banco
- http://127.0.0.1:8000/docs: documentação interativa (Swagger)

### Testes e lint

Os testes usam SQLite em memória e definem as próprias variáveis (inclusive a `SECRET_KEY`), então **não precisam** do Docker nem do `.env`.

```cmd
uv run pytest
uv run ruff check .
uv run ruff format .
```

### Comandos úteis

```cmd
:: Criar uma migration depois de mudar os modelos
uv run alembic revision --autogenerate -m "cria tabela clientes"

:: Parar o PostgreSQL (os dados continuam no volume "pgdata")
docker compose down

:: Parar e APAGAR todos os dados do banco
docker compose down -v
```

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
