import { Canvas, useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import { useRef } from 'react';
import * as THREE from 'three';

const nodes: [number, number, number][] = [[0,0,0],[-1.5,.8,.2],[1.4,.9,-.2],[-1.3,-.9,-.3],[1.5,-.75,.3],[0,1.4,-.4]];
function Graph({ onAssetClick }: { onAssetClick: () => void }) {
  const group = useRef<THREE.Group>(null);
  useFrame((_, delta) => { if (group.current) group.current.rotation.y += delta * .12; });
  return <group ref={group}>{nodes.slice(1).map((node, index) => <Line key={index} points={[[0,0,0], node]} color="#8a8380" lineWidth={.5} transparent opacity={.55} />)}{nodes.map((node, index) => <mesh key={index} position={node} onClick={index === 0 ? onAssetClick : undefined}><sphereGeometry args={[index === 0 ? .22 : .13, 14, 14]} /><meshBasicMaterial color={index === 0 ? '#ff5a1f' : '#eeeeee'} wireframe={index !== 0} /></mesh>)}</group>;
}

// Real data drivers: asset nodes, source nodes and their evidence connections.
export default function AssetNetworkGraph({ onAssetClick }: { onAssetClick: () => void }) {
  return <div className="absolute inset-0 bg-[#0d0d0d]" role="img" aria-label="Asset and source connection graph"><Canvas dpr={[1, 1.5]} camera={{ position: [0, 0, 5], fov: 45 }}><Graph onAssetClick={onAssetClick} /></Canvas></div>;
}
