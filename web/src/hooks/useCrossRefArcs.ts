import { useState, useEffect } from 'react';
import { apiFetch } from '@/api/client';
import type { CrossRefArc } from '@/types/crossref';

export function useCrossRefArcs(verseId: number | null): CrossRefArc[] {
  const [arcs, setArcs] = useState<CrossRefArc[]>([]);

  useEffect(() => {
    if (verseId === null) {
      setArcs([]);
      return;
    }
    let cancelled = false;
    apiFetch<CrossRefArc[]>(`/verses/${verseId}/crossrefs`)
      .then((data) => {
        if (!cancelled) setArcs(data);
      })
      .catch(() => {
        if (!cancelled) setArcs([]);
      });
    return () => { cancelled = true; };
  }, [verseId]);

  return arcs;
}
