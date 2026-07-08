import { useAgentStore } from "../stores/agentStore";
import { STATUS_VISUALS } from "../three/statusVisuals";

export default function AgentStatusPanel() {
  const status = useAgentStore((s) => s.status);
  const v = STATUS_VISUALS[status];
  return (
    <aside className="neon clip-hud pointer-events-auto w-[248px] p-3 font-mono text-xs">
      <h2 className="glow mb-2 tracking-[0.25em] text-cyan-300">NÚCLEO // ICOSA-12</h2>
      <p className="text-cyan-700/80">ESTADO</p>
      <p className="mb-2 flex items-center gap-2 text-sm" style={{ color: v.color }}>
        <span
          className="inline-block h-2 w-2 animate-pulse rounded-full"
          style={{ background: v.color, boxShadow: `0 0 8px ${v.color}` }}
        />
        {v.label}
      </p>
      <p className="text-cyan-700/80">MODELO</p>
      <p className="text-cyan-200">ollama/qwen3:8b · nomic-embed</p>
    </aside>
  );
}
