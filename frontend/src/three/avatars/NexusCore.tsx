import { useFrame } from "@react-three/fiber";
import { useEffect, useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { isSpeaking } from "../../lib/tts";
import { useAgentStore } from "../../stores/agentStore";
import { STATUS_VISUALS, type AgentStatus } from "../statusVisuals";

/**
 * NexusCore — núcleo de IA futurista, 100% procedural (Three.js), que "actúa" según el
 * estado del agente:
 *   idle       → gira lento y respira
 *   listening  → se activa hacia el usuario
 *   thinking   → el icosaedro interno acelera su giro
 *   searching  → las partículas CONVERGEN hacia el núcleo (investigando datos)
 *   answering  → el anillo ecualizador se enciende y pulsa; las partículas se expanden
 *   no_info    → se apaga/atenúa
 *   error      → tiembla en rojo
 * Todo lerp-ea su color hacia STATUS_VISUALS[status].color en tiempo real.
 *
 * Rendimiento: geometrías/objetos memorizados, instancedMesh para el ecualizador, y
 * cero allocations dentro de useFrame (colores precalculados por estado).
 */
const TICKS = 64;
const PARTICLES = 460;

export default function NexusCore() {
  const root = useRef<THREE.Group>(null!);
  const core = useRef<THREE.Mesh>(null!);
  const glow = useRef<THREE.Mesh>(null!);
  const ico = useRef<THREE.Mesh>(null!);
  const shell = useRef<THREE.Mesh>(null!);
  const rings = useRef<THREE.Group>(null!);
  const ticksGrp = useRef<THREE.Group>(null!);
  const ticks = useRef<THREE.InstancedMesh>(null!);
  const points = useRef<THREE.Points>(null!);

  const color = useRef(new THREE.Color("#22d3ee"));
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const radMul = useRef(1);

  const statusColors = useMemo(() => {
    const rec = {} as Record<AgentStatus, THREE.Color>;
    for (const k of Object.keys(STATUS_VISUALS) as AgentStatus[]) {
      rec[k] = new THREE.Color(STATUS_VISUALS[k].color);
    }
    return rec;
  }, []);

  // Partículas: dirección unitaria fija + radio base (se anima el radio para converger/expandir).
  const { pGeo, dirs, radii } = useMemo(() => {
    const pos = new Float32Array(PARTICLES * 3);
    const d = new Float32Array(PARTICLES * 3);
    const r = new Float32Array(PARTICLES);
    for (let i = 0; i < PARTICLES; i++) {
      const u = Math.random() * 2 - 1;
      const a = Math.random() * Math.PI * 2;
      const sr = Math.sqrt(1 - u * u);
      const dx = sr * Math.cos(a);
      const dy = u;
      const dz = sr * Math.sin(a);
      d[i * 3] = dx;
      d[i * 3 + 1] = dy;
      d[i * 3 + 2] = dz;
      const rad = 2.0 + Math.random() * 1.7;
      r[i] = rad;
      pos[i * 3] = dx * rad;
      pos[i * 3 + 1] = dy * rad;
      pos[i * 3 + 2] = dz * rad;
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    return { pGeo: g, dirs: d, radii: r };
  }, []);

  // La geometría se pasa por prop (no como hijo JSX), así que R3F no la libera al desmontar.
  // Al cambiar de avatar se desmonta este componente: liberamos el BufferGeometry (CPU + VBO GPU).
  useEffect(() => () => pGeo.dispose(), [pGeo]);

  useLayoutEffect(() => {
    for (let i = 0; i < TICKS; i++) {
      const a = (i / TICKS) * Math.PI * 2;
      dummy.position.set(Math.cos(a) * 2.55, 0, Math.sin(a) * 2.55);
      dummy.rotation.set(0, -a, 0);
      dummy.scale.set(1, 1, 1);
      dummy.updateMatrix();
      ticks.current.setMatrixAt(i, dummy.matrix);
    }
    ticks.current.instanceMatrix.needsUpdate = true;
  }, [dummy]);

  useFrame((state, dt) => {
    const { status, talking } = useAgentStore.getState();
    const v = STATUS_VISUALS[status];
    const active = talking || isSpeaking();
    const t = state.clock.elapsedTime;

    color.current.lerp(statusColors[status], 0.06);
    const c = color.current;

    // Rotaciones (velocidad según el estado).
    const spd = v.speed;
    ico.current.rotation.y += dt * (0.3 + spd * 0.9);
    ico.current.rotation.x += dt * 0.12;
    shell.current.rotation.y -= dt * (0.05 + spd * 0.12);
    shell.current.rotation.z += dt * 0.02;
    rings.current.rotation.y += dt * (0.25 + spd * 0.7);
    rings.current.rotation.z += dt * 0.06;
    ticksGrp.current.rotation.y += dt * 0.12;
    points.current.rotation.y += dt * (0.06 + spd * 0.2);
    root.current.rotation.y = Math.sin(t * 0.2) * 0.12;

    // Pulso del núcleo (respira; late al hablar).
    const p = 0.9 + Math.sin(t * (active ? 8 : 2.4)) * (active ? 0.2 : 0.06) * (0.6 + v.pulse);
    core.current.scale.setScalar(p);
    glow.current.scale.setScalar(p * 1.9);

    // Color de todos los materiales.
    (core.current.material as THREE.MeshBasicMaterial).color.copy(c);
    (glow.current.material as THREE.MeshBasicMaterial).color.copy(c);
    (ico.current.material as THREE.MeshBasicMaterial).color.copy(c);
    (shell.current.material as THREE.MeshBasicMaterial).color.copy(c);
    (points.current.material as THREE.PointsMaterial).color.copy(c);
    (ticks.current.material as THREE.MeshBasicMaterial).color.copy(c);
    for (const m of rings.current.children) {
      ((m as THREE.Mesh).material as THREE.MeshBasicMaterial).color.lerp(c, 0.1);
    }

    // Partículas: convergen (searching) o se expanden (answering).
    const target =
      status === "searching" ? 0.5 : status === "thinking" ? 0.8 : active ? 1.28 : 1.0;
    radMul.current = THREE.MathUtils.lerp(radMul.current, target, 0.05);
    const pos = pGeo.attributes.position as THREE.BufferAttribute;
    for (let i = 0; i < PARTICLES; i++) {
      const r = radii[i] * radMul.current + Math.sin(t * 2 + i) * 0.05;
      pos.setXYZ(i, dirs[i * 3] * r, dirs[i * 3 + 1] * r, dirs[i * 3 + 2] * r);
    }
    pos.needsUpdate = true;

    // Anillo ecualizador: se enciende al responder.
    const tm = ticks.current.material as THREE.MeshBasicMaterial;
    if (active) {
      for (let i = 0; i < TICKS; i++) {
        const a = (i / TICKS) * Math.PI * 2;
        const h = 0.35 + Math.abs(Math.sin(t * 6 + i * 0.5)) * (0.7 + v.ring);
        dummy.position.set(Math.cos(a) * 2.55, 0, Math.sin(a) * 2.55);
        dummy.rotation.set(0, -a, 0);
        dummy.scale.set(1, h, 1);
        dummy.updateMatrix();
        ticks.current.setMatrixAt(i, dummy.matrix);
      }
      ticks.current.instanceMatrix.needsUpdate = true;
      tm.opacity = THREE.MathUtils.lerp(tm.opacity, 0.9, 0.2);
    } else {
      tm.opacity = THREE.MathUtils.lerp(tm.opacity, 0.12 + v.ring * 0.3, 0.05);
    }
  });

  return (
    <group ref={root} position={[0, 0.9, 0]}>
      {/* halo aditivo del núcleo */}
      <mesh ref={glow}>
        <sphereGeometry args={[0.55, 16, 16]} />
        <meshBasicMaterial
          color="#22d3ee"
          transparent
          opacity={0.14}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>
      {/* núcleo incandescente */}
      <mesh ref={core}>
        <sphereGeometry args={[0.5, 32, 32]} />
        <meshBasicMaterial color="#a5f3fc" toneMapped={false} />
      </mesh>
      {/* icosaedro interno wireframe */}
      <mesh ref={ico}>
        <icosahedronGeometry args={[1.15, 1]} />
        <meshBasicMaterial color="#22d3ee" wireframe transparent opacity={0.6} />
      </mesh>
      {/* cascarón geodésico externo */}
      <mesh ref={shell}>
        <icosahedronGeometry args={[2.1, 2]} />
        <meshBasicMaterial color="#22d3ee" wireframe transparent opacity={0.12} />
      </mesh>
      {/* anillos orbitales */}
      <group ref={rings} rotation={[1.2, 0, 0]}>
        <mesh>
          <torusGeometry args={[1.7, 0.012, 8, 120]} />
          <meshBasicMaterial color="#22d3ee" transparent opacity={0.6} />
        </mesh>
        <mesh rotation={[0.9, 0.4, 0]}>
          <torusGeometry args={[2.0, 0.009, 8, 120]} />
          <meshBasicMaterial color="#67e8f9" transparent opacity={0.4} />
        </mesh>
        <mesh rotation={[-0.6, 1.1, 0]}>
          <torusGeometry args={[2.3, 0.006, 8, 120]} />
          <meshBasicMaterial color="#e879f9" transparent opacity={0.3} />
        </mesh>
      </group>
      {/* anillo ecualizador (se enciende al responder) */}
      <group ref={ticksGrp}>
        <instancedMesh ref={ticks} args={[undefined, undefined, TICKS]} frustumCulled={false}>
          <boxGeometry args={[0.03, 0.4, 0.03]} />
          <meshBasicMaterial color="#22d3ee" transparent opacity={0.15} />
        </instancedMesh>
      </group>
      {/* partículas orbitales */}
      <points ref={points} geometry={pGeo} frustumCulled={false}>
        <pointsMaterial color="#67e8f9" size={0.05} sizeAttenuation transparent opacity={0.85} />
      </points>
    </group>
  );
}
