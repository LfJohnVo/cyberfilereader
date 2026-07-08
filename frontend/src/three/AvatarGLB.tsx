import { useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import { isSpeaking } from "../lib/tts";
import { useAgentStore } from "../stores/agentStore";

/**
 * Carga /avatar.glb (personaje riggeado, unlit, SIN animaciones ni morph targets).
 * Encuadre BUSTO: solo cabeza+torso por encima de la consola. El modelo se centra por
 * el PECHO en el origen del grupo (pivote natural para asentir/balancear) y se anima
 * por código según el estado del chat + vaivén del pelo.
 *
 * Ajusta el encuadre con estas tres constantes:
 */
const FULL_HEIGHT = 10.0; // altura del modelo completo (mayor = más zoom / más busto)
const CHEST_FRAC = 0.72; // dónde está el pecho respecto a la altura (desde los pies)
const GROUP_Y = -0.6; // posición vertical del pecho en la escena (headroom para la cabeza)

interface HairBone {
  bone: THREE.Object3D;
  baseZ: number;
  baseX: number;
  phase: number;
}

export default function AvatarGLB() {
  const group = useRef<THREE.Group>(null!);
  const { scene } = useGLTF("/avatar.glb");

  const hairBones = useMemo<HairBone[]>(() => {
    // Medir sobre el modelo CRUDO (idempotente en StrictMode).
    scene.scale.setScalar(1);
    scene.position.set(0, 0, 0);
    scene.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(scene);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);
    const s = FULL_HEIGHT / (size.y || 1);
    scene.scale.setScalar(s);
    // Pecho en el origen del grupo → pivote natural para el busto.
    scene.position.set(-center.x * s, -(box.min.y + CHEST_FRAC * size.y) * s, -center.z * s);

    const hair: HairBone[] = [];
    let i = 0;
    scene.traverse((o) => {
      if (o.name.toLowerCase().includes("hair")) {
        hair.push({ bone: o, baseZ: o.rotation.z, baseX: o.rotation.x, phase: i * 0.6 });
        i++;
      }
    });
    return hair;
  }, [scene]);

  useFrame((state) => {
    const { status, talking } = useAgentStore.getState();
    const active = talking || isSpeaking();
    const t = state.clock.elapsedTime;
    const g = group.current;

    // Amplitudes moderadas (encuadre cercano → los giros se notan más).
    let rotY = Math.sin(t * 0.4) * 0.05;
    let rotX = 0;
    let rotZ = 0;
    let bob = Math.sin(t * 1.1) * 0.02;

    if (active || status === "answering") {
      bob = Math.abs(Math.sin(t * 4.2)) * 0.06; // asiente al hablar
      rotX = Math.sin(t * 4.2) * 0.02;
      rotY = Math.sin(t * 0.7) * 0.05;
    } else if (status === "thinking") {
      rotZ = 0.05 + Math.sin(t * 0.9) * 0.02; // ladea la cabeza
      rotX = 0.04;
    } else if (status === "searching") {
      rotY = Math.sin(t * 1.4) * 0.18; // gira escaneando
    } else if (status === "no_info") {
      rotX = 0.08; // cabizbaja
      bob = -0.04;
    } else if (status === "error") {
      rotZ = Math.sin(t * 34) * 0.02; // tiembla
    } else if (status === "listening") {
      rotY = 0.06 + Math.sin(t * 0.4) * 0.05; // atenta hacia el usuario
      rotX = 0.02;
    }

    g.rotation.x = THREE.MathUtils.lerp(g.rotation.x, rotX, 0.1);
    g.rotation.y = THREE.MathUtils.lerp(g.rotation.y, rotY, 0.08);
    g.rotation.z = THREE.MathUtils.lerp(g.rotation.z, rotZ, 0.1);
    g.position.y = THREE.MathUtils.lerp(g.position.y, GROUP_Y + bob, 0.1);

    const amp = active ? 0.08 : 0.045;
    for (const h of hairBones) {
      h.bone.rotation.z = h.baseZ + Math.sin(t * 1.6 + h.phase) * amp;
      h.bone.rotation.x = h.baseX + Math.cos(t * 1.3 + h.phase) * amp * 0.5;
    }
  });

  return (
    <group ref={group} position={[0, GROUP_Y, 0]}>
      <primitive object={scene} />
    </group>
  );
}

useGLTF.preload("/avatar.glb");
