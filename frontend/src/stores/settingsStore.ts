import { create } from "zustand";

const LS_ON = "sgi_voice_on";
const LS_PRESET = "sgi_voice_preset";

interface SettingsState {
  voiceEnabled: boolean;
  presetId: string;
  setVoiceEnabled: (v: boolean) => void;
  setPreset: (id: string) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  voiceEnabled: (localStorage.getItem(LS_ON) ?? "1") === "1",
  presetId: localStorage.getItem(LS_PRESET) ?? "sabina",
  setVoiceEnabled: (voiceEnabled) => {
    localStorage.setItem(LS_ON, voiceEnabled ? "1" : "0");
    set({ voiceEnabled });
  },
  setPreset: (presetId) => {
    localStorage.setItem(LS_PRESET, presetId);
    set({ presetId });
  },
}));
