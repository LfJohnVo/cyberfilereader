import { useEffect, useRef, useState } from "react";
import { useAgentStore } from "../../stores/agentStore";
import { useChatStore } from "../../stores/chatStore";

export default function ChatPanel() {
  const { messages, loading, send, stop } = useChatStore();
  const setStatus = useAgentStore((s) => s.setStatus);
  const status = useAgentStore((s) => s.status);
  const talking = useAgentStore((s) => s.talking);
  const [text, setText] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [messages]);

  const submit = () => {
    const t = text.trim();
    if (!t || loading) return;
    setText("");
    void send(t);
  };

  const lastIdx = messages.length - 1;

  return (
    <div className="flex h-full flex-col font-mono">
      <div className="clip-hud pointer-events-auto mb-1.5 inline-flex w-fit items-center gap-2 border border-cyan-400/60 bg-[rgba(4,8,18,0.92)] px-3 py-1 text-[11px] tracking-[0.2em] text-cyan-200">
        ▧ [SGI-AGENT &gt;]
      </div>

      <div className="clip-hud console-frame pointer-events-auto min-h-0 flex-1">
        <div className="clip-hud console-panel flex h-full flex-col px-4 py-3 md:px-6 md:py-4">
          <div className="chat-text min-h-0 flex-1 space-y-2 overflow-y-auto pr-2 text-sm leading-relaxed md:text-base">
            {messages.map((m, i) => {
              const streaming = i === lastIdx && m.role === "assistant" && (loading || talking);
              const cls =
                m.role === "user"
                  ? "text-cyan-100"
                  : m.role === "system"
                    ? "text-emerald-300"
                    : m.noInfo
                      ? "text-rose-300"
                      : "text-[#e0f7ff]";
              return (
                <p key={i} className={cls}>
                  <span className="mr-2 select-none opacity-70">{m.role === "user" ? "›" : "◈"}</span>
                  <span className={"whitespace-pre-wrap" + (streaming ? " caret" : "")}>{m.content}</span>
                </p>
              );
            })}
            {loading && messages[lastIdx]?.role !== "assistant" && (
              <p className="animate-pulse text-cyan-300/80">◈ procesando…</p>
            )}
            <div ref={endRef} />
          </div>

          <div className="mt-3 flex items-center gap-3 border-t border-cyan-500/25 pt-3">
            <span className="glow select-none text-cyan-400">»</span>
            <input
              value={text}
              onChange={(e) => {
                setText(e.target.value);
                if (status === "idle") setStatus("listening");
              }}
              onBlur={() => {
                if (status === "listening") setStatus("idle");
              }}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="Escribe tu consulta…"
              className="flex-1 border border-cyan-500/50 bg-black/60 px-3 py-2 text-cyan-50 placeholder-cyan-600 outline-none transition-colors focus:border-cyan-300 focus:ring-2 focus:ring-cyan-400/40"
            />
            {talking ? (
              <button
                onClick={stop}
                className="clip-hud border border-rose-400/80 bg-black/60 px-4 py-2 text-xs font-semibold tracking-widest text-rose-200 outline-none hover:bg-rose-500/20 focus-visible:ring-2 focus-visible:ring-rose-400/60"
              >
                ■ DETENER
              </button>
            ) : (
              <button
                onClick={submit}
                disabled={loading}
                className="clip-hud border border-fuchsia-400/80 bg-fuchsia-500/20 px-5 py-2 text-xs font-semibold tracking-widest text-fuchsia-100 outline-none hover:bg-fuchsia-500/30 focus-visible:ring-2 focus-visible:ring-fuchsia-400/60 disabled:opacity-40"
              >
                {loading ? "…" : "ENVIAR"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
