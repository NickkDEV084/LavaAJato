# Banco SQLite — área do cliente

O banco usa três tabelas: `clientes`, `servicos` e `agendamentos`. O campo `cliente_id` liga cada agendamento ao seu cliente; `servico_id` liga ao serviço escolhido.

Crie/preencha o banco na raiz do projeto com:

```powershell
python backend/lavaAjato.py
```

As funções CRUD ficam em `crud.py`. Elas podem ser importadas por uma API futuramente; este projeto ainda não cria uma API.
