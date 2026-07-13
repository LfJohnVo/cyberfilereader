import { nanoid } from "nanoid";
import { create } from "zustand";
import { sendChat, type Source } from "../lib/api";
import { speak, stopSpeaking } from "../lib/tts";
import { useAgentStore } from "./agentStore";
import { useSettingsStore } from "./settingsStore";

export interface Msg {
  role: "user" | "assistant" | "system";
  content: string;
  noInfo?: boolean;
}

// nanoid funciona sobre HTTP; crypto.randomUUID solo en contexto seguro.
const sid = sessionStorage.getItem("sid") ?? nanoid();
sessionStorage.setItem("sid", sid);
const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

const REVEAL_CPS = 20;
let revealRAF = 0;
// Handle del revelado en curso: permite saltarlo (mostrar todo) desde fuera de send().
let activeReveal: { done: () => void } | null = null;

interface ChatState {
  messages: Msg[];
  sources: Source[];
  loading: boolean;
  areas: string;
  setAreas: (a: string) => void;
  send: (text: string) => Promise<void>;
  stop: () => void;
  revealNow: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [
    { role: "system", content: "SGI-AGENT EN LÍNEA — NÚCLEO SINCRONIZADO" },
    {
      role: "assistant",
      content:
        "Hola, soy la asistente del SGI. Pregúntame por políticas, procedimientos o lineamientos ISO.",
    },
  ],
  sources: [],
  loading: false,
  areas: "*",
  setAreas: (areas) => set({ areas }),

  send: async (text) => {
    const agent = useAgentStore.getState();
    set((s) => ({ messages: [...s.messages, { role: "user", content: text }], loading: true }));
    try {
      agent.setStatus("thinking");
      await wait(300);
      agent.setStatus("searching");
      const res = await sendChat(text, sid, get().areas);

      set((s) => ({
        messages: [...s.messages, { role: "assistant", content: "", noInfo: res.no_info }],
        sources: res.sources,
      }));
      agent.setStatus(res.no_info ? "no_info" : "answering");
      agent.setTalking(true);

      const settings = useSettingsStore.getState();
      speak(res.answer, { presetId: settings.presetId, enabled: settings.voiceEnabled });
      await new Promise<void>((resolve) => {
        const full = res.answer;
        let startTs = 0;
        let prevN = -1;
        const writeUpTo = (n: number) =>
          set((s) => {
            const msgs = s.messages.slice();
            const li = msgs.length - 1;
            if (li >= 0 && msgs[li].role === "assistant") {
              msgs[li] = { ...msgs[li], content: full.slice(0, n) };
            }
            return { messages: msgs };
          });
        const finish = () => {
          activeReveal = null;
          resolve();
        };
        // Saltar el revelado: vuelca el texto completo de inmediato y termina.
        activeReveal = {
          done: () => {
            cancelAnimationFrame(revealRAF);
            writeUpTo(full.length);
            finish();
          },
        };
        const step = (ts: number) => {
          if (!startTs) startTs = ts;
          const n = Math.min(full.length, Math.floor(((ts - startTs) / 1000) * REVEAL_CPS));
          // Evita el set redundante cuando no hay caracteres nuevos en el frame.
          if (n !== prevN) {
            prevN = n;
            writeUpTo(n);
          }
          if (n < full.length) revealRAF = requestAnimationFrame(step);
          else finish();
        };
        revealRAF = requestAnimationFrame(step);
      });

      agent.setTalking(false);
      agent.setStatus(res.no_info ? "no_info" : "idle");
      await wait(res.no_info ? 1500 : 500);
      agent.setStatus("idle");
    } catch (e) {
      stopSpeaking();
      agent.setTalking(false);
      agent.setStatus("error");
      set((s) => ({
        messages: [...s.messages, { role: "system", content: `ERROR: ${(e as Error).message}` }],
      }));
      await wait(2000);
      agent.setStatus("idle");
    } finally {
      set({ loading: false });
    }
  },

  stop: () => {
    cancelAnimationFrame(revealRAF);
    activeReveal = null;
    stopSpeaking();
    useAgentStore.getState().setTalking(false);
    useAgentStore.getState().setStatus("idle");
    set({ loading: false });
  },

  // Muestra la respuesta completa de inmediato y silencia la voz (salta el efecto de tipeo).
  revealNow: () => {
    stopSpeaking();
    activeReveal?.done();
  },
}));
