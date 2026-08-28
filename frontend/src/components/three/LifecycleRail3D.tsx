import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Html, Line, OrbitControls } from '@react-three/drei';
import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import type { Asset } from '../../types/api';

function CameraDolly({ selected }: { selected: number }) {
  const { camera } = useThree();
  // oxlint-disable-next-line react/immutability -- R3F camera transforms belong in the frame loop.
  useFrame(() => { camera.position.x = THREE.MathUtils.lerp(camera.position.x, (selected - 4.5) * 1.25, .055); camera.lookAt(camera.position.x, 0, 0); });
  return null;
}
function Rail({ asset, selected, setSelected, shockwaveKey }: { asset: Asset; selected: number; setSelected: (index: number) => void; shockwaveKey: number }) {
  const current = asset.timeline.findIndex((stage) => stage.stage === asset.currentStage);
  const ripple = useRef<THREE.Mesh>(null);
  const started = useRef(0);
  useEffect(() => { started.current = performance.now(); }, [shockwaveKey]);
  useFrame(() => { if (!ripple.current) return; const progress = Math.min(1, (performance.now() - started.current) / 1100); ripple.current.scale.setScalar(.5 + progress * 7); const material = ripple.current.material as THREE.MeshBasicMaterial; material.opacity = (1 - progress) * .65; });
  const points = useMemo(() => asset.timeline.map((_, index) => [(index - 4.5) * 1.25, Math.sin(index * .8) * .22, Math.cos(index * .7) * .28] as [number,number,number]), [asset.timeline]);
  return <group><Line points={points} color="#3d3a39" lineWidth={1} />{asset.timeline.map((stage, index) => { const past = index < current; const active = index === current; return <group key={stage.stage} position={points[index]}><mesh onClick={() => setSelected(index)}><sphereGeometry args={[active ? .18 : .12, 18, 18]} /><meshBasicMaterial color={active ? '#ff5a1f' : '#eeeeee'} transparent opacity={active ? 1 : past ? .55 : .18} wireframe={!active} /></mesh>{index === selected && <Html center distanceFactor={8}><span className="mono whitespace-nowrap bg-[#101010] px-2 py-1 text-[#eeeeee]">{stage.label}</span></Html>}{active && <mesh ref={ripple} rotation-x={Math.PI / 2}><ringGeometry args={[.16,.2,32]} /><meshBasicMaterial color="#ff5a1f" transparent opacity={0} side={THREE.DoubleSide} /></mesh>}</group>; })}</group>;
}

// Real data drivers: lifecycle stage index, reconciled stage state, and event shockwave key.
export default function LifecycleRail3D({ asset, shockwaveKey = 0 }: { asset: Asset; shockwaveKey?: number }) {
  const initial = Math.max(0, asset.timeline.findIndex((stage) => stage.stage === asset.currentStage));
  const [selected, setSelected] = useState(initial); const stage = asset.timeline[selected];
  return <div className="grid gap-5 lg:grid-cols-[1fr_280px]"><div className="h-[310px] overflow-hidden rounded-[10px] border border-[var(--color-ash-stroke)] bg-[#0d0d0d]"><Canvas dpr={[1,1.5]} camera={{ position: [(initial - 4.5) * 1.25, 2.5, 6], fov: 42 }}><Rail asset={asset} selected={selected} setSelected={setSelected} shockwaveKey={shockwaveKey} /><CameraDolly selected={selected} /><OrbitControls enablePan={false} minDistance={4.5} maxDistance={8} minPolarAngle={1.05} maxPolarAngle={1.75} minAzimuthAngle={-.65} maxAzimuthAngle={.65} /></Canvas></div><aside className="panel p-5"><div className="mono text-[var(--color-signal-orange)]">Stage / {String(selected + 1).padStart(2,'0')}</div><h3 className="mt-5 text-2xl tracking-[-.025em]">{stage.label}</h3><dl className="mt-7 grid gap-4 text-sm"><div><dt className="mono text-[var(--color-warm-granite)]">Status</dt><dd className="mt-2 uppercase">{stage.status}</dd></div><div><dt className="mono text-[var(--color-warm-granite)]">Reconciled state</dt><dd className="mt-2">{selected === initial ? asset.physicalState : stage.status === 'completed' ? 'Verified milestone' : 'Awaiting evidence'}</dd></div><div><dt className="mono text-[var(--color-warm-granite)]">Evidence confidence</dt><dd className="mt-2">{selected <= initial ? `${asset.confidence}%` : 'INSUFFICIENT DATA'}</dd></div></dl></aside></div>;
}
