import { useEffect } from "react";
import AgentStatusPanel from "./components/AgentStatusPanel";
import AvatarPicker from "./components/AvatarPicker";
import ComplianceModal from "./components/ComplianceModal";
import ErrorBoundary from "./components/ErrorBoundary";
import VoiceControls from "./components/VoiceControls";
import ChatPanel from "./components/chat/ChatPanel";
import SourcesPanel from "./components/SourcesPanel";
import { primeVoices } from "./lib/tts";
import { useSettingsStore } from "./stores/settingsStore";
import Scene from "./three/Scene";

export default function App() {
  const chatExpanded = useSettingsStore((s) => s.chatExpanded);
  useEffect(() => {
    primeVoices();
  }, []);

  return (
    <div className="scanlines relative h-screen w-screen overflow-hidden text-cyan-100">
      {/* si WebGL falla, el degradado de fondo hace de respaldo */}
      <div className="absolute inset-0">
        <ErrorBoundary label="scene" fallback={null}>
          <Scene />
        </ErrorBoundary>
      </div>

      <header className="pointer-events-none absolute inset-x-0 top-0 z-20 flex items-center justify-between px-5 py-3 font-mono">
        <span className="glow text-sm tracking-[0.3em] text-cyan-300 md:text-base">
          SGI-AGENT <span className="text-fuchsia-400/80">// ASISTENTE CIBERNÉTICA</span>
        </span>
        <span className="flex items-center gap-2 text-xs text-fuchsia-300">
          <span
            className="h-2 w-2 animate-pulse rounded-full bg-fuchsia-400"
            style={{ boxShadow: "0 0 8px #e879f9" }}
          />
          ONLINE
        </span>
      </header>

      <div className="absolute left-4 top-16 z-20 space-y-3">
        <AgentStatusPanel />
        <AvatarPicker />
        <VoiceControls />
        <ComplianceModal />
      </div>
      <div className="absolute right-4 top-16 z-20">
        <SourcesPanel />
      </div>

      <div
        className={`absolute inset-x-0 bottom-0 z-20 px-5 pb-4 pt-2 transition-[height] duration-300 ${
          chatExpanded ? "h-[72vh]" : "h-[34vh]"
        }`}
      >
        <div className="mx-auto h-full max-w-[1400px]">
          <ChatPanel />
        </div>
      </div>
    </div>
  );
}
