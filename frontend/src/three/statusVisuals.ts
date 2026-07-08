// Contrato compartido con el backend: los 7 estados del agente (idénticos a schemas/chat.py).
export type AgentStatus =
  | "idle"
  | "listening"
  | "thinking"
  | "searching"
  | "answering"
  | "no_info"
  | "error";

// Paleta cyberpunk (cian/magenta). `speed/ring/pulse` alimentan el aura del avatar y el fondo.
export const STATUS_VISUALS: Record<
  AgentStatus,
  { label: string; color: string; speed: number; ring: number; pulse: number }
> = {
  idle: { label: "ESTABLE", color: "#22d3ee", speed: 0.15, ring: 0.15, pulse: 0.06 },
  listening: { label: "ESCUCHANDO", color: "#38bdf8", speed: 0.3, ring: 0.35, pulse: 0.12 },
  thinking: { label: "PENSANDO", color: "#a855f7", speed: 0.9, ring: 0.5, pulse: 0.25 },
  searching: { label: "CONSULTANDO DOCUMENTOS", color: "#e879f9", speed: 1.4, ring: 0.85, pulse: 0.35 },
  answering: { label: "RESPONDIENDO", color: "#22d3ee", speed: 0.7, ring: 1.0, pulse: 0.5 },
  no_info: { label: "SIN INFORMACIÓN", color: "#fb7185", speed: 0.1, ring: 0.25, pulse: 0.06 },
  error: { label: "ERROR", color: "#f43f5e", speed: 0.05, ring: 0.2, pulse: 0.6 },
};
