import * as THREE from 'three';

/** Create a quadratic bezier arc between two 3D points, lifted upward */
export function createArcCurve(
  start: THREE.Vector3,
  end: THREE.Vector3,
  liftFactor = 0.3,
): THREE.QuadraticBezierCurve3 {
  const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
  const dist = start.distanceTo(end);
  // Lift the control point perpendicular to the line
  mid.y += dist * liftFactor;
  return new THREE.QuadraticBezierCurve3(start, mid, end);
}

/** Parse binary verse bulk data (28 bytes per record) */
export function parseVerseBulk(buffer: ArrayBuffer) {
  const RECORD_SIZE = 28;
  const count = buffer.byteLength / RECORD_SIZE;
  const view = new DataView(buffer);

  const verseIds = new Int32Array(count);
  const positions = new Float32Array(count * 3);
  const metadata = new Uint8Array(count * 7); // book, chapter, verseLo, verseHi, xrefLo, xrefHi, testament, genre
  const ethicsMax = new Float32Array(count);

  for (let i = 0; i < count; i++) {
    const off = i * RECORD_SIZE;
    verseIds[i] = view.getInt32(off, true);
    positions[i * 3] = view.getFloat32(off + 4, true);
    positions[i * 3 + 1] = view.getFloat32(off + 8, true);
    positions[i * 3 + 2] = view.getFloat32(off + 12, true);
    metadata[i * 7] = view.getUint8(off + 16);       // book_id
    metadata[i * 7 + 1] = view.getUint8(off + 17);   // chapter_number
    metadata[i * 7 + 2] = view.getUint8(off + 18);   // verse_number lo
    metadata[i * 7 + 3] = view.getUint8(off + 19);   // verse_number hi
    metadata[i * 7 + 4] = view.getUint8(off + 20);   // xref_count lo
    metadata[i * 7 + 5] = view.getUint8(off + 21);   // xref_count hi
    metadata[i * 7 + 6] = view.getUint8(off + 22);   // testament
    // genre_id at offset 23 stored separately:
    ethicsMax[i] = view.getFloat32(off + 24, true);
  }

  return { verseIds, positions, metadata, ethicsMax, count };
}

/** Parse binary Strong's bulk data (24 bytes per record) */
export function parseStrongsBulk(buffer: ArrayBuffer) {
  const RECORD_SIZE = 24;
  const count = buffer.byteLength / RECORD_SIZE;
  const view = new DataView(buffer);

  const strongsIds = new Int32Array(count);
  const positions = new Float32Array(count * 3);
  const languages = new Uint8Array(count);
  const posIds = new Uint8Array(count);
  const usageCounts = new Uint16Array(count);

  for (let i = 0; i < count; i++) {
    const off = i * RECORD_SIZE;
    strongsIds[i] = view.getInt32(off, true);
    positions[i * 3] = view.getFloat32(off + 4, true);
    positions[i * 3 + 1] = view.getFloat32(off + 8, true);
    positions[i * 3 + 2] = view.getFloat32(off + 12, true);
    languages[i] = view.getUint8(off + 16);
    posIds[i] = view.getUint8(off + 17);
    usageCounts[i] = view.getUint16(off + 18, true);
  }

  return { strongsIds, positions, languages, posIds, usageCounts, count };
}
