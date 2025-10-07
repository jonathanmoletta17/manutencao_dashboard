import { useEffect, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import { Button } from "./ui/button";

type Props = {
  value: number;
  onChange: (n: number) => void;
};

// Componente separado para evitar remount em cada re-render do Dashboard
export function TopNSelect({ value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const options = [5, 10, 20, 50];
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e: PointerEvent) => {
      const el = containerRef.current;
      if (el && !el.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="text-white bg-white/10 hover:bg-white/20 border border-white/30 flex items-center gap-2"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="font-medium">{value}</span>
        <ChevronDown className="w-4 h-4 text-white" />
      </Button>
      {open && (
        <div className="absolute right-0 mt-1 w-24 bg-[#5A9BD4]/10 backdrop-blur-sm border border-white/30 rounded-md shadow-lg z-20">
          <ul className="py-1">
            {options.map((n) => (
              <li key={n}>
                <button
                  type="button"
                  className={`w-full text-left px-3 py-1.5 text-sm text-white ${
                    n === value ? "bg-white/20" : "hover:bg-white/10"
                  }`}
                  onClick={() => {
                    onChange(n);
                    setOpen(false);
                  }}
                >
                  {n}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}