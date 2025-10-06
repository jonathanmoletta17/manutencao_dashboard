import { 
  useState, 
  useEffect,
  useRef
} from 'react';
import {
  RotateCcw,
  User,
  TrendingUp,
  Clock,
  CheckCircle,
  Wrench,
  Building2,
  FolderKanban,
  Ticket,
} from "lucide-react";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { 
  fetchMaintenanceGeneralStats, 
  fetchMaintenanceStatusTotals,
  fetchEntityRanking, 
  fetchCategoryRanking,
  fetchMaintenanceNewTickets,
  fetchTopEntityAttribution
} from './services/maintenance-api';
import type { 
  MaintenanceGeneralStats, 
  MaintenanceStatusTotals,
  EntityRankingItem, 
  CategoryRankingItem,
  MaintenanceNewTicketItem 
} from './types/maintenance-api.d';
import { DateRangePicker } from './components/DateRangePicker';

export default function MaintenanceDashboard() {
  const [generalStats, setGeneralStats] = useState<MaintenanceGeneralStats | null>(null);
  const [statusTotals, setStatusTotals] = useState<MaintenanceStatusTotals | null>(null);
  const [entityRanking, setEntityRanking] = useState<EntityRankingItem[] | null>(null);
  const [categoryRanking, setCategoryRanking] = useState<CategoryRankingItem[] | null>(null);
  const [newTickets, setNewTickets] = useState<MaintenanceNewTicketItem[] | null>(null);
  const [time, setTime] = useState<Date>(new Date());
  const [dateRange, setDateRange] = useState<{ inicio: string; fim: string }>(() => {
    const toYmd = (d: Date) => d.toISOString().slice(0, 10);
    const now = new Date();
    const end = new Date(now);
    const start = new Date(now);
    start.setDate(start.getDate() - 30);
    return { inicio: toYmd(start), fim: toYmd(end) };
  });

  const refreshInFlight = useRef(false);
  const dateRangeRef = useRef(dateRange);
  
  useEffect(() => {
    dateRangeRef.current = dateRange;
  }, [dateRange]);

  const fmt = (n: number | undefined | null) =>
    n !== undefined && n !== null
      ? new Intl.NumberFormat('pt-BR').format(n)
      : '-';

  const applyDateRange = () => {
    loadDashboardData();
  };

  const loadDashboardDataWith = async (inicio: string, fim: string) => {
    // Totais gerais por status (sem filtro de data)
    try {
      const st = await fetchMaintenanceStatusTotals();
      setStatusTotals(st);
    } catch (err) {
      console.error('Falha ao buscar Status Totais:', err);
    }

    try {
      const gs = await fetchMaintenanceGeneralStats(inicio, fim);
      setGeneralStats(gs);
    } catch (err) {
      console.error('Falha ao buscar Estatísticas Gerais:', err);
    }

    try {
      const er = await fetchTopEntityAttribution(5);
      setEntityRanking(er);
    } catch (err) {
      console.error('Falha ao buscar Ranking de Entidades (Top atribuição global):', err);
    }

    try {
      const cr = await fetchCategoryRanking(inicio, fim, 5);
      setCategoryRanking(cr);
    } catch (err) {
      console.error('Falha ao buscar Ranking de Categorias:', err);
    }

    try {
      const nt = await fetchMaintenanceNewTickets(8);
      setNewTickets(nt);
    } catch (err) {
      console.error('Falha ao buscar Tickets Novos:', err);
    }
  };

  const loadDashboardData = async () => {
    const { inicio, fim } = dateRangeRef.current;
    await loadDashboardDataWith(inicio, fim);
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Polling de 15s
  useEffect(() => {
    const intervalMs = Number(import.meta.env.VITE_REALTIME_POLL_INTERVAL_SEC ?? 15000);
    const id = setInterval(async () => {
      if (refreshInFlight.current) return;
      refreshInFlight.current = true;
      try {
        const { inicio, fim } = dateRangeRef.current;
        await loadDashboardDataWith(inicio, fim);
      } finally {
        refreshInFlight.current = false;
      }
    }, intervalMs);
    return () => clearInterval(id);
  }, []);

  // Relógio
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-[#5A9BD4] text-white p-3 px-6 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-4">
          <Wrench className="w-6 h-6" />
          <div>
            <h1 className="text-xl font-semibold">Divisão de Manutenção</h1>
            <p className="text-sm text-blue-100">Dashboard de Métricas</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <DateRangePicker
            value={dateRange}
            onChange={setDateRange}
            onApply={applyDateRange}
            className="w-auto"
          />
          <Button variant="ghost" size="sm" className="text-white hover:bg-blue-600" onClick={loadDashboardData}>
            <RotateCcw className="w-4 h-4" />
          </Button>
          <div className="flex items-center gap-3 pl-4 border-l border-white/20">
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <div className="text-sm">
              <p className="text-blue-100 text-xs">{time.toLocaleTimeString('pt-BR')}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Content - Layout otimizado para tela cheia */}
      <div className="p-4 h-[calc(100vh-64px)] flex flex-col gap-3">
        {/* Stats Cards - Linha superior (período) */}
        <div className="grid grid-cols-4 gap-3">
          <Card className="bg-white border-l-4 border-l-[#5A9BD4] shadow-sm">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Novos</p>
                  <p className="text-xl font-semibold text-gray-900">{fmt(statusTotals?.novos)}</p>
                </div>
                <div className="w-9 h-9 bg-[#5A9BD4]/10 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-[#5A9BD4]" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-l-4 border-l-amber-500 shadow-sm">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Pendentes</p>
                  <p className="text-xl font-semibold text-gray-900">{fmt(statusTotals?.nao_solucionados)}</p>
                </div>
                <div className="w-9 h-9 bg-amber-100 rounded-lg flex items-center justify-center">
                  <Clock className="w-4 h-4 text-amber-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-l-4 border-l-purple-500 shadow-sm">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Planejados</p>
                  <p className="text-xl font-semibold text-gray-900">{fmt(statusTotals?.planejados)}</p>
                </div>
                <div className="w-9 h-9 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Clock className="w-4 h-4 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-l-4 border-l-green-500 shadow-sm">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Resolvidos</p>
                  <p className="text-xl font-semibold text-gray-900">{fmt(statusTotals?.resolvidos)}</p>
                </div>
                <div className="w-9 h-9 bg-green-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content - 2 colunas */}
        <div className="grid grid-cols-2 gap-3 flex-1 min-h-0">
          {/* Coluna Esquerda - Rankings */}
          <div className="flex flex-col gap-3 min-h-0">
            {/* Ranking Entidades */}
            <Card className="bg-white shadow-sm border-0 flex-1 min-h-0 flex flex-col">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-[#5A9BD4] text-base">
                  <Building2 className="w-4 h-4" />
                  Top 5 - Atribuição por Entidades
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-auto px-4 pb-3">
                <div className="space-y-2">
                  {(entityRanking ?? []).map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-gray-500 w-6">#{idx + 1}</span>
                        <span className="text-sm text-gray-900 font-medium truncate">{item.entity_name}</span>
                      </div>
                      <Badge className="bg-[#5A9BD4] text-white text-xs">{fmt(item.ticket_count)}</Badge>
                    </div>
                  ))}
                  {(!entityRanking || entityRanking.length === 0) && (
                    <div className="text-center text-xs text-gray-500 py-4">Ranking indisponível</div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Ranking Categorias */}
            <Card className="bg-white shadow-sm border-0 flex-1 min-h-0 flex flex-col">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-[#5A9BD4] text-base">
                  <FolderKanban className="w-4 h-4" />
                  Top 5 - Atribuição por Categorias
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-auto px-4 pb-3">
                <div className="space-y-2">
                  {(categoryRanking ?? []).map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-gray-500 w-6">#{idx + 1}</span>
                        <span className="text-sm text-gray-900 font-medium truncate">{item.category_name}</span>
                      </div>
                      <Badge className="bg-[#5A9BD4] text-white text-xs">{fmt(item.ticket_count)}</Badge>
                    </div>
                  ))}
                  {(!categoryRanking || categoryRanking.length === 0) && (
                    <div className="text-center text-xs text-gray-500 py-4">Ranking indisponível</div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Coluna Direita - Tickets Novos */}
          <Card className="bg-white shadow-sm border-0 flex-1 min-h-0 flex flex-col">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-[#5A9BD4] text-base">
                <Ticket className="w-4 h-4" />
                Tickets Novos (Últimos)
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-auto px-4 pb-3">
              <div className="space-y-2">
                {(newTickets ?? []).map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-gray-500 w-10">#{item.id}</span>
                      <span className="text-sm text-gray-900 font-medium truncate">{item.titulo}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-[#5A9BD4] text-white text-xs">{item.entidade}</Badge>
                      <span className="text-xs text-gray-600">{item.data}</span>
                    </div>
                  </div>
                ))}
                {(!newTickets || newTickets.length === 0) && (
                  <div className="text-center text-xs text-gray-500 py-4">Sem tickets novos</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}