import { useEffect, useMemo, useCallback } from 'react';
import { OrbitControls, Text } from '@react-three/drei';
import { InstancedPoints } from '@/objects/InstancedPoints';
import { HoverLabel } from '@/objects/HoverLabel';
import { useSceneStore } from '@/stores/sceneStore';
import { useFilterStore } from '@/stores/filterStore';
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { LANGUAGE_COLORS } from '@/lib/colors';

export function WordConstellation() {
  const { loadStrongsPoints, strongsPoints } = useDataStore();
  const { hoveredIndex, setHoveredIndex, selectNode } = useSceneStore();
  const { testamentFilter } = useFilterStore();
  const { setLoading } = useUIStore();

  useEffect(() => {
    if (!strongsPoints?.loaded) {
      setLoading(true, 'Loading 14,298 Strong\'s lexicon entries...');
      loadStrongsPoints()
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [strongsPoints?.loaded, loadStrongsPoints, setLoading]);

  // Scale and center coordinates (same approach as Galaxy)
  const scaledPositions = useMemo(() => {
    if (!strongsPoints) return new Float32Array(0);
    const SCALE = 8;
    const p = strongsPoints.positions;
    const n = strongsPoints.count;
    const scaled = new Float32Array(p.length);
    let cx = 0, cy = 0, cz = 0;
    for (let i = 0; i < n; i++) {
      cx += p[i * 3]; cy += p[i * 3 + 1]; cz += p[i * 3 + 2];
    }
    cx /= n; cy /= n; cz /= n;
    for (let i = 0; i < n; i++) {
      scaled[i * 3] = (p[i * 3] - cx) * SCALE;
      scaled[i * 3 + 1] = (p[i * 3 + 1] - cy) * SCALE;
      scaled[i * 3 + 2] = (p[i * 3 + 2] - cz) * SCALE;
    }
    return scaled;
  }, [strongsPoints]);

  const colors = useMemo(() => {
    if (!strongsPoints) return new Float32Array(0);
    const { languages, count } = strongsPoints;
    const c = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const lang = languages[i] === 0 ? 'heb' : 'grc';
      const rgb = LANGUAGE_COLORS[lang];
      c[i * 3] = rgb[0];
      c[i * 3 + 1] = rgb[1];
      c[i * 3 + 2] = rgb[2];
    }
    return c;
  }, [strongsPoints]);

  const sizes = useMemo(() => {
    if (!strongsPoints) return new Float32Array(0);
    const { usageCounts, count } = strongsPoints;
    const s = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      s[i] = 0.5 + Math.min(usageCounts[i] / 50, 4);
    }
    return s;
  }, [strongsPoints]);

  const hoveredLabel = useMemo(() => {
    if (hoveredIndex === null || !strongsPoints) return '';
    return `Strong's #${strongsPoints.strongsIds[hoveredIndex]}`;
  }, [hoveredIndex, strongsPoints]);

  const hoveredPosition = useMemo((): [number, number, number] | null => {
    if (hoveredIndex === null || !scaledPositions.length) return null;
    return [scaledPositions[hoveredIndex * 3], scaledPositions[hoveredIndex * 3 + 1], scaledPositions[hoveredIndex * 3 + 2]];
  }, [hoveredIndex, scaledPositions]);

  const handleClick = useCallback(
    (index: number) => {
      if (!strongsPoints) return;
      selectNode('strongs', strongsPoints.strongsIds[index]);
    },
    [strongsPoints, selectNode],
  );

  // Testament filter: Hebrew (0) = OT, Greek (1) = NT
  const visibilityMask = useMemo(() => {
    if (!strongsPoints) return new Uint8Array(0);
    const { languages, count } = strongsPoints;
    const mask = new Uint8Array(count);
    for (let i = 0; i < count; i++) {
      if (testamentFilter === 'all') { mask[i] = 1; continue; }
      const isHebrew = languages[i] === 0;
      mask[i] = (testamentFilter === 'OT' && isHebrew) || (testamentFilter === 'NT' && !isHebrew) ? 1 : 0;
    }
    return mask;
  }, [strongsPoints, testamentFilter]);

  // Compute centroids for Hebrew and Greek clusters
  const clusterLabels = useMemo(() => {
    if (!strongsPoints || !scaledPositions.length) return { heb: [0, 0, 0] as [number, number, number], grc: [0, 0, 0] as [number, number, number] };
    const { languages, count } = strongsPoints;
    let hx = 0, hy = 0, hz = 0, hc = 0;
    let gx = 0, gy = 0, gz = 0, gc = 0;
    for (let i = 0; i < count; i++) {
      const x = scaledPositions[i * 3], y = scaledPositions[i * 3 + 1], z = scaledPositions[i * 3 + 2];
      if (languages[i] === 0) { hx += x; hy += y; hz += z; hc++; }
      else { gx += x; gy += y; gz += z; gc++; }
    }
    return {
      heb: [hc ? hx / hc : 0, hc ? hy / hc + 12 : 0, hc ? hz / hc : 0] as [number, number, number],
      grc: [gc ? gx / gc : 0, gc ? gy / gc + 12 : 0, gc ? gz / gc : 0] as [number, number, number],
    };
  }, [strongsPoints, scaledPositions]);

  if (!strongsPoints?.loaded) return null;

  return (
    <>
      <OrbitControls enableDamping dampingFactor={0.05} />
      <ambientLight intensity={0.6} />
      <pointLight position={[50, 50, 50]} intensity={0.8} />
      <InstancedPoints
        positions={scaledPositions}
        colors={colors}
        sizes={sizes}
        count={strongsPoints.count}
        visibilityMask={visibilityMask}
        onHover={setHoveredIndex}
        onClick={handleClick}
        baseSize={0.15}
      />

      {/* Floating cluster labels */}
      <Text
        position={clusterLabels.heb}
        fontSize={3}
        color="#D4A574"
        anchorX="center"
        anchorY="bottom"
        fillOpacity={0.25}
        font={undefined}
      >
        Hebrew
      </Text>
      <Text
        position={[clusterLabels.heb[0], clusterLabels.heb[1] - 3, clusterLabels.heb[2]]}
        fontSize={1.2}
        color="#D4A574"
        anchorX="center"
        anchorY="bottom"
        fillOpacity={0.15}
        font={undefined}
      >
        8,674 Old Testament words
      </Text>

      <Text
        position={clusterLabels.grc}
        fontSize={3}
        color="#7EB8DA"
        anchorX="center"
        anchorY="bottom"
        fillOpacity={0.25}
        font={undefined}
      >
        Greek
      </Text>
      <Text
        position={[clusterLabels.grc[0], clusterLabels.grc[1] - 3, clusterLabels.grc[2]]}
        fontSize={1.2}
        color="#7EB8DA"
        anchorX="center"
        anchorY="bottom"
        fillOpacity={0.15}
        font={undefined}
      >
        5,624 New Testament words
      </Text>

      <HoverLabel position={hoveredPosition} text={hoveredLabel} />
    </>
  );
}
