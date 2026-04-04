import { useEffect, useMemo, useRef, useState } from 'react';
import { OrbitControls } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { HoverLabel } from '@/objects/HoverLabel';
import { GraphInfoPanel } from '@/panels/GraphInfoPanel';
import { useSceneStore } from '@/stores/sceneStore';
import { useFilterStore } from '@/stores/filterStore';
import { useUIStore } from '@/stores/uiStore';
import { apiFetch } from '@/api/client';
import { EDGE_TYPE_COLORS } from '@/lib/colors';
import { Html } from '@react-three/drei';

// Match actual API response shape
interface ApiNode {
  node_type: string;
  node_id: number;
  label: string;
}
interface ApiEdge {
  source_type: string;
  source_id: number;
  target_type: string;
  target_id: number;
  edge_type: string;
  weight: number;
}
interface ApiNeighborhood {
  center_node_type: string;
  center_node_id: number;
  nodes: ApiNode[];
  edges: ApiEdge[];
}

const NODE_COLORS: Record<string, THREE.Color> = {
  verse: new THREE.Color('#4A90D9'),
  theme: new THREE.Color('#50C878'),
  strongs: new THREE.Color('#E8A838'),
};

const EDGE_TYPE_THREE_COLORS: Record<string, THREE.Color> = {};
for (const [k, v] of Object.entries(EDGE_TYPE_COLORS)) {
  EDGE_TYPE_THREE_COLORS[k] = new THREE.Color(v);
}

const _dummy = new THREE.Object3D();
const _color = new THREE.Color();
const _pointer = new THREE.Vector2();

function nodeKey(type: string, id: number) { return `${type}_${id}`; }

export function GraphExplorer() {
  const { selectedNodeId, selectedNodeType, selectNode } = useSceneStore();
  const { edgeTypeFilter, minWeight, graphHops } = useFilterStore();
  const { setLoading } = useUIStore();
  const { camera, gl } = useThree();

  const groupRef = useRef<THREE.Group>(null);
  const meshRef = useRef<THREE.InstancedMesh | null>(null);
  const edgeLinesRef = useRef<Map<string, THREE.LineSegments>>(new Map());
  const nodesRef = useRef<ApiNode[]>([]);
  const edgesRef = useRef<ApiEdge[]>([]);
  const posRef = useRef<Map<string, [number, number, number]>>(new Map());
  const frameCount = useRef(0);
  const lastHover = useRef<number | null>(null);

  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [centerType, setCenterType] = useState<string | null>(null);
  const [centerId, setCenterId] = useState<number | null>(null);
  const [nodeList, setNodeList] = useState<ApiNode[]>([]);
  const [edgeList, setEdgeList] = useState<ApiEdge[]>([]);

  // Auto-select "Love" theme on mount
  useEffect(() => {
    if (!selectedNodeType && !selectedNodeId) {
      selectNode('theme', 3077);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Load neighborhood
  useEffect(() => {
    if (!selectedNodeType || !selectedNodeId) return;
    let cancelled = false;

    setLoading(true, 'Loading graph neighborhood...');
    const params: Record<string, string> = {
      hops: String(graphHops),
      max_nodes: '200',
      min_weight: String(minWeight),
    };
    if (edgeTypeFilter.length > 0) {
      params.edge_types = edgeTypeFilter.join(',');
    }

    apiFetch<ApiNeighborhood>(`/graph/neighborhood/${selectedNodeType}/${selectedNodeId}`, params)
      .then((data) => {
        if (cancelled) return;

        const centerKey = nodeKey(data.center_node_type, data.center_node_id);
        const hasCenter = data.nodes.some(n => nodeKey(n.node_type, n.node_id) === centerKey);
        const allNodes = hasCenter ? data.nodes : [
          { node_type: data.center_node_type, node_id: data.center_node_id, label: `${data.center_node_type} #${data.center_node_id}` },
          ...data.nodes,
        ];

        const posMap = new Map<string, [number, number, number]>();
        for (const n of allNodes) {
          posMap.set(nodeKey(n.node_type, n.node_id), [
            (Math.random() - 0.5) * 30,
            (Math.random() - 0.5) * 30,
            (Math.random() - 0.5) * 30,
          ]);
        }

        nodesRef.current = allNodes;
        edgesRef.current = data.edges;
        posRef.current = posMap;
        frameCount.current = 0;

        setCenterType(data.center_node_type);
        setCenterId(data.center_node_id);
        setNodeList(allNodes);
        setEdgeList(data.edges);

        rebuildMesh(allNodes.length, data.edges);
      })
      .catch(console.error)
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [selectedNodeType, selectedNodeId, graphHops, minWeight, edgeTypeFilter, setLoading]);

  function rebuildMesh(count: number, edges: ApiEdge[]) {
    const group = groupRef.current;
    if (!group) return;

    // Remove old mesh
    if (meshRef.current) {
      group.remove(meshRef.current);
      meshRef.current.geometry.dispose();
      (meshRef.current.material as THREE.Material).dispose();
    }
    // Remove old edge lines
    for (const lines of edgeLinesRef.current.values()) {
      group.remove(lines);
      lines.geometry.dispose();
      (lines.material as THREE.Material).dispose();
    }
    edgeLinesRef.current.clear();

    if (count === 0) return;

    // Instanced mesh for nodes
    const geo = new THREE.SphereGeometry(1, 10, 8);
    const mat = new THREE.MeshBasicMaterial();
    const mesh = new THREE.InstancedMesh(geo, mat, count);
    mesh.frustumCulled = false;
    mesh.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(count * 3), 3);
    meshRef.current = mesh;
    group.add(mesh);

    // Group edges by type for colored lines
    const edgesByType = new Map<string, ApiEdge[]>();
    for (const e of edges) {
      const list = edgesByType.get(e.edge_type) || [];
      list.push(e);
      edgesByType.set(e.edge_type, list);
    }

    for (const [edgeType] of edgesByType) {
      const lineGeo = new THREE.BufferGeometry();
      const color = EDGE_TYPE_COLORS[edgeType] || '#666666';
      const lineMat = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.4 });
      const lines = new THREE.LineSegments(lineGeo, lineMat);
      edgeLinesRef.current.set(edgeType, lines);
      group.add(lines);
    }
  }

  // Force layout + render
  useFrame(() => {
    const nodes = nodesRef.current;
    const edges = edgesRef.current;
    const posMap = posRef.current;
    const mesh = meshRef.current;
    if (!mesh || nodes.length === 0) return;

    frameCount.current++;
    const settling = frameCount.current < 300;

    if (settling) {
      for (const edge of edges) {
        const k1 = nodeKey(edge.source_type, edge.source_id);
        const k2 = nodeKey(edge.target_type, edge.target_id);
        const p1 = posMap.get(k1), p2 = posMap.get(k2);
        if (!p1 || !p2) continue;
        const dx = p2[0] - p1[0], dy = p2[1] - p1[1], dz = p2[2] - p1[2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 0.01;
        const f = (dist - 8) * 0.003 * edge.weight;
        const fx = (dx / dist) * f, fy = (dy / dist) * f, fz = (dz / dist) * f;
        p1[0] += fx; p1[1] += fy; p1[2] += fz;
        p2[0] -= fx; p2[1] -= fy; p2[2] -= fz;
      }

      for (let i = 0; i < nodes.length; i++) {
        const pi = posMap.get(nodeKey(nodes[i].node_type, nodes[i].node_id));
        if (!pi) continue;
        for (let j = i + 1; j < nodes.length; j++) {
          const pj = posMap.get(nodeKey(nodes[j].node_type, nodes[j].node_id));
          if (!pj) continue;
          const dx = pj[0] - pi[0], dy = pj[1] - pi[1], dz = pj[2] - pi[2];
          const d2 = dx * dx + dy * dy + dz * dz || 0.01;
          const f = 3 / d2;
          const dist = Math.sqrt(d2);
          const fx = (dx / dist) * f, fy = (dy / dist) * f, fz = (dz / dist) * f;
          pi[0] -= fx; pi[1] -= fy; pi[2] -= fz;
          pj[0] += fx; pj[1] += fy; pj[2] += fz;
        }
      }
    }

    // Update node instances
    const colorBuf = mesh.instanceColor!.array as Float32Array;
    for (let i = 0; i < nodes.length; i++) {
      const pos = posMap.get(nodeKey(nodes[i].node_type, nodes[i].node_id));
      if (!pos) continue;
      _dummy.position.set(pos[0], pos[1], pos[2]);
      _dummy.scale.setScalar(nodes[i].node_type === 'theme' ? 1.5 : 0.8);
      _dummy.updateMatrix();
      mesh.setMatrixAt(i, _dummy.matrix);
      _color.copy(NODE_COLORS[nodes[i].node_type] ?? NODE_COLORS.verse);
      colorBuf[i * 3] = _color.r;
      colorBuf[i * 3 + 1] = _color.g;
      colorBuf[i * 3 + 2] = _color.b;
    }
    mesh.instanceMatrix.needsUpdate = true;
    mesh.instanceColor!.needsUpdate = true;

    // Update edge lines per type
    const edgesByType = new Map<string, ApiEdge[]>();
    for (const e of edges) {
      const list = edgesByType.get(e.edge_type) || [];
      list.push(e);
      edgesByType.set(e.edge_type, list);
    }

    for (const [edgeType, typeEdges] of edgesByType) {
      const lines = edgeLinesRef.current.get(edgeType);
      if (!lines) continue;
      const pts: number[] = [];
      for (const e of typeEdges) {
        const p1 = posMap.get(nodeKey(e.source_type, e.source_id));
        const p2 = posMap.get(nodeKey(e.target_type, e.target_id));
        if (!p1 || !p2) continue;
        pts.push(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2]);
      }
      lines.geometry.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    }
  });

  // Screen-space hover (same approach as InstancedPoints — no raycasting)
  useEffect(() => {
    const canvas = gl.domElement;
    const onMove = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      _pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      _pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    };
    const onClick = () => {
      const idx = lastHover.current;
      if (idx === null) return;
      const node = nodesRef.current[idx];
      if (node) {
        selectNode(node.node_type as 'verse' | 'strongs' | 'theme', node.node_id);
      }
    };
    canvas.addEventListener('pointermove', onMove);
    canvas.addEventListener('click', onClick);
    return () => {
      canvas.removeEventListener('pointermove', onMove);
      canvas.removeEventListener('click', onClick);
    };
  }, [gl, selectNode]);

  // Hover detection at ~10fps
  const _proj = useMemo(() => new THREE.Vector3(), []);
  useFrame(() => {
    if (frameCount.current % 6 !== 0) return;
    const nodes = nodesRef.current;
    const posMap = posRef.current;
    const rect = gl.domElement.getBoundingClientRect();
    const mx = ((_pointer.x + 1) / 2) * rect.width;
    const my = ((1 - _pointer.y) / 2) * rect.height;

    let bestDist = 25 * 25;
    let bestIdx: number | null = null;

    for (let i = 0; i < nodes.length; i++) {
      const pos = posMap.get(nodeKey(nodes[i].node_type, nodes[i].node_id));
      if (!pos) continue;
      _proj.set(pos[0], pos[1], pos[2]).project(camera);
      const sx = ((_proj.x + 1) / 2) * rect.width;
      const sy = ((1 - _proj.y) / 2) * rect.height;
      const d2 = (sx - mx) ** 2 + (sy - my) ** 2;
      if (d2 < bestDist) { bestDist = d2; bestIdx = i; }
    }

    if (bestIdx !== lastHover.current) {
      lastHover.current = bestIdx;
      setHoveredIdx(bestIdx);
    }
  });

  // Hovered node info
  const hoveredNode = hoveredIdx !== null ? nodesRef.current[hoveredIdx] ?? null : null;
  const hoveredEdges = useMemo(() => {
    if (!hoveredNode) return [];
    const key = nodeKey(hoveredNode.node_type, hoveredNode.node_id);
    return edgeList.filter(e =>
      nodeKey(e.source_type, e.source_id) === key ||
      nodeKey(e.target_type, e.target_id) === key
    );
  }, [hoveredNode, edgeList]);

  const hoveredLabel = hoveredNode?.label ?? '';
  const hoveredPosition = useMemo((): [number, number, number] | null => {
    if (!hoveredNode) return null;
    return posRef.current.get(nodeKey(hoveredNode.node_type, hoveredNode.node_id)) ?? null;
  }, [hoveredNode]);

  return (
    <>
      <OrbitControls enableDamping dampingFactor={0.05} />
      <ambientLight intensity={0.6} />
      <group ref={groupRef} />
      <HoverLabel position={hoveredPosition} text={hoveredLabel} />
      {/* Info panel as HTML overlay, positioned bottom-right of canvas */}
      <Html fullscreen style={{ pointerEvents: 'none' }}>
        <div className="absolute bottom-2 right-2 w-64 max-h-96 bg-bg-panel/95 backdrop-blur-sm border border-white/10 rounded-lg overflow-hidden" style={{ pointerEvents: 'auto' }}>
          <GraphInfoPanel
            nodes={nodeList}
            edges={edgeList}
            centerType={centerType}
            centerId={centerId}
            hoveredNode={hoveredNode}
            hoveredEdges={hoveredEdges}
          />
        </div>
      </Html>
    </>
  );
}
