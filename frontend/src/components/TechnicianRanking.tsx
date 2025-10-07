import { Award } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import type { TechnicianRankingItem } from "../types/maintenance-api.d";

interface TechnicianRankingProps {
  items: TechnicianRankingItem[] | null;
  title?: string;
  topN?: number;
}

const shortName = (name: string) => {
  const parts = (name || '').trim().split(/\s+/);
  if (parts.length === 0) return '-';
  if (parts.length === 1) return parts[0];
  const first = parts[0];
  const lastInitial = parts[parts.length - 1].charAt(0);
  return `${first} ${lastInitial}.`;
};

const fmt = (n: number | undefined | null) =>
  n !== undefined && n !== null
    ? new Intl.NumberFormat('pt-BR').format(n)
    : '-';

export function TechnicianRanking({ items, title = 'Ranking de Técnicos', topN }: TechnicianRankingProps) {
  const normalize = (s: string) => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  // Defesa em profundidade: ocultar qualquer item identificado como "Sem técnico"
  const filtered = (items ?? []).filter((it) => normalize(it.tecnico) !== 'sem tecnico');
  const list = filtered.slice(0, topN ?? filtered.length);

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
                e.preventDefault();
                target.scrollLeft += e.deltaY;
              }
            }}
          >
            <div className="inline-flex w-max gap-3">
              {list.map((tech, idx) => {
                const isFirst = idx === 0;
                const isSecond = idx === 1;
                const isThird = idx === 2;
                const isTop3 = isFirst || isSecond || isThird;
                const baseClasses = isTop3
                  ? 'flex-shrink-0 w-56 bg-gradient-to-br text-white p-3 rounded-lg shadow-sm'
                  : 'flex-shrink-0 w-56 bg-gray-50 border border-gray-200 text-gray-900 p-3 rounded-lg shadow-sm';
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
                  <div key={`${tech.tecnico}-${idx}`} className={`${baseClasses} ${gradientClasses}`}>
                    <div className="text-center">
                      <Badge className={`${badgeClasses} mb-2 font-medium text-xs`} variant={isTop3 ? undefined : 'outline'}>
                        #{idx + 1}
                      </Badge>
                      <p className={`text-xs font-medium mb-1 ${isTop3 ? '' : 'text-gray-900'}`}>{shortName(tech.tecnico)}</p>
                      <p className={`text-xs mb-2 ${isFirst ? 'text-blue-100' : isSecond ? 'text-slate-200' : isThird ? 'text-orange-100' : 'text-gray-600'}`}>{tech.tecnico}</p>
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