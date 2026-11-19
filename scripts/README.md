# Scripts

Scripts de apoio ao desenvolvimento. Rode sempre a partir da **raiz do projeto**.

## Criação do banco

Não existe script para criar o banco: o container do PostgreSQL (`docker-compose.yml`)
cria o database `lavaajato` sozinho na primeira subida, pela variável `POSTGRES_DB`.

As tabelas são criadas pelas migrations do Alembic:

```cmd
uv run alembic upgrade head
```

## Próximos scripts

- carregar dados de exemplo (seed)
