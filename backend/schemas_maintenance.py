"""
Schemas Pydantic para o Dashboard de Manutenção
Define modelos de resposta da API específicos para métricas de manutenção.
"""
from pydantic import BaseModel, Field


class MaintenanceGeneralStats(BaseModel):
    """Estatísticas gerais de tickets de manutenção por status."""
    novos: int = Field(..., description="Novos (status 1) no período selecionado")
    em_atendimento: int = Field(..., description="Em atendimento (status 2 - Atribuído/Em progresso) no período")
    pendentes: int = Field(..., description="Pendentes (status 4) no período")
    planejados: int = Field(..., description="Planejados (status 3) no período")
    resolvidos: int = Field(..., description="Resolvidos (status 5 + 6) no período")


class EntityRankingItem(BaseModel):
    """Item de ranking por entidade."""
    entity_name: str = Field(..., description="Nome completo da entidade (ou label resolvido)")
    ticket_count: int = Field(..., description="Total de tickets atribuídos à entidade")


class CategoryRankingItem(BaseModel):
    """Item de ranking por categoria."""
    category_name: str = Field(..., description="Nome completo da categoria (ou label resolvido)")
    ticket_count: int = Field(..., description="Total de tickets atribuídos à categoria")


class TechnicianRankingItem(BaseModel):
    """Item de ranking por técnico (nome e total de tickets)."""
    tecnico: str = Field(..., description="Nome do técnico")
    tickets: int = Field(..., description="Total de tickets atribuídos ao técnico")


class MaintenanceNewTicketItem(BaseModel):
    """Ticket novo de manutenção."""
    id: int = Field(..., description="ID do ticket")
    titulo: str = Field(..., description="Título do ticket")
    solicitante: str = Field(..., description="Nome do solicitante (resolvido quando possível)")
    data: str = Field(..., description="Data de criação formatada (dd/MM/yyyy HH:mm)")
    entidade: str = Field(..., description="Nome da entidade associada ao ticket")