# Módulo 1 - Cadastro de clientes e veículos

## O que adicionar
- Cliente: nome, CPF, telefone, e-mail, data de cadastro
- Veículo: placa, marca, modelo, cor, ano e porte (moto, carro pequeno, SUV, caminhonete)
- Um cliente pode ter vários veículos
- Busca por nome, telefone ou placa
- Histórico de serviços por cliente e por veículo
- Editar e inativar cadastros

## Como deve funcionar
- Cadastra o cliente primeiro e depois o veículo
- Valida CPF e placa (ABC-1234 e Mercosul ABC1D23)
- Placa duplicada é bloqueada
- Cliente com histórico só é inativado, nunca excluído
- O porte do veículo define o preço do serviço (módulo 2)
