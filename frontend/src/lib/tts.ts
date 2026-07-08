// Voz femenina en español vía Web Speech API del navegador (sin backend).
export const ttsSupported =
  typeof window !== "undefined" && "speechSynthesis" in window;

// 5 "tipos" de voz seleccionables. Cada preset intenta casar una voz instalada por
// nombre/idioma (en orden) y aplica su propio tono/velocidad para dar variedad aunque
// el sistema tenga pocas voces en español.
export interface VoicePreset {
  id: string;
  label: string;
  match: string[];
  pitch: number;
  rate: number;
}

export const VOICE_PRESETS: VoicePreset[] = [
  { id: "sabina", label: "Sabina · cálida (MX)", match: ["sabina", "es-mx", "es_mx"], pitch: 1.05, rate: 1.0 },
  { id: "helena", label: "Helena · clara (ES)", match: ["helena", "laura", "es-es", "es_es"], pitch: 1.16, rate: 1.03 },
  { id: "serena", label: "Serena · suave", match: ["sabina", "helena", "es-", "es_"], pitch: 0.95, rate: 0.9 },
  { id: "agil", label: "Ágil · rápida", match: ["helena", "sabina", "es-", "es_"], pitch: 1.12, rate: 1.28 },
  { id: "neo", label: "Neo · grave", match: ["pablo", "jorge", "raul", "es-", "es_"], pitch: 0.82, rate: 0.98 },
];

let all: SpeechSynthesisVoice[] = [];
function refresh() {
  if (ttsSupported) all = window.speechSynthesis.getVoices();
}

export function primeVoices(): void {
  if (!ttsSupported) return;
  refresh();
  if (all.length === 0) window.speechSynthesis.onvoiceschanged = refresh;
}

const FEMALE_HINTS = [
  "sabina",
  "helena",
  "laura",
  "mónica",
  "monica",
  "paulina",
  "elvira",
  "female",
  "mujer",
  "google español",
];

function bestFemaleEs(): SpeechSynthesisVoice | null {
  if (!all.length) refresh();
  const es = all.filter((v) => v.lang.toLowerCase().startsWith("es"));
  const pool = es.length ? es : all;
  const scored = pool.map((v) => {
    const k = `${v.name} ${v.lang}`.toLowerCase();
    const i = FEMALE_HINTS.findIndex((h) => k.includes(h));
    return { v, r: i < 0 ? 99 : i };
  });
  scored.sort((a, b) => a.r - b.r);
  return scored[0]?.v ?? null;
}

function resolveVoice(preset: VoicePreset): SpeechSynthesisVoice | null {
  if (!all.length) refresh();
  for (const hint of preset.match) {
    const v = all.find((x) => `${x.name} ${x.lang}`.toLowerCase().includes(hint));
    if (v) return v;
  }
  return bestFemaleEs();
}

export function presetById(id: string): VoicePreset {
  return VOICE_PRESETS.find((p) => p.id === id) ?? VOICE_PRESETS[0];
}

export function voiceNameFor(id: string): string {
  if (!ttsSupported) return "sin voz";
  return resolveVoice(presetById(id))?.name ?? "voz del sistema";
}

export interface SpeakOpts {
  presetId?: string;
  enabled?: boolean;
  onEnd?: () => void;
}

export function speak(text: string, opts: SpeakOpts = {}): void {
  const { presetId = "sabina", enabled = true, onEnd } = opts;
  if (!ttsSupported || !enabled || !text.trim()) {
    onEnd?.();
    return;
  }
  const synth = window.speechSynthesis;
  synth.cancel();
  const preset = presetById(presetId);
  const u = new SpeechSynthesisUtterance(text);
  const v = resolveVoice(preset);
  if (v) {
    u.voice = v;
    u.lang = v.lang;
  } else {
    u.lang = "es-ES";
  }
  u.pitch = preset.pitch;
  u.rate = preset.rate;
  u.onend = () => onEnd?.();
  u.onerror = () => onEnd?.();
  synth.speak(u);
}

export function stopSpeaking(): void {
  if (ttsSupported) window.speechSynthesis.cancel();
}

export function isSpeaking(): boolean {
  return ttsSupported && window.speechSynthesis.speaking;
}
