"""
Constantes de campos e status do GLPI centralizadas.

Somente os campos e status usados no dashboard foram definidos.
"""

# Campos de Ticket
FIELD_ID = 2
FIELD_NAME = 1
FIELD_LEVEL = 8
FIELD_STATUS = 12
FIELD_CREATED = 15
FIELD_TECH = 5
FIELD_ENTITY = 80
FIELD_CATEGORY = 7

# Campos de User (para buscas auxiliares)
FIELD_USER_ACTIVE = 8
FIELD_GROUP = 13

# Status de Ticket
STATUS = {
    "NEW": 1,
    "ASSIGNED": 2,
    "PLANNED": 3,
    "IN_PROGRESS": 4,
    "SOLVED": 5,
    "CLOSED": 6,
}

# Status simplificados para imports diretos
STATUS_NEW = 1
STATUS_PENDING_PLANNED = 4
STATUS_SOLVED = 5