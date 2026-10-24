# Módulo 6 - Status do serviço

## O que adicionar
- Etapas: Agendado, Aguardando, Em lavagem, Em acabamento, Pronto para retirada, Entregue
- Estados especiais: Cancelado e Não compareceu
- Data/hora e funcionário em cada mudança
- Observações e fotos de entrada (avarias)
- Aviso ao cliente quando estiver pronto
- Tempo real x tempo estimado

## Como deve funcionar
- Só transições válidas (não pula de Agendado para Pronto)
- Toda mudança grava uma linha no histórico (quem, quando, de qual para qual)
- Painel do lavador mostra a fila do dia
- Entregue só depois do pagamento (módulo 4)
- Pronto para retirada dispara a notificação
