import { Award } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { fmt } from "../utils/format";
import type { TechnicianRankingItem } from "../types/maintenance-api.d";

interface TechnicianRankingProps {
  items: TechnicianRankingItem[] | null;
  title?: string;
}

// usa utilitário compartilhado fmt

export function TechnicianRanking({ items, title = 'Ranking de Técnicos' }: TechnicianRankingProps) {
  const normalize = (s: string) => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  // Defesa em profundidade: ocultar qualquer item identificado como "Sem técnico"
  const filtered = (items ?? []).filter((it) => normalize(it.tecnico) !== 'sem tecnico');
  const list = filtered;

  return (
    <Card className="bg-white shadow-sm border-0">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-[#5A9BD4] text-base">
          <Award className="w-4 h-4" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!(list && list.length > 0) ? (
          <div className="w-full text-center text-xs text-gray-600 py-2">Ranking indisponível</div>
        ) : (
          <div
            className="w-full overflow-x-auto [&::-webkit-scrollbar]:h-[6px] [&::-webkit-scrollbar-track]:bg-slate-100 [&::-webkit-scrollbar-track]:rounded-sm [&::-webkit-scrollbar-thumb]:bg-[#5A9BD4] [&::-webkit-scrollbar-thumb]:rounded-sm [&::-webkit-scrollbar-thumb:hover]:bg-[#4A8BC2]"
            style={{ overflowX: 'auto', scrollbarWidth: 'thin', scrollbarColor: '#5A9BD4 #f1f5f9', overscrollBehaviorX: 'contain' }}
            onWheel={(e) => {
              const target = e.currentTarget as HTMLDivElement;
              const canScrollHorizontally = target.scrollWidth > target.clientWidth;
              if (!canScrollHorizontally) return;
              if (Math.abs(e.deltaY) >= Math.abs(e.deltaX)) {
                if (e.cancelable) e.preventDefault();
                target.scrollLeft += e.deltaY;
              }
            }}
          >
            <div className="inline-flex w-max gap-3 pb-2">
              {list.map((tech, idx) => {
                const isFirst = idx === 0;
                const isSecond = idx === 1;
                const isThird = idx === 2;
                const isTop3 = isFirst || isSecond || isThird;
                const baseClasses = isTop3
                  ? 'flex-shrink-0 overflow-hidden bg-gradient-to-br text-white p-3 rounded-lg shadow-sm'
                  : 'flex-shrink-0 overflow-hidden bg-gray-50 border border-gray-200 text-gray-900 p-3 rounded-lg shadow-sm';
                const gradientClasses = isFirst
                  ? 'from-[#5A9BD4] to-[#4A8BC2]'
                  : isSecond
                  ? 'from-slate-600 to-slate-700'
                  : isThird
                  ? 'from-orange-600 to-orange-700'
                  : '';
                const badgeClasses = isFirst
                  ? 'bg-yellow-500 text-yellow-900'
                  : isSecond
                  ? 'bg-gray-300 text-gray-800'
                  : isThird
                  ? 'bg-orange-200 text-orange-900'
                  : '';

                return (
                  <div
                    key={`${tech.tecnico}-${idx}`}
                    className={`${baseClasses} ${gradientClasses}`}
                    style={{ width: 143, height: 117 }}
                  >
                    <div className="text-center">
                      <Badge className={`${badgeClasses} mb-2 font-medium text-xs`} variant={isTop3 ? undefined : 'outline'}>
                        #{idx + 1}
                      </Badge>
                      <p className={`text-xs font-semibold mb-2 text-gray-900`}>{tech.tecnico}</p>
                      <div className="space-y-1">
                        <div className="text-xs">
                          <span className={`${isTop3 ? (isFirst ? 'text-blue-100' : isSecond ? 'text-slate-200' : 'text-orange-100') : 'text-gray-600'}`}>Tickets:</span>
                          <span className="font-medium ml-1">{fmt(tech.tickets)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default TechnicianRanking;