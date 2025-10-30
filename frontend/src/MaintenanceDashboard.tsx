import { 
  useState, 
  useEffect
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
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
  import { DateRangePicker } from './components/DateRangePicker';
  import TechnicianRanking from './components/TechnicianRanking';
import { 
  readDateRangeFromUrl,
  replaceUrlParams,
  readCategoryModeFromUrl,
  replaceCategoryModeInUrl,
} from './services/url_params';
  import { useDashboardData } from './hooks/useDashboardData';
  import { useTechnicianRanking } from './hooks/useTechnicianRanking';
  import { useCategoryGrouping } from './hooks/useCategoryGrouping';
  import { useCarousel } from './hooks/useCarousel';
  import { fmt, fmtDateTimeParts, fmtTimeOfDay } from './utils/format';
  import { stripParentPrefix, abbreviateEntityName } from './utils/entity';
  import { useClock } from './hooks/useClock';

export default function MaintenanceDashboard() {
  const time = useClock();
  const [dateRange, setDateRange] = useState<{ inicio: string; fim: string }>(() => readDateRangeFromUrl(window.location.href));
  const [categoryMode, setCategoryMode] = useState<'original'|'aggregated'>(() => readCategoryModeFromUrl(window.location.href));

  // Removidos refs; usamos estados atuais diretamente

  // Helpers utilitários

  const { generalStats, entityRanking, categoryRanking, newTickets, refresh, error } = useDashboardData(dateRange);
  const { items: techItems } = useTechnicianRanking(dateRange);

  const applyDateRange = () => {
    replaceUrlParams({ inicio: dateRange.inicio, fim: dateRange.fim });
    refresh();
  };

  // Persistir Top N no URL sempre que o usuário alterar (evita duplicação)
  useEffect(() => {
    replaceUrlParams({ inicio: dateRange.inicio, fim: dateRange.fim });
  }, [dateRange]);

  // Relógio movido para useClock

  // Totais de status agora são atualizados junto ao polling em loadDashboardDataWith

  // ====== Classificação por macro área e carrossel ======
  const { manCategories, consCategories } = useCategoryGrouping(categoryRanking, categoryMode);
  const areas: ReadonlyArray<'Manutenção' | 'Conservação'> = ['Manutenção', 'Conservação'] as const;
  const { current: currentCategoryArea, setCurrent: setCurrentCategoryArea, goPrev: goPrevArea, goNext: goNextArea, schedulePause } = useCarousel(areas, 'Manutenção');

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-[#5A9BD4] text-white p-3 px-6 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-4">
          <Wrench className="w-6 h-6" />
          <div>
            <h1 className="text-xl font-semibold">Departamento de Manutenção e Conservação</h1>
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
          <Button variant="ghost" size="sm" className="text-white hover:bg-blue-600" onClick={refresh}>
            <RotateCcw className="w-4 h-4" />
          </Button>
          {/* Seletor Top N removido: exibe todos os itens */}
          <div className="flex items-center gap-3 pl-4 border-l border-white/20">
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <div className="text-sm">
            <p className="text-blue-100 text-xs">{fmtTimeOfDay(time)}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Erros globais do dashboard (ponto único de exibição) */}
      {error && (
        <div className="px-6 py-2 bg-red-50 border-l-4 border-red-500 text-red-700 text-sm">
          <span className="font-medium">Falha ao carregar dados do dashboard.</span> Tente novamente.
          <span className="ml-2 opacity-80">Detalhes: {error}</span>
        </div>
      )}

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
          <Card className="bg-white border-l-4 shadow-sm" style={{ borderLeftColor: '#1E3A8A' }}>
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Em atendimento</p>
                  <p className="text-xl font-semibold text-gray-900">{fmt(generalStats?.em_atendimento)}</p>
                </div>
                <div className="w-10 h-10 p-1 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: 'rgba(30,58,138,0.18)' }}>
                  <Clock className="w-5 h-5" style={{ color: '#1E3A8A' }} />
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

          <Card className="bg-white border-l-4 border-l-orange-500 shadow-sm">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Planejados</p>
                  <p className="text-xl font-semibold text-gray-900">{fmt(generalStats?.planejados)}</p>
                </div>
                <div className="w-10 h-10 p-1 bg-orange-100 rounded-xl flex items-center justify-center shrink-0">
                  <Clock className="w-5 h-5 text-orange-900" />
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

        {/* Conteúdo principal em duas colunas: Rankings à esquerda, Tickets Novos à direita */}
        <div className="flex gap-4 flex-1 min-h-0">
          {/* Coluna esquerda: Rankings (Entidades e Categorias lado a lado) */}
          <div className="flex-1 min-w-0 min-h-0 grid grid-cols-2 gap-4">
            {/* Ranking por Entidades */}
            <Card className="bg-white shadow-sm border-0 min-h-0 flex flex-col overflow-hidden">
              <CardHeader className="pb-2 flex-none">
                <CardTitle className="flex items-center gap-2 text-[#5A9BD4] text-base">
                  <Building2 className="w-4 h-4" />
                  {`Ranking por Entidades`}
                </CardTitle>
              </CardHeader>
              <CardContent className="px-2 pb-0 flex-1 min-h-0 overflow-hidden">
                <div
                  className="h-full min-h-0 overflow-y-auto px-2 space-y-3 pt-3 pb-3 [&::-webkit-scrollbar]:w-[6px] [&::-webkit-scrollbar-track]:bg-slate-100 [&::-webkit-scrollbar-track]:rounded-sm [&::-webkit-scrollbar-thumb]:bg-[#5A9BD4] [&::-webkit-scrollbar-thumb]:rounded-sm [&::-webkit-scrollbar-thumb:hover]:bg-[#4A8BC2]"
                  style={{ scrollbarWidth: 'thin', scrollbarColor: '#5A9BD4 #f1f5f9' }}
                >
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
                </div>
                {(!entityRanking || entityRanking.length === 0) && (
                  <div className="text-center text-xs text-gray-500 py-4">Ranking indisponível</div>
                )}
              </CardContent>
            </Card>

            {/* Ranking por Categorias */}
            <Card className="bg-white shadow-sm border-0 min-h-0 flex flex-col overflow-hidden">
              <CardHeader className="pb-2 flex-none">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-[#5A9BD4] text-base">
                    <FolderKanban className="w-4 h-4" />
                    {`Ranking por Categorias (${currentCategoryArea})`}
                  </CardTitle>
                  <div className="flex items-center">
                    <div className="flex items-center gap-2 mr-2 text-xs text-gray-600">
                      <span>Agregado</span>
                      <input
                        type="checkbox"
                        aria-label="Alternar modo agregado"
                        checked={categoryMode === 'aggregated'}
                        onChange={(e) => {
                          const next = e.target.checked ? 'aggregated' : 'original';
                          setCategoryMode(next);
                          replaceCategoryModeInUrl(next);
                        }}
                        className="cursor-pointer"
                      />
                    </div>
                    <button
                      type="button"
                      aria-label="Anterior"
                      className="text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md px-2 py-1"
                      onClick={goPrevArea}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <div className="flex items-center gap-1" aria-label="Indicadores de área">
                      {areas.map((a) => (
                        <button
                          key={a}
                          type="button"
                          aria-label={`Ir para ${a}`}
                          onClick={() => { setCurrentCategoryArea(a); schedulePause(); }}
                          className="rounded-full border-0"
                          style={{
                            width: 5,
                            height: 5,
                            backgroundColor: currentCategoryArea === a ? 'rgba(90,155,212,0.65)' : 'transparent',
                            border: currentCategoryArea === a ? '1px solid rgba(90,155,212,0.65)' : '1px solid rgba(0,0,0,0.22)',
                            opacity: currentCategoryArea === a ? 0.8 : 0.35
                          }}
                        />
                      ))}
                    </div>
                    <button
                      type="button"
                      aria-label="Próximo"
                      className="text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md px-2 py-1"
                      onClick={goNextArea}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="px-2 pb-0 flex-1 min-h-0 overflow-hidden">
                <div
                  className="h-full min-h-0 overflow-y-auto px-2 space-y-3 pt-3 pb-3 [&::-webkit-scrollbar]:w-[6px] [&::-webkit-scrollbar-track]:bg-slate-100 [&::-webkit-scrollbar-track]:rounded-sm [&::-webkit-scrollbar-thumb]:bg-[#5A9BD4] [&::-webkit-scrollbar-thumb]:rounded-sm [&::-webkit-scrollbar-thumb:hover]:bg-[#4A8BC2]"
                  style={{ scrollbarWidth: 'thin', scrollbarColor: '#5A9BD4 #f1f5f9' }}
                >
                  {(() => {
                    const items = (
                      currentCategoryArea === 'Manutenção' ? manCategories : consCategories
                    );
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
                </div>
                {(!categoryRanking || categoryRanking.length === 0) ? (
                  <div className="text-center text-xs text-gray-500 py-4">Ranking indisponível</div>
                ) : ((currentCategoryArea === 'Manutenção' ? manCategories : consCategories).length === 0) ? (
                  <div className="text-center text-xs text-gray-500 py-4">Sem itens nesta área no período</div>
                ) : null}
              </CardContent>
            </Card>
          </div>

          {/* Coluna direita: Tickets Novos (sidebar) */}
          <div className="w-130 flex-shrink-0">
            <Card className="bg-white shadow-sm border-0 h-full flex flex-col">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-[#5A9BD4] text-lg">
                    <Ticket className="w-5 h-5" />
                    Tickets Novos
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded-md">{newTickets ? `${newTickets.length} tickets` : '0 tickets'}</span>
                    <Button variant="ghost" size="sm" className="text-gray-500 hover:text-gray-700 hover:bg-gray-100" onClick={refresh}>
                      <RotateCcw className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-hidden px-2">
                <div 
                  className="h-full overflow-y-auto px-2 pb-6 [&::-webkit-scrollbar]:w-[6px] [&::-webkit-scrollbar-track]:bg-slate-100 [&::-webkit-scrollbar-track]:rounded-sm [&::-webkit-scrollbar-thumb]:bg-[#5A9BD4] [&::-webkit-scrollbar-thumb]:rounded-sm [&::-webkit-scrollbar-thumb:hover]:bg-[#4A8BC2]"
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
                            {(() => { const { time, date } = fmtDateTimeParts(item.data); return (
                              <>
                                <span className="text-gray-600 whitespace-nowrap">{time}</span>
                                <span className="text-gray-600 whitespace-nowrap">{date}</span>
                              </>
                            ); })()}
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

        {/* Ranking de Técnicos - largura total abaixo das colunas */}
        <div className="w-full">
          <TechnicianRanking items={techItems} />
        </div>
      </div>
    </div>
  );
}