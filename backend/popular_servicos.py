from lavaAjato import conectar

servicos = [
    ("Higienização interna", 40.0, 15),
    ("Lavagem interna", 60.0, 30),
    ("Shampoo automotivo", 70.0, 30),
]

conn = conectar()


total = conn.execute("SELECT COUNT(*) FROM servicos").fetchone()[0]
if total == 0:
    conn.executemany(
        "INSERT INTO servicos (nome, preco, duracao_min) VALUES (?, ?, ?)",
        servicos,
    )
    conn.commit()
    print("Serviços inseridos!")
else:
    print("Já existem serviços no banco.")

conn.close()