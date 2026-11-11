from crud import criar_cliente, criar_agendamento, listar_servicos

print(listar_servicos())

cliente_id = criar_cliente("Nicolas Gabriel", "81989173082")
ag_id = criar_agendamento(cliente_id, 2, "2026-11-15", "14:00")
print("Agendamento criado:", ag_id)