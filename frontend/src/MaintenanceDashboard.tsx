import { 
  useState, 
  useEffect,
  useRef,
  useMemo,
  useCallback
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
    fetchMaintenanceNewTickets,
    fetchEntityRanking,
    fetchCategoryRanking,
    fetchTechnicianRanking
  } from './services/maintenance-api';
  import type { 
    MaintenanceGeneralStats,
    EntityRankingItem, 
    CategoryRankingItem,
    MaintenanceNewTicketItem,
    TechnicianRankingItem
  } from './types/maintenance-api.d';
  import { DateRangePicker } from './components/DateRangePicker';
  import { TopNSelect } from './components/TopNSelect';
  import TechnicianRanking from './components/TechnicianRanking';

export default function MaintenanceDashboard() {
  const [generalStats, setGeneralStats] = useState<MaintenanceGeneralStats | null>(null);
  
  const [entityRanking, setEntityRanking] = useState<EntityRankingItem[] | null>(null);
  const [categoryRanking, setCategoryRanking] = useState<CategoryRankingItem[] | null>(null);
  const [technicianRanking, setTechnicianRanking] = useState<TechnicianRankingItem[] | null>(null);
  const [newTickets, setNewTickets] = useState<MaintenanceNewTicketItem[] | null>(null);
  const [time, setTime] = useState<Date>(new Date());
  const [topN, setTopN] = useState<number>(() => {
    const url = new URL(window.location.href);
    const qsTop = url.searchParams.get('top');
    const n = qsTop ? Number(qsTop) : NaN;
    const allowed = [5, 10, 20, 50];
    return allowed.includes(n) ? n : 5;
  });
  const [dateRange, setDateRange] = useState<{ inicio: string; fim: string }>(() => {
    const toYmd = (d: Date) => d.toISOString().slice(0, 10);
    const url = new URL(window.location.href);
    const qsInicio = url.searchParams.get('inicio');
    const qsFim = url.searchParams.get('fim');
    if (qsInicio && qsFim && qsInicio <= qsFim) {
      return { inicio: qsInicio, fim: qsFim };
    }
    const now = new Date();
    const end = new Date(now);
    const start = new Date(now);
    start.setDate(start.getDate() - 30);
    return { inicio: toYmd(start), fim: toYmd(end) };
  });

  const refreshInFlight = useRef(false);
  const dateRangeRef = useRef(dateRange);
  const topNRef = useRef(topN);
  
  useEffect(() => {
    dateRangeRef.current = dateRange;
  }, [dateRange]);

  useEffect(() => {
    topNRef.current = topN;
  }, [topN]);

  const fmt = (n: number | undefined | null) =>
    n !== undefined && n !== null
      ? new Intl.NumberFormat('pt-BR').format(n)
      : '-';

  // Remove o prefixo do pai "Origem > PIRATINI" quando a entidade não é exatamente o pai
  const stripParentPrefix = (name: string) => {
    const PARENT = 'Origem > PIRATINI';
    const s = (name || '').trim();
    const norm = s.replace(/\s*>\s*/g, ' > ');
    const lower = norm.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    const parentLower = PARENT.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    if (lower === parentLower) return s;
    if (lower.startsWith(parentLower + ' > ')) return norm.slice(PARENT.length + 3).trim();
    return s;
  };

  // Abreviação: usar apenas o primeiro e o último segmento, abreviando o primeiro por sigla conhecida ou acrônimo
  const abbreviateEntityName = (rawName: string) => {
    const name = stripParentPrefix(rawName ?? '');
    const norm = name.replace(/\s*>\s*/g, ' > ').trim();
    if (!norm) return name;
    const parts = norm.split(' > ').map((p) => p.trim()).filter(Boolean);
    if (parts.length <= 1) return parts[0] ?? name;
    const first = parts[0];
    const last = parts[parts.length - 1];

    const normalize = (s: string) => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    const SIGLAS_PRIMEIRO: Record<string, string> = {
      'casa civil': 'CC',
      'gabinete do governador': 'GG',
      'gabinete do vice-governador': 'GVG',
      'secom': 'SECOM',
      'casa militar': 'CM',
    };
    const firstKey = normalize(first);
    let sigla = SIGLAS_PRIMEIRO[firstKey];
    if (!sigla) {
      const stop = new Set(['da','de','do','dos','das','e']);
      const words = firstKey.split(/\s+/).filter((w) => w && !stop.has(w));
      sigla = words.filter((w) => w.length >= 3).map((w) => w[0]).join('').slice(0,4).toUpperCase();
      if (!sigla) sigla = (first.trim().slice(0,3) || first).toUpperCase();
    }

    if (!last || normalize(last) === firstKey) return first; // evita duplicação
    return `${sigla} > ${last}`;
  };

  const applyDateRange = () => {
    const { inicio, fim } = dateRangeRef.current;
    const url = new URL(window.location.href);
    url.searchParams.set('inicio', inicio);
    url.searchParams.set('fim', fim);
    url.searchParams.set('top', String(topNRef.current));
    window.history.replaceState(null, '', `${url.pathname}?${url.searchParams.toString()}`);
    loadDashboardData();
  };

  const loadDashboardDataWith = async (inicio?: string, fim?: string) => {
    // Stats gerais por período
    try {
      const inRange = inicio ?? dateRangeRef.current.inicio;
      const endRange = fim ?? dateRangeRef.current.fim;
      const gs = await fetchMaintenanceGeneralStats(inRange, endRange);
      setGeneralStats(gs);
    } catch (err) {
      console.error('Falha ao buscar Estatísticas Gerais:', err);
    }

    // Ranking por entidades filtrado por período (como stats gerais)
    try {
      const inRange = inicio ?? dateRangeRef.current.inicio;
      const endRange = fim ?? dateRangeRef.current.fim;
      const topParam = topNRef.current;
      const er = await fetchEntityRanking(inRange, endRange, topParam);
      setEntityRanking(er);
    } catch (err) {
      console.error('Falha ao buscar Ranking de Entidades (por período):', err);
    }

    // Ranking por categorias filtrado por período
    // Para garantir itens suficientes em cada macro área, buscamos 3x TopN
    try {
      const inRange = inicio ?? dateRangeRef.current.inicio;
      const endRange = fim ?? dateRangeRef.current.fim;
      const topParam = topNRef.current;
      const cr = await fetchCategoryRanking(inRange, endRange, Math.max(topParam * 3, 15));
      setCategoryRanking(cr);
    } catch (err) {
      console.error('Falha ao buscar Ranking de Categorias (por período):', err);
    }

    try {
      const nt = await fetchMaintenanceNewTickets(8);
      setNewTickets(nt);
    } catch (err) {
      console.error('Falha ao buscar Tickets Novos:', err);
    }

    // Ranking de técnicos (sem níveis na manutenção)
    try {
      const inRange = inicio ?? dateRangeRef.current.inicio;
      const endRange = fim ?? dateRangeRef.current.fim;
      const topParam = topNRef.current;
      const tk = await fetchTechnicianRanking(inRange, endRange, topParam);
      setTechnicianRanking(tk);
    } catch (err) {
      console.error('Falha ao buscar Ranking de Técnicos:', err);
    }

    // Em atendimento agora vem do stats-gerais (com filtro de datas)
  };

  // Wrapper para recarregar dados usando o intervalo atual
  const loadDashboardData = async () => {
    const { inicio, fim } = dateRangeRef.current;
    await loadDashboardDataWith(inicio, fim);
  };

  useEffect(() => {
    (async () => {
      const { inicio, fim } = dateRangeRef.current;
      await loadDashboardDataWith(inicio, fim);
    })();
  }, []);

  // Atualizar dados quando Top N mudar
  useEffect(() => {
    const { inicio, fim } = dateRangeRef.current;
    loadDashboardDataWith(inicio, fim);
  }, [topN]);

  // Persistir Top N no URL sempre que o usuário alterar
  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set('top', String(topN));
    window.history.replaceState(null, '', `${url.pathname}?${url.searchParams.toString()}`);
  }, [topN]);

  // Polling configurável via .env (usa apenas VITE_REALTIME_POLL_INTERVAL_SEC)
  useEffect(() => {
    const env = (import.meta as unknown as { env: Record<string, string | undefined> }).env;
    const rawPollSec = env?.VITE_REALTIME_POLL_INTERVAL_SEC;
    const intervalMs = rawPollSec !== undefined ? Number(rawPollSec) * 1000 : 15000;
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

  // Totais de status agora são atualizados junto ao polling em loadDashboardDataWith

  // ====== Classificação por macro área e carrossel ======
  const removeDiacritics = (s: string) => s ? s.normalize('NFD').replace(/[\u0300-\u036f]/g, '') : s;
  const classifyMacroArea = useCallback((label: string) => {
    if (!label) return 'Outros' as const;
    const first = label.split('>', 1)[0].trim();
    const plain = removeDiacritics(first).toLowerCase();
    if (plain.startsWith('manutencao')) return 'Manutenção' as const;
    if (plain.startsWith('conservacao')) return 'Conservação' as const;
    return 'Outros' as const;
  }, []);

  const { manCategories, consCategories, outsCategories } = useMemo(() => {
    const man: CategoryRankingItem[] = [];
    const cons: CategoryRankingItem[] = [];
    const outs: CategoryRankingItem[] = [];
    (categoryRanking ?? []).forEach((item) => {
      const grp = classifyMacroArea(item.category_name);
      if (grp === 'Manutenção') man.push(item);
      else if (grp === 'Conservação') cons.push(item);
      else outs.push(item);
    });
    // ordenar por ticket_count desc para garantir Top 5 correto por grupo
    man.sort((a, b) => (b.ticket_count ?? 0) - (a.ticket_count ?? 0));
    cons.sort((a, b) => (b.ticket_count ?? 0) - (a.ticket_count ?? 0));
    outs.sort((a, b) => (b.ticket_count ?? 0) - (a.ticket_count ?? 0));
    return { manCategories: man, consCategories: cons, outsCategories: outs };
  }, [categoryRanking, classifyMacroArea]);

  const [currentCategoryArea, setCurrentCategoryArea] = useState<'Manutenção' | 'Conservação' | 'Outros'>('Manutenção');

  useEffect(() => {
    const env = (import.meta as unknown as { env: Record<string, string | undefined> }).env;
    const rawCarouselMs = env?.VITE_CATEGORY_CAROUSEL_INTERVAL_MS;
    const rawCarouselSec = env?.VITE_CATEGORY_CAROUSEL_INTERVAL_SEC;
    const intervalMs = rawCarouselMs !== undefined
      ? Number(rawCarouselMs)
      : rawCarouselSec !== undefined
        ? Number(rawCarouselSec) * 1000
        : 15000;
    const id = setInterval(() => {
      setCurrentCategoryArea((prev) => (prev === 'Manutenção' ? 'Conservação' : (prev === 'Conservação' ? 'Outros' : 'Manutenção')));
    }, intervalMs);
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
          {/* Seletor Top N (dropdown customizado) */}
          <div className="flex items-center gap-2 px-2 border-l border-white/20">
            <label className="text-sm text-blue-100">Top N</label>
            <TopNSelect value={topN} onChange={(n) => setTopN(n)} />
          </div>
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
      <div className="p-6 h-[calc(100vh-64px)] flex flex-col gap-4 overflow-hidden">
        {/* Stats Gerais - Linha superior (período selecionado) */}
        <div className="grid grid-cols-5 gap-3">
          <Card className="bg-white border-l-4 border-l-[#5A9BD4] shadow-sm">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Novos</p>
                  <p className="text-xl font-semibold text-gray-900">{fmt(generalStats?.novos)}</p>
                </div>
                <div className="w-10 h-10 p-1 bg-[#5A9BD4]/10 rounded-xl flex items-center justify-center shrink-0">
                  <TrendingUp className="w-5 h-5 text-[#5A9BD4]" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Em atendimento (status 2 - atribuído/em progresso) por período */}
          <Card className="bg-white border-l-4 border-l-sky-500 shadow-sm">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Em atendimento</p>
                  <p className="text-xl font-semibold text-gray-900">{fmt(generalStats?.em_atendimento)}</p>
                </div>
                <div className="w-10 h-10 p-1 bg-sky-100 rounded-xl flex items-center justify-center shrink-0">
                  <Clock className="w-5 h-5 text-sky-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-l-4 border-l-amber-500 shadow-sm">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Pendentes</p>
                  <p className="text-xl font-semibold text-gray-900">{fmt(generalStats?.pendentes)}</p>
                </div>
                <div className="w-10 h-10 p-1 bg-amber-100 rounded-xl flex items-center justify-center shrink-0">
                  <Clock className="w-5 h-5 text-amber-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-l-4 border-l-purple-500 shadow-sm">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Planejados</p>
                  <p className="text-xl font-semibold text-gray-900">{fmt(generalStats?.planejados)}</p>
                </div>
                <div className="w-10 h-10 p-1 bg-purple-100 rounded-xl flex items-center justify-center shrink-0">
                  <Clock className="w-5 h-5 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-l-4 border-l-green-500 shadow-sm">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Resolvidos</p>
                  <p className="text-xl font-semibold text-gray-900">{fmt(generalStats?.resolvidos)}</p>
                </div>
                <div className="w-10 h-10 p-1 bg-green-100 rounded-xl flex items-center justify-center shrink-0">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content - 2 colunas */}
        <div className="flex gap-4 flex-1 min-h-0">
          {/* Coluna Esquerda - Rankings (flexível) */}
          <div className="flex-1 min-w-0 min-h-0 flex flex-col gap-4">
            <Card className="bg-white shadow-sm border-0 flex-1 min-h-0 flex flex-col overflow-hidden">
              <CardHeader className="pb-2 flex-none">
                <CardTitle className="flex items-center gap-2 text-[#5A9BD4] text-base">
                  <Building2 className="w-4 h-4" />
                  {`Top ${topN} - Atribuição por Entidades`}
                </CardTitle>
              </CardHeader>
              <CardContent className="px-4 pb-3 flex-1 min-h-0 space-y-2 overflow-y-auto pr-1">
                {(entityRanking ?? []).map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between gap-3 md:gap-4 p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1 pr-2">
                      <span className="text-xs font-bold text-gray-600 w-7">#{idx + 1}</span>
                      <span className="text-sm text-gray-900 font-medium truncate" title={stripParentPrefix(item.entity_name)}>{abbreviateEntityName(item.entity_name)}</span>
                    </div>
                    <Badge className="bg-[#5A9BD4] text-white text-xs px-3 py-1 rounded-md shrink-0 ml-1 md:ml-2">
                      {fmt(item.ticket_count)}
                    </Badge>
                  </div>
                ))}
                {(!entityRanking || entityRanking.length === 0) && (
                  <div className="text-center text-xs text-gray-500 py-4">Ranking indisponível</div>
                )}
              </CardContent>
            </Card>

            {/* Ranking Categorias */}
            <Card className="bg-white shadow-sm border-0 flex-1 min-h-0 flex flex-col overflow-hidden">
            <CardHeader className="pb-2 flex-none">
              <CardTitle className="flex items-center gap-2 text-[#5A9BD4] text-base">
                <FolderKanban className="w-4 h-4" />
                {`Top ${topN} - Atribuição por Categorias (${currentCategoryArea})`}
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-3 flex-1 min-h-0 space-y-2 overflow-y-auto pr-1">
              {(() => {
                const items = (
                  currentCategoryArea === 'Manutenção' ? manCategories :
                  currentCategoryArea === 'Conservação' ? consCategories : outsCategories
                ).slice(0, topN);
                return items.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-bold text-gray-600 w-7">#{idx + 1}</span>
                      <span className="text-sm text-gray-900 font-medium truncate">{item.category_name}</span>
                    </div>
                    <Badge className="bg-[#5A9BD4] text-white text-xs px-3 py-1 rounded-md shrink-0">{fmt(item.ticket_count)}</Badge>
                  </div>
                ));
              })()}
              {(
                (!categoryRanking || categoryRanking.length === 0) ||
                ((currentCategoryArea === 'Manutenção' ? manCategories : (currentCategoryArea === 'Conservação' ? consCategories : outsCategories)).length === 0)
              ) && (
                <div className="text-center text-xs text-gray-500 py-4">Sem itens nesta área no período</div>
              )}
            </CardContent>
          </Card>
            {/* Ranking Técnicos */}
            <TechnicianRanking items={technicianRanking} topN={topN} />
            {/* Ranking Entidades */}
          </div>

          {/* Coluna Direita - Tickets Novos (largura restaurada) */}
          <div className="w-135 flex-shrink-0">
            <Card className="bg-white shadow-sm border-0 h-full flex flex-col">
              <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-[#5A9BD4] text-lg">
                    <Ticket className="w-5 h-5" />
                    Tickets Novos
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded-md">{newTickets ? `${newTickets.length} tickets` : '0 tickets'}</span>
                    <Button variant="ghost" size="sm" className="text-gray-500 hover:text-gray-700 hover:bg-gray-100" onClick={loadDashboardData}>
                      <RotateCcw className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-hidden p-0">
                <div 
                  className="h-full overflow-y-auto px-6 pb-6 [&::-webkit-scrollbar]:w-[6px] [&::-webkit-scrollbar-track]:bg-slate-100 [&::-webkit-scrollbar-track]:rounded-sm [&::-webkit-scrollbar-thumb]:bg-[#5A9BD4] [&::-webkit-scrollbar-thumb]:rounded-sm [&::-webkit-scrollbar-thumb:hover]:bg-[#4A8BC2]"
                  style={{ scrollbarWidth: 'thin', scrollbarColor: '#5A9BD4 #f1f5f9' }}
                >
                  <div className="space-y-3">
                    {(newTickets ?? []).map((item) => (
                      <div key={item.id} className="border-l-4 border-[#5A9BD4] bg-[#5A9BD4]/5 p-3 rounded-r-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded">#{item.id ?? '-'}</span>
                          <Badge variant="outline" className="border-[#5A9BD4] text-[#5A9BD4] bg-[#5A9BD4]/10 text-xs">Novo</Badge>
                        </div>
                        <h4 className="font-medium text-gray-900 mb-2 text-sm truncate" title={item.titulo}>{item.titulo}</h4>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-700 font-medium truncate" title={item.solicitante}>{item.solicitante}</span>
                          <div className="flex flex-col items-end w-48">
                            <span className="text-gray-600 whitespace-nowrap">{(item.data || '').split(' ')[1] || ''}</span>
                            <span className="text-gray-600 whitespace-nowrap">{(item.data || '').split(' ')[0] || item.data}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                    {(!newTickets || newTickets.length === 0) && (
                      <div className="w-full text-center text-xs text-gray-600 py-2">Sem tickets novos</div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}