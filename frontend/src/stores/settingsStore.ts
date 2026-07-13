import { create } from "zustand";
import { DEFAULT_AVATAR } from "../three/avatars/registry";

const LS_ON = "sgi_voice_on";
const LS_PRESET = "sgi_voice_preset";
const LS_AVATAR = "sgi_avatar";
const LS_CHAT_SIZE = "sgi_chat_size";
const LS_CHAT_EXPANDED = "sgi_chat_expanded";

export type ChatSize = "sm" | "md" | "lg";
const CHAT_SIZES: ChatSize[] = ["sm", "md", "lg"];

interface SettingsState {
  voiceEnabled: boolean;
  presetId: string;
  avatarId: string;
  chatSize: ChatSize;
  chatExpanded: boolean;
  setVoiceEnabled: (v: boolean) => void;
  setPreset: (id: string) => void;
  setAvatar: (id: string) => void;
  setChatSize: (s: ChatSize) => void;
  toggleChatExpanded: () => void;
}

const storedSize = localStorage.getItem(LS_CHAT_SIZE) as ChatSize | null;

export const useSettingsStore = create<SettingsState>((set) => ({
  voiceEnabled: (localStorage.getItem(LS_ON) ?? "1") === "1",
  presetId: localStorage.getItem(LS_PRESET) ?? "sabina",
  avatarId: localStorage.getItem(LS_AVATAR) ?? DEFAULT_AVATAR,
  chatSize: storedSize && CHAT_SIZES.includes(storedSize) ? storedSize : "md",
  chatExpanded: localStorage.getItem(LS_CHAT_EXPANDED) === "1",
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
  setChatSize: (chatSize) => {
    localStorage.setItem(LS_CHAT_SIZE, chatSize);
    set({ chatSize });
  },
  toggleChatExpanded: () =>
    set((s) => {
      const chatExpanded = !s.chatExpanded;
      localStorage.setItem(LS_CHAT_EXPANDED, chatExpanded ? "1" : "0");
      return { chatExpanded };
    }),
}));
