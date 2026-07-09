import { useSettingsStore } from "../stores/settingsStore";
import { AVATARS } from "../three/avatars/registry";

export default function AvatarPicker() {
  const avatarId = useSettingsStore((s) => s.avatarId);
  const setAvatar = useSettingsStore((s) => s.setAvatar);

  return (
    <aside className="neon clip-hud pointer-events-auto w-[248px] p-3 font-mono text-xs">
      <h2 className="glow mb-2 tracking-[0.25em] text-cyan-300">AVATAR</h2>
      <select
        value={avatarId}
        onChange={(e) => setAvatar(e.target.value)}
        className="w-full rounded border border-cyan-500/40 bg-black/40 px-2 py-1 text-cyan-100 outline-none"
      >
        {AVATARS.map((a) => (
          <option key={a.id} value={a.id} className="bg-slate-900">
            {a.label}
          </option>
        ))}
      </select>
      <p className="mt-2 text-[10px] text-cyan-700/80">
        Se guarda en el navegador · cambio en caliente
      </p>
    </aside>
  );
}
