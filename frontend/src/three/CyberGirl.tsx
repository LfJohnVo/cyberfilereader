import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { isSpeaking } from "../lib/tts";
import { useAgentStore } from "../stores/agentStore";
import { STATUS_VISUALS, type AgentStatus } from "./statusVisuals";

/**
 * CyberGirl — "diosa de neón wireframe".
 * Busto femenino procedural fiel a /avatar.png: contornos de cabeza/mandíbula/cuello/
 * hombros como tubos luminosos finos (CatmullRomCurve3 + TubeGeometry), rostro sugerido
 * por una constelación de puntos (ojos con parpadeo, pómulos, labios densos con
 * lip-sync), pelo lateral cian/magenta barrido a un lado (identidad fija), núcleo de
 * pecho brillante con anillos y una scanline vertical que recorre la figura.
 *
 * Rendimiento: geometrías/materiales memorizados una sola vez, cero allocations por
 * frame (colores THREE.Color precalculados, mutación in-place de atributos),
 * instancedMesh para los nodos de circuito, sin luces dinámicas ni sombras.
 */

type V3 = readonly [number, number, number];

const mirrorX = (pts: readonly V3[]): V3[] => pts.map(([x, y, z]): V3 => [-x, y, z]);

// ---- Silueta (coordenadas locales; el grupo raíz baja la figura para encuadrarla) ----
const HEAD_PTS: readonly V3[] = [
  [0, 2.18, 0.02],
  [-0.34, 2.08, 0.05],
  [-0.52, 1.86, 0.08],
  [-0.57, 1.58, 0.12],
  [-0.5, 1.28, 0.16],
  [-0.3, 1.03, 0.19],
  [0, 0.94, 0.21], // mentón
  [0.3, 1.03, 0.19],
  [0.5, 1.28, 0.16],
  [0.57, 1.58, 0.12],
  [0.52, 1.86, 0.08],
  [0.34, 2.08, 0.05],
];
const NECK_L: readonly V3[] = [
  [-0.17, 1.0, 0.14],
  [-0.21, 0.78, 0.12],
  [-0.27, 0.56, 0.1],
];
const SHOULDER_L: readonly V3[] = [
  [-0.28, 0.52, 0.1],
  [-0.68, 0.58, 0.04],
  [-1.06, 0.42, -0.02],
  [-1.3, 0.05, -0.06],
  [-1.4, -0.65, -0.1],
  [-1.32, -1.45, -0.12],
];
const COLLAR_L: readonly V3[] = [
  [-0.3, 0.42, 0.16],
  [-0.46, 0.68, 0.1],
  [-0.52, 0.92, 0.0],
];
const LAPEL_L: readonly V3[] = [
  [-0.32, 0.44, 0.18],
  [-0.26, -0.1, 0.26],
  [-0.2, -0.85, 0.3],
  [-0.24, -1.5, 0.3],
];
const NECKLINE: readonly V3[] = [
  [-0.3, 0.4, 0.2],
  [0, 0.02, 0.3],
  [0.3, 0.4, 0.2],
];
const HEM: readonly V3[] = [
  [-1.32, -1.45, -0.12],
  [0, -1.6, 0.06],
  [1.32, -1.45, -0.12],
];

// Nodos de circuito en la chaqueta (instanciados).
const NODE_POS: readonly V3[] = [
  [-1.06, 0.42, -0.02],
  [1.06, 0.42, -0.02],
  [-0.68, 0.58, 0.04],
  [0.68, 0.58, 0.04],
  [-1.3, 0.05, -0.06],
  [1.3, 0.05, -0.06],
  [-0.52, 0.92, 0.0],
  [0.52, 0.92, 0.0],
  [-0.26, -0.1, 0.26],
  [0.26, -0.1, 0.26],
  [-0.2, -0.85, 0.3],
  [0.2, -0.85, 0.3],
  [-1.4, -0.65, -0.1],
  [1.4, -0.65, -0.1],
];

const EYE_CY = 1.6; // altura del eje de los ojos (para el parpadeo)
const MOUTH_GAP = 0.085; // desplazamiento máximo de labios al hablar

function tubeFrom(points: readonly V3[], radius: number, closed: boolean, segs: number): THREE.TubeGeometry {
  const curve = new THREE.CatmullRomCurve3(
    points.map(([x, y, z]) => new THREE.Vector3(x, y, z)),
    closed,
    "catmullrom",
    0.5,
  );
  return new THREE.TubeGeometry(curve, segs, radius, 6, closed);
}

interface FaceData {
  geo: THREE.BufferGeometry;
  attr: THREE.BufferAttribute;
  base: Float32Array;
  eyeW: Float32Array; // 1 = ojo (colapsa al parpadear), 0.25 = ceja (acompaña)
  mouthW: Float32Array; // >0 labio superior, <0 inferior (magnitud = cuánto se abre)
  count: number;
}

/** Rostro-constelación: ojos, cejas, pómulos, nariz, labios densos y tatuajes de circuito. */
function buildFace(): FaceData {
  const pos: number[] = [];
  const eyeW: number[] = [];
  const mouthW: number[] = [];
  const add = (x: number, y: number, z: number, eye = 0, mouth = 0): void => {
    pos.push(x, y, z);
    eyeW.push(eye);
    mouthW.push(mouth);
  };

  // ojos (contorno + iris + pupila) y cejas
  for (const s of [-1, 1]) {
    const cx = s * 0.23;
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * Math.PI * 2;
      add(cx + Math.cos(a) * 0.125, EYE_CY + Math.sin(a) * 0.052, 0.34, 1);
    }
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      add(cx + Math.cos(a) * 0.045, EYE_CY + Math.sin(a) * 0.042, 0.36, 1);
    }
    add(cx, EYE_CY, 0.37, 1); // pupila
    for (let i = 0; i < 7; i++) {
      const u = i / 6;
      add(cx - 0.16 + u * 0.32, EYE_CY + 0.13 + Math.sin(u * Math.PI) * 0.045, 0.33, 0.25);
    }
    // pómulo
    for (let i = 0; i < 6; i++) {
      const u = i / 5;
      add(s * (0.38 - u * 0.12), 1.42 - u * 0.13 + Math.sin(u * Math.PI) * 0.02, 0.32);
    }
  }

  // nariz
  add(0, 1.52, 0.36);
  add(0, 1.45, 0.38);
  add(0, 1.38, 0.4);
  add(-0.045, 1.32, 0.38);
  add(0.045, 1.32, 0.38);
  add(0, 1.335, 0.41);

  // labios (dos filas por labio; las comisuras casi no se mueven: peso ∝ 1-u²)
  const MY = 1.16;
  for (let i = 0; i < 16; i++) {
    const u = -1 + (i / 15) * 2;
    const arco = 1 - u * u;
    const yTop = MY + 0.02 + 0.034 * arco - 0.016 * Math.exp(-(u * u) / 0.03); // arco de cupido
    add(u * 0.17, yTop, 0.38, 0, 0.35 * arco);
    add(u * 0.165, MY - 0.018 - 0.045 * arco, 0.38, 0, -arco);
  }
  for (let i = 0; i < 12; i++) {
    const u = -0.85 + (i / 11) * 1.7;
    const arco = 1 - u * u;
    add(u * 0.15, MY + 0.045 + 0.026 * arco, 0.375, 0, 0.25 * arco);
    add(u * 0.15, MY - 0.052 - 0.03 * arco, 0.375, 0, -0.8 * arco);
  }

  // tatuajes de circuito en mejilla derecha y cuello (como en avatar.png)
  const circuitos: readonly V3[] = [
    [0.34, 1.5, 0.3],
    [0.42, 1.44, 0.3],
    [0.42, 1.34, 0.3],
    [0.36, 1.26, 0.3],
    [0.44, 1.18, 0.3],
    [0.3, 1.2, 0.31],
    [0.1, 0.86, 0.26],
    [0.15, 0.75, 0.26],
    [0.1, 0.64, 0.26],
    [0.17, 0.56, 0.26],
    [-0.09, 0.8, 0.26],
    [-0.13, 0.66, 0.26],
  ];
  for (const [x, y, z] of circuitos) add(x, y, z);

  const base = new Float32Array(pos);
  const attr = new THREE.BufferAttribute(new Float32Array(pos), 3);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", attr);
  return {
    geo,
    attr,
    base,
    eyeW: new Float32Array(eyeW),
    mouthW: new Float32Array(mouthW),
    count: eyeW.length,
  };
}

export default function CyberGirl() {
  const grp = useRef<THREE.Group>(null!);
  const headGrp = useRef<THREE.Group>(null!);
  const hairGrp = useRef<THREE.Group>(null!);
  const torsoGrp = useRef<THREE.Group>(null!);
  const ringsGrp = useRef<THREE.Group>(null!);
  const coreMesh = useRef<THREE.Mesh>(null!);
  const scanMesh = useRef<THREE.Mesh>(null!);
  const nodesRef = useRef<THREE.InstancedMesh>(null!);

  // estado de animación (sin re-render)
  const phase = useRef(0);
  const openSm = useRef(0);
  const blinkStart = useRef(-10);
  const nextBlink = useRef(1.6);
  const scanPhase = useRef(0);

  // colores destino precalculados (cero allocations en useFrame)
  const statusColors = useMemo(() => {
    const rec = {} as Record<AgentStatus, THREE.Color>;
    for (const key of Object.keys(STATUS_VISUALS) as AgentStatus[]) {
      rec[key] = new THREE.Color(STATUS_VISUALS[key].color);
    }
    return rec;
  }, []);

  const mats = useMemo(() => {
    const neon = (color: string, opacity: number) =>
      new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
    return {
      line: neon("#22d3ee", 0.85),
      core: neon("#a5f3fc", 0.95),
      glow: neon("#22d3ee", 0.25),
      ring: neon("#22d3ee", 0.5),
      node: neon("#67e8f9", 0.7),
      scan: neon("#22d3ee", 0.16),
      // el pelo NO reacciona al estado: identidad cian/magenta fija (avatar.png)
      hairCyan: neon("#22d3ee", 0.8),
      hairBright: neon("#67e8f9", 0.9),
      hairMagenta: neon("#e879f9", 0.85),
      pts: new THREE.PointsMaterial({
        color: "#67e8f9",
        size: 0.03,
        sizeAttenuation: true,
        transparent: true,
        opacity: 0.95,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      }),
    };
  }, []);

  const contours = useMemo(
    () => ({
      head: tubeFrom(HEAD_PTS, 0.02, true, 84),
      torso: [
        tubeFrom(NECK_L, 0.016, false, 12),
        tubeFrom(mirrorX(NECK_L), 0.016, false, 12),
        tubeFrom(SHOULDER_L, 0.02, false, 40),
        tubeFrom(mirrorX(SHOULDER_L), 0.02, false, 40),
        tubeFrom(COLLAR_L, 0.018, false, 12),
        tubeFrom(mirrorX(COLLAR_L), 0.018, false, 12),
        tubeFrom(LAPEL_L, 0.018, false, 28),
        tubeFrom(mirrorX(LAPEL_L), 0.018, false, 28),
        tubeFrom(NECKLINE, 0.014, false, 20),
        tubeFrom(HEM, 0.016, false, 24),
      ],
    }),
    [],
  );

  // 12 mechones barridos hacia el lado izquierdo del espectador (su derecha)
  const hair = useMemo(() => {
    const strands: { geo: THREE.TubeGeometry; magenta: boolean; bright: boolean }[] = [];
    const N = 12;
    for (let i = 0; i < N; i++) {
      const k = i / (N - 1);
      const j = Math.sin(i * 12.9898) * 0.5; // jitter determinista
      const p: readonly V3[] = [
        [0.34 - k * 0.5, 2.02 + Math.sin(k * Math.PI) * 0.22, 0.1 + k * 0.06],
        [-0.15 - k * 0.28, 2.1 - k * 0.05 + j * 0.04, 0.16 + k * 0.05],
        [-0.55 - k * 0.22, 1.72 - k * 0.06, 0.22 + j * 0.05],
        [-0.72 - k * 0.28, 1.2 + j * 0.06, 0.2],
        [-0.66 - k * 0.34, 0.55 - k * 0.12, 0.12],
        [-0.52 - k * 0.42 + j * 0.08, -0.15 - k * 0.45, 0.06],
      ];
      const radio = 0.016 + (i % 3 === 0 ? 0.012 : 0.006);
      strands.push({ geo: tubeFrom(p, radio, false, 26), magenta: i % 4 === 2, bright: i % 3 === 0 });
    }
    return strands;
  }, []);

  const face = useMemo(buildFace, []);

  const geos = useMemo(
    () => ({
      node: new THREE.OctahedronGeometry(0.024, 0),
      core: new THREE.IcosahedronGeometry(0.13, 1),
      glow: new THREE.IcosahedronGeometry(0.24, 1),
      ringA: new THREE.TorusGeometry(0.3, 0.008, 6, 48),
      ringB: new THREE.TorusGeometry(0.42, 0.006, 6, 48),
      scan: new THREE.PlaneGeometry(3.2, 0.045),
    }),
    [],
  );

  // matrices de los nodos instanciados (una sola vez)
  useEffect(() => {
    const m = new THREE.Matrix4();
    NODE_POS.forEach(([x, y, z], i) => {
      m.makeTranslation(x, y, z);
      nodesRef.current.setMatrixAt(i, m);
    });
    nodesRef.current.instanceMatrix.needsUpdate = true;
  }, []);

  useFrame((state, dt) => {
    const t = state.clock.elapsedTime;
    const { status, talking } = useAgentStore.getState();
    const v = STATUS_VISUALS[status];
    const target = statusColors[status];

    // colores reactivos al estado (el pelo conserva su identidad)
    mats.line.color.lerp(target, 0.06);
    mats.pts.color.lerp(target, 0.06);
    mats.core.color.lerp(target, 0.08);
    mats.glow.color.lerp(target, 0.08);
    mats.ring.color.lerp(target, 0.06);
    mats.scan.color.lerp(target, 0.06);
    mats.node.color.lerp(target, 0.06);
    mats.line.opacity = THREE.MathUtils.lerp(mats.line.opacity, 0.7 + v.ring * 0.25, 0.05);

    // flotación + respiración + vaivén de cabeza/pelo
    grp.current.position.y = -0.35 + Math.sin(t * 0.7) * 0.06;
    grp.current.rotation.y = Math.sin(t * 0.28) * 0.05;
    const breath = Math.sin(t * 1.15);
    torsoGrp.current.scale.x = 1 + breath * 0.012;
    torsoGrp.current.scale.z = 1 + breath * 0.012;
    torsoGrp.current.position.y = breath * 0.014;
    headGrp.current.rotation.z = Math.sin(t * 0.45) * 0.022;
    headGrp.current.rotation.x = Math.sin(t * 0.6) * 0.015;
    hairGrp.current.rotation.z = Math.sin(t * 0.55 + 1.3) * 0.018;

    // parpadeo (los puntos del ojo colapsan hacia su eje)
    if (t >= nextBlink.current) {
      blinkStart.current = t;
      nextBlink.current = t + 2.4 + Math.random() * 3.2;
    }
    const bp = (t - blinkStart.current) / 0.16;
    const blink = bp > 0 && bp < 1 ? Math.sin(bp * Math.PI) : 0;

    // lip-sync (talking del store o voz del navegador)
    const active = talking || isSpeaking();
    phase.current += dt * 21;
    let openT = 0;
    if (active) {
      const base = 0.5 + 0.5 * Math.sin(phase.current);
      const flick = 0.5 + 0.5 * Math.sin(phase.current * 2.3 + 1.1);
      openT = Math.min(1, Math.max(0, base * 0.7 + flick * 0.35 + (Math.random() - 0.5) * 0.14));
    }
    openSm.current += (openT - openSm.current) * 0.4;
    const open = openSm.current;

    // constelación: mutación in-place de Y (ojos + labios)
    for (let i = 0; i < face.count; i++) {
      const by = face.base[i * 3 + 1];
      let y = by;
      const ew = face.eyeW[i];
      if (ew > 0) y = by - (by - EYE_CY) * blink * ew;
      const mw = face.mouthW[i];
      if (mw !== 0) y = by + mw * open * MOUTH_GAP;
      face.attr.setY(i, y);
    }
    face.attr.needsUpdate = true;
    mats.pts.size = 0.03 + open * 0.012 + v.pulse * 0.008;

    // núcleo del pecho + anillos
    const pulse = 1 + Math.sin(t * (1.6 + v.speed * 3)) * (0.12 + v.pulse * 0.3) + open * 0.18;
    coreMesh.current.scale.setScalar(pulse);
    coreMesh.current.rotation.y += dt * 0.6;
    mats.glow.opacity = 0.22 + v.pulse * 0.3 + open * 0.15 + Math.sin(t * 2.2) * 0.04;
    ringsGrp.current.rotation.y += dt * (0.4 + v.speed * 0.9);
    ringsGrp.current.rotation.z += dt * 0.15;
    mats.ring.opacity = THREE.MathUtils.lerp(mats.ring.opacity, 0.25 + v.ring * 0.55, 0.06);

    // scanline vertical recorriendo la figura
    scanPhase.current += dt * (0.16 + v.speed * 0.1);
    scanMesh.current.position.y = -1.7 + (scanPhase.current % 1) * 4.05;
    mats.scan.opacity = 0.1 + v.ring * 0.14 + Math.sin(t * 9) * 0.03;

    // nodos de circuito titilando
    mats.node.opacity = 0.55 + Math.sin(t * (2 + v.speed * 4)) * 0.25;
  });

  return (
    <group ref={grp} position={[0, -0.35, 0]}>
      <group ref={headGrp}>
        <mesh geometry={contours.head} material={mats.line} frustumCulled={false} />
        <group ref={hairGrp}>
          {hair.map((s, i) => (
            <mesh
              key={i}
              geometry={s.geo}
              material={s.magenta ? mats.hairMagenta : s.bright ? mats.hairBright : mats.hairCyan}
              frustumCulled={false}
            />
          ))}
        </group>
        <points geometry={face.geo} material={mats.pts} frustumCulled={false} />
      </group>

      <group ref={torsoGrp}>
        {contours.torso.map((g, i) => (
          <mesh key={i} geometry={g} material={mats.line} frustumCulled={false} />
        ))}
        <instancedMesh ref={nodesRef} args={[geos.node, mats.node, NODE_POS.length]} frustumCulled={false} />
        <group position={[0, -0.12, 0.3]}>
          <mesh ref={coreMesh} geometry={geos.core} material={mats.core} frustumCulled={false} />
          <mesh geometry={geos.glow} material={mats.glow} frustumCulled={false} />
          <group ref={ringsGrp}>
            <mesh rotation={[1.2, 0, 0]} geometry={geos.ringA} material={mats.ring} frustumCulled={false} />
            <mesh rotation={[0.4, 0.9, 0]} geometry={geos.ringB} material={mats.ring} frustumCulled={false} />
          </group>
        </group>
      </group>

      <mesh ref={scanMesh} position={[0, 0, 0.55]} geometry={geos.scan} material={mats.scan} frustumCulled={false} />
    </group>
  );
}
