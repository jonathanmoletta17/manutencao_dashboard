import { useMemo } from "react";
import { Input } from "./ui/input";
import { Button } from "./ui/button";

type DateRange = { inicio: string; fim: string };

type Props = {
  value: DateRange;
  onChange: (_next: DateRange) => void;
  onApply?: () => void;
  className?: string;
};

export function DateRangePicker({ value, onChange, onApply, className }: Props) {
  const canApply = useMemo(() => {
    return Boolean(value?.inicio) && Boolean(value?.fim) && value.inicio <= value.fim;
  }, [value]);

  return (
    <div className={`flex items-center gap-2 bg-white/20 rounded-lg px-4 py-2 ${className ?? ""}`}>
      <div className="flex items-center gap-2">
        <span className="text-xs text-white/80">Início</span>
        <Input
          type="date"
          value={value.inicio}
          onChange={(e) => onChange({ ...value, inicio: e.target.value })}
          className="bg-transparent border-none text-white placeholder:text-white/70"
        />
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-white/80">Fim</span>
        <Input
          type="date"
          value={value.fim}
          onChange={(e) => onChange({ ...value, fim: e.target.value })}
          className="bg-transparent border-none text-white placeholder:text-white/70"
        />
      </div>
      {onApply && (
        <Button
          disabled={!canApply}
          variant="ghost"
          size="sm"
          className="text-white hover:bg-blue-600"
          onClick={onApply}
        >
          Aplicar
        </Button>
      )}
    </div>
  );
}