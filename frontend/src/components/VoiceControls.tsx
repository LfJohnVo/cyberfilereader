import { VOICE_PRESETS, speak, voiceNameFor } from "../lib/tts";
import { useSettingsStore } from "../stores/settingsStore";

export default function VoiceControls() {
  // Selectores atómicos: así este panel solo re-renderiza cuando cambian voz/preset, no al
  // cambiar de avatar (avatarId vive en el mismo store).
  const voiceEnabled = useSettingsStore((s) => s.voiceEnabled);
  const presetId = useSettingsStore((s) => s.presetId);
  const setVoiceEnabled = useSettingsStore((s) => s.setVoiceEnabled);
  const setPreset = useSettingsStore((s) => s.setPreset);
  return (
    <aside className="neon neon-mag clip-hud pointer-events-auto w-[248px] p-3 font-mono text-[11px]">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="glow tracking-[0.25em] text-fuchsia-300">VOZ</h2>
        <button
          onClick={() => setVoiceEnabled(!voiceEnabled)}
          className={
            "clip-hud border px-2 py-0.5 text-[10px] tracking-widest " +
            (voiceEnabled
              ? "border-cyan-400/60 bg-cyan-500/10 text-cyan-200"
              : "border-zinc-600/60 text-zinc-400")
          }
        >
          {voiceEnabled ? "🔊 ON" : "🔇 OFF"}
        </button>
      </div>
      <select
        value={presetId}
        onChange={(e) => setPreset(e.target.value)}
        disabled={!voiceEnabled}
        className="w-full border border-fuchsia-500/40 bg-black/50 px-2 py-1 text-fuchsia-200 outline-none disabled:opacity-40"
      >
        {VOICE_PRESETS.map((p) => (
          <option key={p.id} value={p.id} className="bg-[#0a0f1e]">
            {p.label}
          </option>
        ))}
      </select>
      <p className="mt-1 truncate text-cyan-500/70">→ {voiceNameFor(presetId)}</p>
      <button
        onClick={() =>
          speak("Hola, soy la asistente del SGI. Así sonará mi voz.", {
            presetId,
            enabled: true,
          })
        }
        className="clip-hud mt-2 w-full border border-cyan-500/50 px-2 py-1 text-cyan-200 hover:bg-cyan-500/10"
      >
        ▶ Probar voz
      </button>
    </aside>
  );
}
