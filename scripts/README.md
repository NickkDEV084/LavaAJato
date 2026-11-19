# Scripts

Scripts de apoio ao desenvolvimento. Rode sempre a partir da **raiz do projeto**.

## Banco de dados

O banco é o SQLite `lavaajato.db`, na raiz do projeto. Ele já vem com as tabelas
`servicos`, `clientes` e `agendamentos`, então não existe script para criar o banco
nem migrations. O caminho usado pela API vem da variável `SQLITE_PATH` do `.env`.

O schema pertence ao banco existente: a API nunca cria nem altera tabelas. Para
conferir se a API enxerga o banco, suba a API e abra http://127.0.0.1:8000/health/db.

## Próximos scripts

- carregar dados de exemplo (seed)
