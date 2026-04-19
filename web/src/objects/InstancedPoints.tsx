import { useRef, useEffect, useMemo } from 'react';
import { useThree, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface InstancedPointsProps {
  positions: Float32Array;
  colors: Float32Array;
  sizes: Float32Array;
  count: number;
  visibilityMask?: Uint8Array;
  onHover?: (index: number | null) => void;
  onClick?: (index: number) => void;
  baseSize?: number;
}

const _dummy = new THREE.Object3D();
const _pointer = new THREE.Vector2();
const _projected = new THREE.Vector3();

export function InstancedPoints({
  positions,
  colors,
  sizes,
  count,
  visibilityMask,
  onHover,
  onClick,
  baseSize = 0.4,
}: InstancedPointsProps) {
  const groupRef = useRef<THREE.Group>(null);
  const meshRef = useRef<THREE.InstancedMesh | null>(null);
  const { camera, gl } = useThree();
  const lastHover = useRef<number | null>(null);
  const throttleRef = useRef(0);

  // Create instanced mesh imperatively with pre-allocated color buffer
  const mesh = useMemo(() => {
    const geo = new THREE.SphereGeometry(1, 6, 4);
    const mat = new THREE.MeshBasicMaterial();
    const m = new THREE.InstancedMesh(geo, mat, count);
    m.frustumCulled = false;
    // Pre-allocate instance color
    m.instanceColor = new THREE.InstancedBufferAttribute(
      new Float32Array(count * 3), 3,
    );
    meshRef.current = m;
    return m;
  }, [count]);

  // Populate matrices and colors when data changes
  useEffect(() => {
    if (!mesh || count === 0) return;
    const colorBuf = mesh.instanceColor!.array as Float32Array;

    for (let i = 0; i < count; i++) {
      const vis = visibilityMask ? visibilityMask[i] : 1;
      _dummy.position.set(positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2]);
      _dummy.scale.setScalar(vis ? sizes[i] * baseSize : 0);
      _dummy.updateMatrix();
      mesh.setMatrixAt(i, _dummy.matrix);
      colorBuf[i * 3] = colors[i * 3];
      colorBuf[i * 3 + 1] = colors[i * 3 + 1];
      colorBuf[i * 3 + 2] = colors[i * 3 + 2];
    }
    mesh.instanceMatrix.needsUpdate = true;
    mesh.instanceColor!.needsUpdate = true;
    mesh.computeBoundingSphere();
  }, [mesh, positions, colors, sizes, count, visibilityMask, baseSize]);

  // Attach to scene
  useEffect(() => {
    const g = groupRef.current;
    if (!g || !mesh) return;
    g.add(mesh);
    return () => { g.remove(mesh); };
  }, [mesh]);

  // Cheap nearest-point hover: project every Nth frame, find closest to mouse
  useFrame(() => {
    throttleRef.current++;
    if (throttleRef.current % 6 !== 0) return; // ~10fps hover check
    if (!onHover) return;

    const rect = gl.domElement.getBoundingClientRect();
    const mx = ((_pointer.x + 1) / 2) * rect.width;
    const my = ((1 - _pointer.y) / 2) * rect.height;

    let bestDist = 20 * 20; // 20px threshold
    let bestIdx: number | null = null;

    for (let i = 0; i < count; i++) {
      if (visibilityMask && !visibilityMask[i]) continue;
      _projected.set(positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2]);
      _projected.project(camera);
      const sx = ((_projected.x + 1) / 2) * rect.width;
      const sy = ((1 - _projected.y) / 2) * rect.height;
      const dx = sx - mx, dy = sy - my;
      const d2 = dx * dx + dy * dy;
      if (d2 < bestDist) {
        bestDist = d2;
        bestIdx = i;
      }
    }

    if (bestIdx !== lastHover.current) {
      lastHover.current = bestIdx;
      onHover(bestIdx);
    }
  });

  // Track mouse position without R3F events (no raycasting overhead).
  // On touch devices: first tap = preview (show hover label), second tap on same
  // index within 1500ms = commit. Prevents accidental selections on dense dot clouds.
  useEffect(() => {
    const canvas = gl.domElement;
    const lastTap = { idx: null as number | null, time: 0 };

    const onMove = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      _pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      _pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    };
    const onPointerUp = (e: PointerEvent) => {
      if (!onClick) return;
      // Compute hover index synchronously on tap/click so we don't depend on
      // the throttled useFrame loop having run between pointermove and up.
      const rect = canvas.getBoundingClientRect();
      const mx = ((_pointer.x + 1) / 2) * rect.width;
      const my = ((1 - _pointer.y) / 2) * rect.height;
      let bestDist = 28 * 28; // larger threshold for touch
      let idx: number | null = null;
      for (let i = 0; i < count; i++) {
        if (visibilityMask && !visibilityMask[i]) continue;
        _projected.set(positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2]);
        _projected.project(camera);
        const sx = ((_projected.x + 1) / 2) * rect.width;
        const sy = ((1 - _projected.y) / 2) * rect.height;
        const dx = sx - mx, dy = sy - my;
        const d2 = dx * dx + dy * dy;
        if (d2 < bestDist) { bestDist = d2; idx = i; }
      }
      if (idx === null) return;

      if (e.pointerType === 'touch') {
        const now = Date.now();
        if (lastTap.idx === idx && now - lastTap.time < 1500) {
          // Commit on second tap of same node
          lastTap.idx = null;
          lastTap.time = 0;
          onClick(idx);
        } else {
          // First tap: show preview via hover
          lastTap.idx = idx;
          lastTap.time = now;
          if (onHover) onHover(idx);
          lastHover.current = idx;
        }
      } else {
        // Mouse / pen: commit on first click
        onClick(idx);
      }
    };
    canvas.addEventListener('pointermove', onMove);
    canvas.addEventListener('pointerup', onPointerUp);
    return () => {
      canvas.removeEventListener('pointermove', onMove);
      canvas.removeEventListener('pointerup', onPointerUp);
    };
  }, [gl, onClick, onHover, count, visibilityMask, positions, camera]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (mesh) {
        mesh.geometry.dispose();
        (mesh.material as THREE.Material).dispose();
      }
    };
  }, [mesh]);

  return <group ref={groupRef} />;
}
