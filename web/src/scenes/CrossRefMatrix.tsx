import { useEffect } from 'react';
import { OrbitControls } from '@react-three/drei';
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { BookHeatmap } from '@/charts/BookHeatmap';

export function CrossRefMatrix() {
  const { bookMatrix, loadBookMatrix } = useDataStore();
  const { setLoading } = useUIStore();

  useEffect(() => {
    if (!bookMatrix) {
      setLoading(true, 'Loading cross-reference matrix...');
      loadBookMatrix()
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [bookMatrix, loadBookMatrix, setLoading]);

  return (
    <>
      <OrbitControls enableDamping dampingFactor={0.05} />
      <ambientLight intensity={0.5} />
      {/* The heatmap is rendered as HTML overlay */}
      {bookMatrix && <BookHeatmap matrix={bookMatrix} />}
    </>
  );
}
