# Módulo 3 - Agenda, reagendamentos e fila de atendimento

## O que adicionar
- Horário de funcionamento e bloqueio de dias (feriados)
- Capacidade: número de boxes/vagas simultâneas
- Agendamento: cliente, veículo, serviços, data/hora e previsão de término
- Reagendamento com histórico (data antiga e nova)
- Fila para quem chega sem agendar (senha numerada)
- Lista de espera e lembrete ao cliente (opcional)

## Como deve funcionar
- Só mostra horários livres, considerando duração e boxes
- Conflito de horário é bloqueado
- Reagendar libera o horário antigo
- Atraso de 15 min vira "não compareceu" e a vaga é liberada
- Fila segue ordem de chegada; cliente agendado tem prioridade
- Vaga liberada chama o próximo da lista de espera
