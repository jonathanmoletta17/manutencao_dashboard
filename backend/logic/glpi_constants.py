"""
Constantes de campos e status do GLPI centralizadas.

Origem dos IDs
----------------
- Os valores abaixo correspondem aos IDs de opções de busca (search options)
  do GLPI para o itemtype `Ticket`.
- Foram validados contra o ambiente GLPI em uso e devem ser conferidos
  sempre que houver atualização de versão ou customizações.
- Como validar: consultar as "Search Options" do item `Ticket` no GLPI
  (via API de busca, documentação oficial do GLPI, ou tela de configuração).

Apenas constantes utilizadas pelo dashboard permanecem aqui para evitar
acoplamento desnecessário.
"""

# Campos de Ticket
FIELD_ID = 2           # Ticket.id
FIELD_NAME = 1         # Ticket.name (título)
FIELD_STATUS = 12      # Ticket.status
FIELD_CREATED = 15     # Ticket.date (data de criação)
FIELD_TECH = 5         # Ticket.assigned_to (técnico atribuído)
FIELD_REQUESTER = 4    # Ticket.requester (solicitante)
FIELD_ENTITY = 80      # Ticket.entities_id (entidade)
FIELD_CATEGORY = 7     # Ticket.itilcategories_id (categoria)

# Status simplificados (apenas os usados diretamente)
STATUS_NEW = 1         # Novo
STATUS_ASSIGNED = 2    # Em atendimento (Atribuído/Em progresso)
STATUS_PLANNED = 3     # Planejado
STATUS_PENDING = 4     # Pendente
STATUS_SOLVED = 5      # Solucionado
STATUS_CLOSED = 6      # Fechado

# Mapa de rótulos de status (para documentação/validação)
STATUS_LABELS = {
    STATUS_NEW: 'Novo',
    STATUS_ASSIGNED: 'Em atendimento',
    STATUS_PLANNED: 'Planejado',
    STATUS_PENDING: 'Pendente',
    STATUS_SOLVED: 'Solucionado',
    STATUS_CLOSED: 'Fechado',
}

"""
Notas de validação
------------------
- Validar IDs de campos e status contra as Search Options do GLPI (item `Ticket`).
- Revisar após atualizações de versão/customizações do GLPI.
- Remover entradas não utilizadas para evitar acoplamento desnecessário.
"""