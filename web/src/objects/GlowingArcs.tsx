import { useMemo, useRef, useEffect } from 'react';
import * as THREE from 'three';
import type { CrossRefArc } from '@/types/crossref';

interface GlowingArcsProps {
  arcs: CrossRefArc[];
  color: string;
  opacity?: number;
}

// Auto-select rendering mode based on arc count:
// < 1000: curved bezier arcs (pretty, 12 segments each)
// >= 1000: straight lines (fast, single segment, GPU handles it)
const CURVE_THRESHOLD = 1000;
const CURVE_SEGMENTS = 10;

export function GlowingArcs({ arcs, color, opacity = 0.35 }: GlowingArcsProps) {
  const groupRef = useRef<THREE.Group>(null);
  const linesRef = useRef<THREE.LineSegments | null>(null);

  const useStraight = arcs.length >= CURVE_THRESHOLD;

  const linePositions = useMemo(() => {
    if (arcs.length === 0) return new Float32Array(0);

    if (useStraight) {
      // Straight lines: 2 vertices per arc = very fast
      const buf = new Float32Array(arcs.length * 6);
      for (let i = 0; i < arcs.length; i++) {
        const a = arcs[i];
        buf[i * 6] = a.sourceX;
        buf[i * 6 + 1] = a.sourceY;
        buf[i * 6 + 2] = a.sourceZ;
        buf[i * 6 + 3] = a.targetX;
        buf[i * 6 + 4] = a.targetY;
        buf[i * 6 + 5] = a.targetZ;
      }
      return buf;
    }

    // Curved bezier arcs
    const points: number[] = [];
    for (const arc of arcs) {
      const sx = arc.sourceX, sy = arc.sourceY, sz = arc.sourceZ;
      const tx = arc.targetX, ty = arc.targetY, tz = arc.targetZ;
      const mx = (sx + tx) / 2, my = (sy + ty) / 2, mz = (sz + tz) / 2;
      const dist = Math.sqrt((tx - sx) ** 2 + (ty - sy) ** 2 + (tz - sz) ** 2);
      const cy = my + dist * 0.15;

      for (let i = 0; i < CURVE_SEGMENTS; i++) {
        const t0 = i / CURVE_SEGMENTS;
        const t1 = (i + 1) / CURVE_SEGMENTS;
        const a0 = (1 - t0) * (1 - t0), b0 = 2 * (1 - t0) * t0, c0 = t0 * t0;
        const a1 = (1 - t1) * (1 - t1), b1 = 2 * (1 - t1) * t1, c1 = t1 * t1;
        points.push(
          a0 * sx + b0 * mx + c0 * tx, a0 * sy + b0 * cy + c0 * ty, a0 * sz + b0 * mz + c0 * tz,
          a1 * sx + b1 * mx + c1 * tx, a1 * sy + b1 * cy + c1 * ty, a1 * sz + b1 * mz + c1 * tz,
        );
      }
    }
    return new Float32Array(points);
  }, [arcs, useStraight]);

  useEffect(() => {
    const group = groupRef.current;
    if (!group) return;

    if (linesRef.current) {
      group.remove(linesRef.current);
      linesRef.current.geometry.dispose();
      (linesRef.current.material as THREE.Material).dispose();
    }

    if (arcs.length === 0) return;

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));

    // Lower opacity for large counts so the glow accumulates naturally
    const effectiveOpacity = useStraight
      ? Math.max(0.03, opacity * (500 / arcs.length)) // Fade as count grows
      : opacity;

    const mat = new THREE.LineBasicMaterial({
      color: new THREE.Color(color),
      transparent: true,
      opacity: effectiveOpacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const lines = new THREE.LineSegments(geo, mat);
    linesRef.current = lines;
    group.add(lines);

    return () => {
      if (linesRef.current && group) {
        group.remove(linesRef.current);
        linesRef.current.geometry.dispose();
        (linesRef.current.material as THREE.Material).dispose();
        linesRef.current = null;
      }
    };
  }, [arcs, linePositions, color, opacity, useStraight]);

  return <group ref={groupRef} />;
}
