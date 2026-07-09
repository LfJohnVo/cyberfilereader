import { useFrame } from "@react-three/fiber";
import { useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { isSpeaking } from "../../lib/tts";
import { useAgentStore } from "../../stores/agentStore";
import { STATUS_VISUALS, type AgentStatus } from "../statusVisuals";

const N = 28;
const TURNS = 3;
const H = 4.6;
const R = 1.05;

export default function Helix() {
  const root = useRef<THREE.Group>(null!);
  const nodes = useRef<THREE.InstancedMesh>(null!);
  const color = useRef(new THREE.Color("#22d3ee"));
  const dummy = useMemo(() => new THREE.Object3D(), []);

  const statusColors = useMemo(() => {
    const rec = {} as Record<AgentStatus, THREE.Color>;
    for (const k of Object.keys(STATUS_VISUALS) as AgentStatus[]) {
      rec[k] = new THREE.Color(STATUS_VISUALS[k].color);
    }
    return rec;
  }, []);

  // Dos hebras (2*N instancias) desfasadas 180°.
  const base = useMemo(() => {
    const arr: [number, number, number][] = [];
    for (let s = 0; s < 2; s++) {
      for (let i = 0; i < N; i++) {
        const f = i / (N - 1);
        const ang = f * Math.PI * 2 * TURNS + s * Math.PI;
        arr.push([Math.cos(ang) * R, (f - 0.5) * H, Math.sin(ang) * R]);
      }
    }
    return arr;
  }, []);

  useLayoutEffect(() => {
    base.forEach((p, i) => {
      dummy.position.set(p[0], p[1], p[2]);
      dummy.scale.setScalar(0.13);
      dummy.updateMatrix();
      nodes.current.setMatrixAt(i, dummy.matrix);
    });
    nodes.current.instanceMatrix.needsUpdate = true;
  }, [base, dummy]);

  useFrame((state, dt) => {
    const { status, talking } = useAgentStore.getState();
    const v = STATUS_VISUALS[status];
    const active = talking || isSpeaking();
    const t = state.clock.elapsedTime;

    color.current.lerp(statusColors[status], 0.06);
    root.current.rotation.y += dt * (0.2 + v.speed * 0.9);
    root.current.rotation.z = Math.sin(t * 0.3) * 0.08;

    for (let i = 0; i < base.length; i++) {
      const p = base[i];
      const s = 0.12 + (active ? Math.abs(Math.sin(t * 6 + i * 0.6)) * 0.08 : 0.02);
      dummy.position.set(p[0], p[1], p[2]);
      dummy.scale.setScalar(s);
      dummy.updateMatrix();
      nodes.current.setMatrixAt(i, dummy.matrix);
    }
    nodes.current.instanceMatrix.needsUpdate = true;
    (nodes.current.material as THREE.MeshBasicMaterial).color.copy(color.current);
  });

  return (
    <group ref={root} position={[0, 0.7, 0]}>
      <instancedMesh ref={nodes} args={[undefined, undefined, 2 * N]} frustumCulled={false}>
        <sphereGeometry args={[1, 12, 12]} />
        <meshBasicMaterial color="#22d3ee" toneMapped={false} />
      </instancedMesh>
    </group>
  );
}
