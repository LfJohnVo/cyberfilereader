import { create } from "zustand";
import type { AgentStatus } from "../three/statusVisuals";

interface AgentState {
  status: AgentStatus;
  talking: boolean; // true mientras se redacta/habla la respuesta (mueve la boca)
  setStatus: (s: AgentStatus) => void;
  setTalking: (v: boolean) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  status: "idle",
  talking: false,
  setStatus: (status) => set({ status }),
  setTalking: (talking) => set({ talking }),
}));
