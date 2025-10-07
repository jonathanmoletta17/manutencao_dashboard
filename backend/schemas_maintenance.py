"""
Schemas Pydantic para o Dashboard de Manutenção
Define modelos de resposta da API específicos para métricas de manutenção.
"""
from pydantic import BaseModel


class MaintenanceGeneralStats(BaseModel):
    """Estatísticas gerais de tickets de manutenção por status."""
    novos: int
    pendentes: int
    planejados: int
    resolvidos: int


class MaintenanceStatusTotals(BaseModel):
    """Totais gerais por status, alinhados ao script PowerShell."""
    novos: int
    em_atendimento: int   # (2)
    nao_solucionados: int  # (2 + 4)
    planejados: int        # (3)
    solucionados: int      # (5)
    fechados: int          # (6)
    resolvidos: int        # (5 + 6)


class EntityRankingItem(BaseModel):
    """Item de ranking por entidade."""
    entity_name: str
    ticket_count: int


class CategoryRankingItem(BaseModel):
    """Item de ranking por categoria."""
    category_name: str
    ticket_count: int


class MaintenanceNewTicketItem(BaseModel):
    """Ticket novo de manutenção."""
    id: int
    titulo: str
    solicitante: str
    data: str
    entidade: str