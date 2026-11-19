from lavaAjato import conectar

conn = conectar()
tabelas = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()
print([t["name"] for t in tabelas])
conn.close()