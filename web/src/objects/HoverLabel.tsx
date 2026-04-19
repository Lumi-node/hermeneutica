import { useEffect, useState } from 'react';
import { Html } from '@react-three/drei';

interface HoverLabelProps {
  position: [number, number, number] | null;
  text: string;
}

// Detect coarse pointer (touch-primary) to show tap-again hint.
function useIsCoarsePointer(): boolean {
  const [coarse, setCoarse] = useState(false);
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mq = window.matchMedia('(pointer: coarse)');
    setCoarse(mq.matches);
    const onChange = (e: MediaQueryListEvent) => setCoarse(e.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);
  return coarse;
}

export function HoverLabel({ position, text }: HoverLabelProps) {
  const isCoarse = useIsCoarsePointer();
  if (!position || !text) return null;

  return (
    <Html position={position} center style={{ pointerEvents: 'none' }}>
      <div className="bg-bg-panel/90 text-white text-xs px-2 py-1 rounded border border-white/10 whitespace-nowrap backdrop-blur-sm">
        {text}
        {isCoarse && (
          <span className="ml-1.5 text-[9px] text-accent-gold">· tap again to open</span>
        )}
      </div>
    </Html>
  );
}
