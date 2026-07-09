import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { isSpeaking } from "../../lib/tts";
import { useAgentStore } from "../../stores/agentStore";
import { STATUS_VISUALS, type AgentStatus } from "../statusVisuals";

/** Orbe de plasma: núcleo incandescente + cascarón geodésico + halo aditivo + partículas que
 *  convergen al buscar y se expanden al responder. Estética más suave/orgánica que Nexus. */
const PARTS = 320;

export default function Orbe() {
  const core = useRef<THREE.Mesh>(null!);
  const glow = useRef<THREE.Mesh>(null!);
  const shell = useRef<THREE.Mesh>(null!);
  const pts = useRef<THREE.Points>(null!);
  const color = useRef(new THREE.Color("#22d3ee"));
  const radMul = useRef(1);

  const statusColors = useMemo(() => {
    const rec = {} as Record<AgentStatus, THREE.Color>;
    for (const k of Object.keys(STATUS_VISUALS) as AgentStatus[]) {
      rec[k] = new THREE.Color(STATUS_VISUALS[k].color);
    }
    return rec;
  }, []);

  const { pGeo, dirs, radii } = useMemo(() => {
    const pos = new Float32Array(PARTS * 3);
    const d = new Float32Array(PARTS * 3);
    const r = new Float32Array(PARTS);
    for (let i = 0; i < PARTS; i++) {
      const u = Math.random() * 2 - 1;
      const a = Math.random() * Math.PI * 2;
      const sr = Math.sqrt(1 - u * u);
      const dx = sr * Math.cos(a);
      const dy = u;
      const dz = sr * Math.sin(a);
      d[i * 3] = dx;
      d[i * 3 + 1] = dy;
      d[i * 3 + 2] = dz;
      const rad = 1.7 + Math.random() * 1.2;
      r[i] = rad;
      pos[i * 3] = dx * rad;
      pos[i * 3 + 1] = dy * rad;
      pos[i * 3 + 2] = dz * rad;
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    return { pGeo: g, dirs: d, radii: r };
  }, []);

  // La geometría se pasa por prop (no como hijo JSX): R3F no la libera al desmontar. Al cambiar
  // de avatar se desmonta este componente, así que liberamos el BufferGeometry (CPU + VBO GPU).
  useEffect(() => () => pGeo.dispose(), [pGeo]);

  useFrame((state, dt) => {
    const { status, talking } = useAgentStore.getState();
    const v = STATUS_VISUALS[status];
    const active = talking || isSpeaking();
    const t = state.clock.elapsedTime;

    color.current.lerp(statusColors[status], 0.06);
    const c = color.current;

    const p = 1 + Math.sin(t * (active ? 7 : 2.2)) * (active ? 0.18 : 0.05) * (0.6 + v.pulse);
    core.current.scale.setScalar(p);
    glow.current.scale.setScalar(p * 1.7);
    shell.current.rotation.y += dt * (0.1 + v.speed * 0.3);
    shell.current.rotation.x += dt * 0.05;
    pts.current.rotation.y += dt * (0.05 + v.speed * 0.2);

    (core.current.material as THREE.MeshBasicMaterial).color.copy(c);
    (glow.current.material as THREE.MeshBasicMaterial).color.copy(c);
    (shell.current.material as THREE.MeshBasicMaterial).color.copy(c);
    (pts.current.material as THREE.PointsMaterial).color.copy(c);

    const target = status === "searching" ? 0.55 : active ? 1.25 : 1.0;
    radMul.current = THREE.MathUtils.lerp(radMul.current, target, 0.05);
    const pos = pGeo.attributes.position as THREE.BufferAttribute;
    for (let i = 0; i < PARTS; i++) {
      const rr = radii[i] * radMul.current + Math.sin(t * 2 + i) * 0.04;
      pos.setXYZ(i, dirs[i * 3] * rr, dirs[i * 3 + 1] * rr, dirs[i * 3 + 2] * rr);
    }
    pos.needsUpdate = true;
  });

  return (
    <group position={[0, 0.9, 0]}>
      <mesh ref={glow}>
        <sphereGeometry args={[0.8, 24, 24]} />
        <meshBasicMaterial
          color="#22d3ee"
          transparent
          opacity={0.13}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>
      <mesh ref={core}>
        <sphereGeometry args={[0.72, 48, 48]} />
        <meshBasicMaterial color="#a5f3fc" toneMapped={false} transparent opacity={0.92} />
      </mesh>
      <mesh ref={shell}>
        <icosahedronGeometry args={[1.55, 1]} />
        <meshBasicMaterial color="#22d3ee" wireframe transparent opacity={0.22} />
      </mesh>
      <points ref={pts} geometry={pGeo} frustumCulled={false}>
        <pointsMaterial color="#67e8f9" size={0.05} sizeAttenuation transparent opacity={0.85} />
      </points>
    </group>
  );
}
