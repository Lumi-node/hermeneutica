import { Html } from '@react-three/drei';

interface HoverLabelProps {
  position: [number, number, number] | null;
  text: string;
}

export function HoverLabel({ position, text }: HoverLabelProps) {
  if (!position || !text) return null;

  return (
    <Html position={position} center style={{ pointerEvents: 'none' }}>
      <div className="bg-bg-panel/90 text-white text-xs px-2 py-1 rounded border border-white/10 whitespace-nowrap backdrop-blur-sm">
        {text}
      </div>
    </Html>
  );
}
