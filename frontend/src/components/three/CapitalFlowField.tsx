import { Canvas, useFrame } from '@react-three/fiber';
import { useMemo, useRef } from 'react';
import * as THREE from 'three';

function FlowParticles() {
  const points = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const values = new Float32Array(150 * 3);
    for (let i = 0; i < 150; i += 1) {
      const t = i / 149;
      values[i * 3] = -6 + t * 12;
      values[i * 3 + 1] = Math.sin(t * Math.PI * 3) * 1.5 + ((i * 47) % 31) / 31 - .5;
      values[i * 3 + 2] = -2 + ((i * 29) % 47) / 10;
    }
    return values;
  }, []);
  useFrame(({ clock, pointer }) => {
    if (!points.current) return;
    points.current.rotation.y = clock.elapsedTime * .012 + pointer.x * .018;
    points.current.rotation.x = pointer.y * .012;
    points.current.position.x = (clock.elapsedTime * .045) % .5;
  });
  return <points ref={points}><bufferGeometry><bufferAttribute attach="attributes-position" args={[positions, 3]} /></bufferGeometry><pointsMaterial color="#f5f5f5" size={.025} transparent opacity={.24} sizeAttenuation /></points>;
}

// Real data driver: capital-flow edges can replace the deterministic curve positions.
export default function CapitalFlowField() {
  return <div className="pointer-events-none absolute inset-0" aria-hidden="true"><Canvas dpr={[1, 1.5]} camera={{ position: [0, 0, 7], fov: 48 }} gl={{ alpha: true, antialias: false }}><FlowParticles /></Canvas></div>;
}
