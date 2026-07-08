import { useChatStore } from "../stores/chatStore";

export default function SourcesPanel() {
  const sources = useChatStore((s) => s.sources);
  return (
    <aside className="neon neon-mag clip-hud pointer-events-auto flex max-h-[72vh] w-[320px] flex-col p-3 font-mono text-[11px]">
      <h2 className="glow mb-2 tracking-[0.25em] text-fuchsia-300">FUENTES CONSULTADAS</h2>
      {sources.length === 0 && <p className="text-cyan-700/70">— sin fuentes en el último turno —</p>}
      <ul className="space-y-2 overflow-y-auto pr-1">
        {sources.map((f) => (
          <li key={f.n} className="clip-hud border border-fuchsia-500/30 bg-black/30 p-2">
            <p className="text-fuchsia-200">
              [{f.n}] {f.file_name}
              {f.page ? ` · pág. ${f.page}` : ""}
            </p>
            <p className="text-cyan-400/80">
              área {f.area} · v{f.version} · score {f.score}
            </p>
            <p className="mt-1 line-clamp-3 text-cyan-200/50">{f.snippet}</p>
          </li>
        ))}
      </ul>
    </aside>
  );
}
