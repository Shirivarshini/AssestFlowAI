import { Canvas } from '@react-three/fiber';
import { Line, OrbitControls } from '@react-three/drei';

const values = [18, 21, 19, 25, 34, 29, 62, 41, 55];
// Real data driver: chronological 0-100 risk observations from risk assessments.
export default function RiskRibbon() {
  const points = values.map((value, index) => [index * .55 - 2.2, value / 28 - 1.4, Math.sin(index) * .22] as [number, number, number]);
  return <div className="absolute inset-0 bg-[#0d0d0d]" role="img" aria-label="Depth view of risk history"><Canvas dpr={[1, 1.5]} camera={{ position: [0, .2, 5.4], fov: 42 }}><Line points={points} color="#ff5a1f" lineWidth={2} />{points.filter((_, index) => index === 6 || index === 8).map((point, index) => <mesh key={index} position={point}><cylinderGeometry args={[.08,.08,.22,12]} /><meshBasicMaterial color="#ff5a1f" /></mesh>)}<OrbitControls enablePan={false} enableZoom={false} minPolarAngle={1.25} maxPolarAngle={1.9} minAzimuthAngle={-.25} maxAzimuthAngle={.25} /></Canvas></div>;
}
