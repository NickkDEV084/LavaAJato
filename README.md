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
└── scripts/               # criar banco, dados de exemplo
```

## Como o Git funciona aqui

- Ninguém escreve direto na `main`.
- Todo trabalho acontece em uma branch (`feature/...`), vira Pull Request para a `develop`, e só vai para a `main` quando fecha uma versão.
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
