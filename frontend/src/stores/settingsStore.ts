import { create } from "zustand";
import { DEFAULT_AVATAR } from "../three/avatars/registry";

const LS_ON = "sgi_voice_on";
const LS_PRESET = "sgi_voice_preset";
const LS_AVATAR = "sgi_avatar";

interface SettingsState {
  voiceEnabled: boolean;
  presetId: string;
  avatarId: string;
  setVoiceEnabled: (v: boolean) => void;
  setPreset: (id: string) => void;
  setAvatar: (id: string) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  voiceEnabled: (localStorage.getItem(LS_ON) ?? "1") === "1",
  presetId: localStorage.getItem(LS_PRESET) ?? "sabina",
  avatarId: localStorage.getItem(LS_AVATAR) ?? DEFAULT_AVATAR,
  setVoiceEnabled: (voiceEnabled) => {
    localStorage.setItem(LS_ON, voiceEnabled ? "1" : "0");
    set({ voiceEnabled });
  },
  setPreset: (presetId) => {
    localStorage.setItem(LS_PRESET, presetId);
    set({ presetId });
  },
  setAvatar: (avatarId) => {
    localStorage.setItem(LS_AVATAR, avatarId);
    set({ avatarId });
  },
}));
