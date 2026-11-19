# Como contribuir

## Branches
- Fluxo: `feature/*` → `develop` → `Principal!`
- `Principal!`: branch de produção, sempre estável, só recebe release (protegida)
- `develop`: integração do que está pronto
- Trabalho do dia a dia: `feature/`, `fix/`, `docs/`, `hotfix/`
- Nome: `tipo/assunto-curto` (minúsculo, com hífen). Ex.: `feature/agenda-fila`

## Commits (Conventional Commits)
`tipo(modulo): descrição`

Tipos: feat, fix, docs, test, refactor, chore.
Ex.: `feat(agenda): bloquear horário em conflito`

## Pull Request
- Título no padrão do commit
- Descrição do que mudou e link da issue (`Closes #12`)
- Testes passando e ao menos 1 revisão antes do merge
- Ninguém escreve direto na `Principal!`

## Segurança
Arquivos `.env` e senhas nunca vão para o Git.
