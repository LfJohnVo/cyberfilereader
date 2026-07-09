import { useEffect, useMemo, useRef } from "react";
import { isSpeaking } from "../../lib/tts";
import { useAgentStore } from "../../stores/agentStore";
import { STATUS_VISUALS } from "../statusVisuals";

/** Avatar 2D (sin Three.js): anillo de estado + ecualizador SVG que reacciona al habla.
 *  Demuestra que el sistema admite avatares "dom" además de "webgl". El color/label salen del
 *  estado (re-render de React); la animación de barras va por rAF sobre refs (sin re-render). */
const BARS = 40;

export default function Onda() {
  const status = useAgentStore((s) => s.status);
  const v = STATUS_VISUALS[status];
  const rects = useRef<(SVGRectElement | null)[]>([]);
  const bars = useMemo(() => Array.from({ length: BARS }, (_, i) => i), []);

  useEffect(() => {
    let raf = 0;
    const tick = () => {
      const { talking } = useAgentStore.getState();
      const active = talking || isSpeaking();
      const t = performance.now() / 1000;
      for (let i = 0; i < rects.current.length; i++) {
        const r = rects.current[i];
        if (!r) continue;
        const b = active ? 0.35 : 0.1;
        const h = b + Math.abs(Math.sin(t * 6 + i * 0.5)) * (active ? 0.55 : 0.06);
        r.setAttribute("height", String(h * 100));
        r.setAttribute("y", String(50 - h * 50));
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div className="flex h-full w-full items-center justify-center" style={{ color: v.color }}>
      <div className="flex flex-col items-center gap-7">
        <div
          className="grid place-items-center rounded-full transition-colors duration-500"
          style={{
            width: 300,
            height: 300,
            border: `1px solid ${v.color}55`,
            boxShadow: `0 0 80px ${v.color}44, inset 0 0 60px ${v.color}22`,
          }}
        >
          <svg viewBox="0 0 100 100" width={220} height={140} preserveAspectRatio="none">
            {bars.map((i) => (
              <rect
                key={i}
                ref={(el) => {
                  rects.current[i] = el;
                }}
                x={(i / BARS) * 100 + 0.4}
                y={44}
                width={100 / BARS - 0.8}
                height={12}
                rx={0.6}
                fill="currentColor"
                opacity={0.85}
              />
            ))}
          </svg>
        </div>
        <div
          className="font-mono text-sm tracking-[0.35em]"
          style={{ textShadow: `0 0 14px ${v.color}` }}
        >
          {v.label}
        </div>
      </div>
    </div>
  );
}
