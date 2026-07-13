import { useEffect, useRef, useState } from "react";
import { useAgentStore } from "../../stores/agentStore";
import { useChatStore } from "../../stores/chatStore";
import { type ChatSize, useSettingsStore } from "../../stores/settingsStore";

const SIZE_CLS: Record<ChatSize, string> = {
  sm: "text-xs md:text-sm leading-relaxed",
  md: "text-sm md:text-base leading-relaxed",
  lg: "text-base md:text-lg leading-loose",
};
const SIZE_META: { id: ChatSize; label: string; px: string }[] = [
  { id: "sm", label: "Compacta", px: "10px" },
  { id: "md", label: "Normal", px: "12px" },
  { id: "lg", label: "Amplia", px: "15px" },
];

export default function ChatPanel() {
  const { messages, loading, send, stop, revealNow } = useChatStore();
  const setStatus = useAgentStore((s) => s.setStatus);
  const status = useAgentStore((s) => s.status);
  const talking = useAgentStore((s) => s.talking);
  const chatSize = useSettingsStore((s) => s.chatSize);
  const setChatSize = useSettingsStore((s) => s.setChatSize);
  const chatExpanded = useSettingsStore((s) => s.chatExpanded);
  const toggleChatExpanded = useSettingsStore((s) => s.toggleChatExpanded);
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
      <div className="mb-1.5 flex items-center justify-between gap-2">
        <div className="clip-hud pointer-events-auto inline-flex w-fit items-center gap-2 border border-cyan-400/60 bg-[rgba(4,8,18,0.92)] px-3 py-1 text-[11px] tracking-[0.2em] text-cyan-200">
          ▧ [SGI-AGENT &gt;]
        </div>
        <div className="pointer-events-auto flex items-center gap-1.5">
          <div className="clip-hud inline-flex items-center overflow-hidden border border-cyan-500/40 bg-[rgba(4,8,18,0.92)]">
            {SIZE_META.map((s, i) => (
              <button
                key={s.id}
                onClick={() => setChatSize(s.id)}
                title={`Vista ${s.label}`}
                aria-pressed={chatSize === s.id}
                style={{ fontSize: s.px }}
                className={
                  "px-2 py-1 font-mono leading-none transition-colors " +
                  (i > 0 ? "border-l border-cyan-500/30 " : "") +
                  (chatSize === s.id
                    ? "bg-cyan-500/20 text-cyan-100"
                    : "text-cyan-500/70 hover:text-cyan-200")
                }
              >
                A
              </button>
            ))}
          </div>
          <button
            onClick={toggleChatExpanded}
            title={chatExpanded ? "Reducir consola" : "Ampliar consola"}
            aria-pressed={chatExpanded}
            className="clip-hud border border-fuchsia-500/50 bg-[rgba(4,8,18,0.92)] px-2 py-1 text-[13px] leading-none text-fuchsia-200 hover:bg-fuchsia-500/15"
          >
            {chatExpanded ? "⤡" : "⤢"}
          </button>
        </div>
      </div>

      <div className="clip-hud console-frame pointer-events-auto min-h-0 flex-1">
        <div className="clip-hud console-panel flex h-full flex-col px-4 py-3 md:px-6 md:py-4">
          <div className={`chat-text min-h-0 flex-1 space-y-2 overflow-y-auto pr-2 ${SIZE_CLS[chatSize]}`}>
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
              <>
                <button
                  onClick={revealNow}
                  title="Mostrar toda la respuesta y silenciar la voz"
                  className="clip-hud border border-cyan-400/80 bg-cyan-500/15 px-4 py-2 text-xs font-semibold tracking-widest text-cyan-100 outline-none hover:bg-cyan-500/25 focus-visible:ring-2 focus-visible:ring-cyan-400/60"
                >
                  ⏭ MOSTRAR YA
                </button>
                <button
                  onClick={stop}
                  title="Detener"
                  className="clip-hud border border-rose-400/80 bg-black/60 px-3 py-2 text-xs font-semibold tracking-widest text-rose-200 outline-none hover:bg-rose-500/20 focus-visible:ring-2 focus-visible:ring-rose-400/60"
                >
                  ■
                </button>
              </>
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
