import { useEffect, useMemo, useCallback } from 'react';
import { OrbitControls } from '@react-three/drei';
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
      setLoading(true, 'Loading Strong\'s lexicon...');
      loadStrongsPoints()
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [strongsPoints?.loaded, loadStrongsPoints, setLoading]);

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
      s[i] = 0.5 + Math.min(usageCounts[i] / 100, 3);
    }
    return s;
  }, [strongsPoints]);

  const hoveredLabel = useMemo(() => {
    if (hoveredIndex === null || !strongsPoints) return '';
    return `Strong's #${strongsPoints.strongsIds[hoveredIndex]}`;
  }, [hoveredIndex, strongsPoints]);

  const hoveredPosition = useMemo((): [number, number, number] | null => {
    if (hoveredIndex === null || !strongsPoints) return null;
    const p = strongsPoints.positions;
    return [p[hoveredIndex * 3], p[hoveredIndex * 3 + 1], p[hoveredIndex * 3 + 2]];
  }, [hoveredIndex, strongsPoints]);

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

  if (!strongsPoints?.loaded) return null;

  return (
    <>
      <OrbitControls enableDamping dampingFactor={0.05} />
      <ambientLight intensity={0.6} />
      <pointLight position={[50, 50, 50]} intensity={0.8} />
      <InstancedPoints
        positions={strongsPoints.positions}
        colors={colors}
        sizes={sizes}
        count={strongsPoints.count}
        visibilityMask={visibilityMask}
        onHover={setHoveredIndex}
        onClick={handleClick}
        baseSize={0.5}
      />
      <HoverLabel position={hoveredPosition} text={hoveredLabel} />
    </>
  );
}
