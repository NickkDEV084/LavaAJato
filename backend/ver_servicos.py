from lavaAjato import conectar

conn = conectar()
for s in conn.execute("SELECT * FROM servicos"):
    print(s["id"], s["nome"], s["preco"], s["duracao_min"])
conn.close()