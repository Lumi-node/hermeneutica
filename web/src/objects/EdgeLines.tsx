import { useMemo } from 'react';
import * as THREE from 'three';
import type { CrossRefArc } from '@/types/crossref';
import { createArcCurve } from '@/lib/geometry';

interface EdgeLinesProps {
  arcs: CrossRefArc[];
  color?: string;
  opacity?: number;
  segments?: number;
}

export function EdgeLines({
  arcs,
  color = '#4A90D9',
  opacity = 0.5,
  segments = 16,
}: EdgeLinesProps) {
  const linePositions = useMemo(() => {
    const points: number[] = [];
    for (const arc of arcs) {
      const start = new THREE.Vector3(arc.sourceX, arc.sourceY, arc.sourceZ);
      const end = new THREE.Vector3(arc.targetX, arc.targetY, arc.targetZ);
      const curve = createArcCurve(start, end);
      const curvePoints = curve.getPoints(segments);
      for (let i = 0; i < curvePoints.length - 1; i++) {
        points.push(
          curvePoints[i].x, curvePoints[i].y, curvePoints[i].z,
          curvePoints[i + 1].x, curvePoints[i + 1].y, curvePoints[i + 1].z,
        );
      }
    }
    return new Float32Array(points);
  }, [arcs, segments]);

  if (arcs.length === 0) return null;

  return (
    <lineSegments>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[linePositions, 3]}
        />
      </bufferGeometry>
      <lineBasicMaterial color={color} transparent opacity={opacity} />
    </lineSegments>
  );
}
