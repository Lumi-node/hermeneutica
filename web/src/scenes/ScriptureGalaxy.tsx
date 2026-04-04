import { useEffect, useMemo, useCallback } from 'react';
import { OrbitControls } from '@react-three/drei';
import { InstancedPoints } from '@/objects/InstancedPoints';
import { EdgeLines } from '@/objects/EdgeLines';
import { GlowingArcs } from '@/objects/GlowingArcs';
import { HoverLabel } from '@/objects/HoverLabel';
import { useSceneStore } from '@/stores/sceneStore';
import { useFilterStore } from '@/stores/filterStore';
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { bookColor, testamentColor, GENRE_COLORS } from '@/lib/colors';
import { BOOK_BY_ID } from '@/lib/constants';
import { useCrossRefArcs } from '@/hooks/useCrossRefArcs';

export function ScriptureGalaxy() {
  const { loadVersePoints, versePoints } = useDataStore();
  const { colorBy, sizeBy, hoveredIndex, setHoveredIndex, selectNode, selectedNodeId, overlayArcs, overlayColor } = useSceneStore();
  const { testamentFilter, bookFilter, genreFilter } = useFilterStore();
  const { setLoading } = useUIStore();

  const arcs = useCrossRefArcs(selectedNodeId);

  useEffect(() => {
    if (!versePoints?.loaded) {
      setLoading(true, 'Loading 31,102 verse embeddings...');
      loadVersePoints()
        .catch((err) => console.error('Failed to load verse points:', err))
        .finally(() => setLoading(false));
    }
  }, [versePoints?.loaded, loadVersePoints, setLoading]);

  // Compute colors from the colorBy mode
  const colors = useMemo(() => {
    if (!versePoints) return new Float32Array(0);
    const { metadata, count } = versePoints;
    const c = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const bookId = metadata[i * 7];
      const testament = metadata[i * 7 + 6] === 0 ? 'OT' as const : 'NT' as const;
      let rgb: [number, number, number];
      switch (colorBy) {
        case 'testament':
          rgb = testamentColor(testament);
          break;
        case 'genre': {
          const book = BOOK_BY_ID.get(bookId);
          rgb = GENRE_COLORS[book?.genre ?? 'History'] ?? [0.5, 0.5, 0.5];
          break;
        }
        case 'ethics': {
          const e = versePoints.ethicsMax[i];
          rgb = [0.2 + e * 0.6, 0.3 + e * 0.4, 0.8 - e * 0.3];
          break;
        }
        case 'book':
        default:
          rgb = bookColor(bookId);
      }
      c[i * 3] = rgb[0];
      c[i * 3 + 1] = rgb[1];
      c[i * 3 + 2] = rgb[2];
    }
    return c;
  }, [versePoints, colorBy]);

  // Compute sizes
  const sizes = useMemo(() => {
    if (!versePoints) return new Float32Array(0);
    const { metadata, ethicsMax, count } = versePoints;
    const s = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      switch (sizeBy) {
        case 'crossrefs': {
          const xrefCount = metadata[i * 7 + 4] | (metadata[i * 7 + 5] << 8);
          s[i] = 0.5 + Math.min(xrefCount / 20, 3);
          break;
        }
        case 'ethics':
          s[i] = 0.5 + ethicsMax[i] * 2;
          break;
        default:
          s[i] = 1.0;
      }
    }
    return s;
  }, [versePoints, sizeBy]);

  // Compute visibility mask from filters
  const visibilityMask = useMemo(() => {
    if (!versePoints) return new Uint8Array(0);
    const { metadata, count } = versePoints;
    const mask = new Uint8Array(count);
    for (let i = 0; i < count; i++) {
      const bookId = metadata[i * 7];
      const testament = metadata[i * 7 + 6] === 0 ? 'OT' : 'NT';
      const book = BOOK_BY_ID.get(bookId);
      let visible = true;
      if (testamentFilter !== 'all' && testament !== testamentFilter) visible = false;
      if (bookFilter.length > 0 && !bookFilter.includes(bookId)) visible = false;
      if (genreFilter.length > 0 && book && !genreFilter.includes(book.genre)) visible = false;
      mask[i] = visible ? 1 : 0;
    }
    return mask;
  }, [versePoints, testamentFilter, bookFilter, genreFilter]);

  // Scale up UMAP coords — raw spans ~8 units, scale to ~80 for proper spacing
  const scaledPositions = useMemo(() => {
    if (!versePoints) return new Float32Array(0);
    const COORD_SCALE = 10;
    const p = versePoints.positions;
    const scaled = new Float32Array(p.length);
    let cx = 0, cy = 0, cz = 0;
    const n = versePoints.count;
    for (let i = 0; i < n; i++) {
      cx += p[i * 3]; cy += p[i * 3 + 1]; cz += p[i * 3 + 2];
    }
    cx /= n; cy /= n; cz /= n;
    for (let i = 0; i < n; i++) {
      scaled[i * 3] = (p[i * 3] - cx) * COORD_SCALE;
      scaled[i * 3 + 1] = (p[i * 3 + 1] - cy) * COORD_SCALE;
      scaled[i * 3 + 2] = (p[i * 3 + 2] - cz) * COORD_SCALE;
    }
    return scaled;
  }, [versePoints]);

  // Hover label
  const hoveredLabel = useMemo(() => {
    if (hoveredIndex === null || !versePoints) return '';
    const m = versePoints.metadata;
    const bookId = m[hoveredIndex * 7];
    const chapter = m[hoveredIndex * 7 + 1];
    const verseNum = m[hoveredIndex * 7 + 2] | (m[hoveredIndex * 7 + 3] << 8);
    const book = BOOK_BY_ID.get(bookId);
    return book ? `${book.abbreviation} ${chapter}:${verseNum}` : '';
  }, [hoveredIndex, versePoints]);

  const hoveredPosition = useMemo((): [number, number, number] | null => {
    if (hoveredIndex === null || !scaledPositions.length) return null;
    return [scaledPositions[hoveredIndex * 3], scaledPositions[hoveredIndex * 3 + 1], scaledPositions[hoveredIndex * 3 + 2]];
  }, [hoveredIndex, scaledPositions]);

  const handleClick = useCallback(
    (index: number) => {
      if (!versePoints) return;
      const verseId = versePoints.verseIds[index];
      selectNode('verse', verseId);
    },
    [versePoints, selectNode],
  );

  if (!versePoints?.loaded) return null;

  return (
    <>
      <OrbitControls enableDamping dampingFactor={0.05} />
      <ambientLight intensity={0.6} />
      <pointLight position={[50, 50, 50]} intensity={0.8} />
      <InstancedPoints
        positions={scaledPositions}
        colors={colors}
        sizes={sizes}
        count={versePoints.count}
        visibilityMask={visibilityMask}
        onHover={setHoveredIndex}
        onClick={handleClick}
        baseSize={0.12}
      />
      <EdgeLines arcs={arcs} />
      {overlayArcs.length > 0 && (
        <GlowingArcs arcs={overlayArcs} color={overlayColor} opacity={0.3} />
      )}
      <HoverLabel position={hoveredPosition} text={hoveredLabel} />
    </>
  );
}
