import { useCallback, useEffect, useRef, useState } from 'react';

export interface CarouselOptions {
  intervalMs?: number; // se não fornecido, usa env VITE_CATEGORY_CAROUSEL_INTERVAL_MS/SEC
  pauseMs?: number; // default 20000
}

export function useCarousel<T>(areas: ReadonlyArray<T>, initial?: T, opts?: CarouselOptions) {
  const [current, setCurrent] = useState<T>(() => {
    if (initial !== undefined) return initial as T;
    return areas[0];
  });
  const pauseUntilRef = useRef<number>(0);
  const pauseMs = opts?.pauseMs ?? 20000;

  const schedulePause = useCallback(() => {
    pauseUntilRef.current = Date.now() + pauseMs;
  }, [pauseMs]);

  const goPrev = useCallback(() => {
    setCurrent((prev) => {
      const idx = areas.indexOf(prev);
      const nextIdx = (idx - 1 + areas.length) % areas.length;
      return areas[nextIdx];
    });
    schedulePause();
  }, [areas, schedulePause]);

  const goNext = useCallback(() => {
    setCurrent((prev) => {
      const idx = areas.indexOf(prev);
      const nextIdx = (idx + 1) % areas.length;
      return areas[nextIdx];
    });
    schedulePause();
  }, [areas, schedulePause]);

  useEffect(() => {
    const env = (import.meta as unknown as { env: Record<string, string | undefined> }).env;
    const rawCarouselMs = env?.VITE_CATEGORY_CAROUSEL_INTERVAL_MS;
    const rawCarouselSec = env?.VITE_CATEGORY_CAROUSEL_INTERVAL_SEC;
    const intervalMs = opts?.intervalMs !== undefined
      ? opts.intervalMs
      : rawCarouselMs !== undefined
        ? Number(rawCarouselMs)
        : rawCarouselSec !== undefined
          ? Number(rawCarouselSec) * 1000
          : 15000;
    const id = setInterval(() => {
      if (Date.now() < pauseUntilRef.current) return;
      setCurrent((prev) => areas[(areas.indexOf(prev) + 1) % areas.length]);
    }, intervalMs);
    return () => clearInterval(id);
  }, [areas, opts?.intervalMs]);

  return { current, setCurrent, goPrev, goNext, schedulePause };
}