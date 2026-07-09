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

// nanoid usa crypto.getRandomValues (disponible sobre HTTP), a diferencia de
// crypto.randomUUID, que solo existe en contextos seguros (HTTPS/localhost).
const sid = sessionStorage.getItem("sid") ?? nanoid();
sessionStorage.setItem("sid", sid);
const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

const REVEAL_CPS = 20; // caracteres por segundo del efecto máquina de escribir
let revealRAF = 0;

interface ChatState {
  messages: Msg[];
  sources: Source[];
  loading: boolean;
  areas: string;
  setAreas: (a: string) => void;
  send: (text: string) => Promise<void>;
  stop: () => void;
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

      // Mensaje del asistente vacío: se irá "escribiendo" a la vez que habla.
      set((s) => ({
        messages: [...s.messages, { role: "assistant", content: "", noInfo: res.no_info }],
        sources: res.sources,
      }));
      agent.setStatus(res.no_info ? "no_info" : "answering");
      agent.setTalking(true);

      // Voz (según ajustes del usuario) + revelado sincronizado del texto.
      const settings = useSettingsStore.getState();
      speak(res.answer, { presetId: settings.presetId, enabled: settings.voiceEnabled });
      await new Promise<void>((resolve) => {
        const full = res.answer;
        let startTs = 0;
        let prevN = -1;
        const step = (ts: number) => {
          if (!startTs) startTs = ts;
          const n = Math.min(full.length, Math.floor(((ts - startTs) / 1000) * REVEAL_CPS));
          // rAF corre a ~60 fps pero el texto solo avanza a REVEAL_CPS: evita el `set` (y el
          // re-render) redundante cuando no se revelaron caracteres nuevos en este frame.
          if (n !== prevN) {
            prevN = n;
            set((s) => {
              const msgs = s.messages.slice();
              const li = msgs.length - 1;
              if (li >= 0 && msgs[li].role === "assistant") {
                msgs[li] = { ...msgs[li], content: full.slice(0, n) };
              }
              return { messages: msgs };
            });
          }
          if (n < full.length) revealRAF = requestAnimationFrame(step);
          else resolve();
        };
        revealRAF = requestAnimationFrame(step);
      });

      // El texto terminó; la boca sigue moviéndose mientras la voz siga hablando
      // (el Avatar observa speechSynthesis.speaking). Cerramos el estado "talking".
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
    stopSpeaking();
    useAgentStore.getState().setTalking(false);
    useAgentStore.getState().setStatus("idle");
    set({ loading: false });
  },
}));
