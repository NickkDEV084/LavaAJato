# Módulo 4 - Pedidos e pagamentos

## O que adicionar
- Pedido (ordem de serviço) com número, cliente, veículo e itens
- Itens: serviços e produtos extras vendidos no balcão
- Desconto e total
- Formas: dinheiro, Pix, cartão de débito e de crédito
- Sinal / pagamento parcial
- Recibo e fechamento de caixa diário

## Como deve funcionar
- O pedido nasce do agendamento ou da fila
- Total = soma dos itens - desconto
- Status de pagamento: pendente, parcial, pago, estornado
- Veículo só é entregue após o pagamento (ou fiado autorizado pelo gerente)
- Estorno exige motivo e fica registrado
- O caixa soma os pagamentos do dia por forma de pagamento
