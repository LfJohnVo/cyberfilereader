import { Canvas, useFrame } from "@react-three/fiber";
import { Suspense, useMemo, useRef } from "react";
import * as THREE from "three";
import { useAgentStore } from "../stores/agentStore";
import { useSettingsStore } from "../stores/settingsStore";
import { avatarById } from "./avatars/registry";
import { STATUS_VISUALS } from "./statusVisuals";

/** Terreno low-poly wireframe animado, con nodos brillantes en los vértices.
 *  Color reactivo al estado del agente (cambia en tiempo real). */
function Terrain() {
  const geo = useMemo(() => new THREE.PlaneGeometry(34, 20, 56, 34), []);
  const base = useMemo(() => Float32Array.from(geo.attributes.position.array as Float32Array), [geo]);
  const wire = useRef<THREE.MeshBasicMaterial>(null!);
  const dots = useRef<THREE.PointsMaterial>(null!);
  const tgt = useRef(new THREE.Color("#22d3ee"));

  useFrame((state) => {
    const t = state.clock.elapsedTime * 0.6;
    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = base[i * 3];
      const y = base[i * 3 + 1];
      const z =
        Math.sin(x * 0.4 + t) * 0.5 +
        Math.cos(y * 0.55 + t * 0.8) * 0.4 +
        Math.sin((x + y) * 0.28 - t * 0.5) * 0.35;
      pos.setZ(i, z);
    }
    pos.needsUpdate = true;

    const { status, talking } = useAgentStore.getState();
    tgt.current.set(STATUS_VISUALS[status].color);
    wire.current.color.lerp(tgt.current, 0.05);
    dots.current.color.lerp(tgt.current, 0.05);
    dots.current.size = talking ? 0.11 : 0.07;
  });

  return (
    <group rotation={[-1.28, 0, 0]} position={[0, -3.3, -1]}>
      <mesh geometry={geo} frustumCulled={false}>
        <meshBasicMaterial ref={wire} color="#22d3ee" wireframe transparent opacity={0.32} />
      </mesh>
      <points geometry={geo} frustumCulled={false}>
        <pointsMaterial
          ref={dots}
          color="#67e8f9"
          size={0.07}
          sizeAttenuation
          transparent
          opacity={0.95}
        />
      </points>
    </group>
  );
}

/** Campo de partículas de fondo con color reactivo. */
function ParticleField() {
  const grp = useRef<THREE.Points>(null!);
  const mat = useRef<THREE.PointsMaterial>(null!);
  const tgt = useRef(new THREE.Color("#67e8f9"));
  const geo = useMemo(() => {
    const n = 360;
    const arr = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 20;
      arr[i * 3 + 1] = (Math.random() - 0.5) * 12;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 9;
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(arr, 3));
    return g;
  }, []);

  useFrame((state, dt) => {
    grp.current.rotation.y += dt * 0.02;
    grp.current.position.y = Math.sin(state.clock.elapsedTime * 0.2) * 0.3;
    const { status, talking } = useAgentStore.getState();
    tgt.current.set(STATUS_VISUALS[status].color);
    mat.current.color.lerp(tgt.current, 0.04);
    mat.current.opacity = THREE.MathUtils.lerp(mat.current.opacity, talking ? 0.95 : 0.7, 0.05);
  });

  return (
    <points ref={grp} geometry={geo} frustumCulled={false}>
      <pointsMaterial ref={mat} color="#67e8f9" size={0.05} sizeAttenuation transparent opacity={0.7} />
    </points>
  );
}

/** Detección de WebGL: si el navegador/GPU no lo soporta, evitamos montar el Canvas
 *  (que lanzaría) y devolvemos un fondo estático. La app sigue 100% usable. */
function webglAvailable(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext("webgl") || canvas.getContext("experimental-webgl"))
    );
  } catch {
    return false;
  }
}

export default function Scene() {
  const avatarId = useSettingsStore((s) => s.avatarId);
  const desc = avatarById(avatarId);
  const Avatar = desc.component;

  // Avatar 2D (sin Three.js): se monta sin <Canvas>.
  if (desc.kind === "dom") {
    return (
      <Suspense fallback={null}>
        <Avatar />
      </Suspense>
    );
  }

  // Avatar 3D: dentro del <Canvas> compartido (con el fondo de terreno + partículas).
  if (!webglAvailable()) return null; // el degradado de fondo (CSS body) hace de respaldo

  return (
    <Canvas
      dpr={[1, 1.75]}
      camera={{ position: [0, 0.5, 7.5], fov: 46 }}
      gl={{ antialias: true, powerPreference: "high-performance" }}
    >
      <color attach="background" args={["#050813"]} />
      <fog attach="fog" args={["#050813", 9, 24]} />
      <ambientLight intensity={0.5} />
      <Suspense fallback={null}>
        <Avatar />
      </Suspense>
      <ParticleField />
      <Terrain />
    </Canvas>
  );
}
