import { type RefObject, useEffect, useRef, useState } from "react";
import { isSpeaking } from "../lib/tts";
import { useAgentStore } from "../stores/agentStore";
import { STATUS_VISUALS } from "../three/statusVisuals";

/**
 * Avatar reactivo. Si existe /avatar.png (tu foto), la usa con una boca superpuesta
 * animada; si no, dibuja un rostro cyber SVG con boca controlable. En ambos casos la
 * boca se abre/cierra mientras `talking` o la voz (speechSynthesis) están activos.
 *
 * Para tu foto: coloca frontend/public/avatar.png y ajusta --mouth-x/--mouth-y (abajo).
 */
export default function Avatar() {
  const [hasPhoto, setHasPhoto] = useState(false);
  const mouthRef = useRef<HTMLDivElement>(null);
  const svgMouthRef = useRef<SVGEllipseElement>(null);
  const auraRef = useRef<HTMLDivElement>(null);
  const floatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const img = new Image();
    img.onload = () => setHasPhoto(true);
    img.onerror = () => setHasPhoto(false);
    img.src = "/avatar.png";
  }, []);

  useEffect(() => {
    let raf = 0;
    let phase = 0;
    const loop = (ts: number) => {
      const { talking, status } = useAgentStore.getState();
      const active = talking || isSpeaking();
      const time = ts / 1000;
      phase += 0.34;
      let open = 0;
      if (active) {
        const base = 0.5 + 0.5 * Math.sin(phase);
        const flick = 0.5 + 0.5 * Math.sin(phase * 2.3 + 1.1);
        open = Math.max(0, Math.min(1, base * 0.7 + flick * 0.35 + (Math.random() - 0.5) * 0.14));
      }
      const color = STATUS_VISUALS[status].color;

      const mouth = mouthRef.current;
      if (mouth) {
        mouth.style.transform = `translate(-50%,-50%) scaleY(${0.1 + open}) scaleX(${0.85 + open * 0.25})`;
        mouth.style.opacity = active ? String(0.2 + open * 0.4) : "0";
        mouth.style.background = `radial-gradient(ellipse at center, ${color}, ${color}22 62%, transparent 72%)`;
        mouth.style.boxShadow = `0 0 ${5 + open * 16}px ${color}`;
      }
      const sm = svgMouthRef.current;
      if (sm) {
        sm.setAttribute("ry", String(1.5 + open * 9));
        sm.setAttribute("fill", color);
        sm.style.filter = `drop-shadow(0 0 ${4 + open * 10}px ${color})`;
      }
      const aura = auraRef.current;
      if (aura) {
        const a = (active ? 0.3 + open * 0.45 : 0.16).toFixed(2);
        aura.style.boxShadow = `0 0 130px 24px color-mix(in srgb, ${color} ${Number(a) * 100}%, transparent)`;
        aura.style.borderColor = `color-mix(in srgb, ${color} 45%, transparent)`;
      }
      const floatEl = floatRef.current;
      if (floatEl) {
        const bob = Math.sin(time * 0.7) * (active ? 11 : 7);
        const sway = Math.sin(time * 0.4) * 0.7;
        const breathe = 1 + Math.sin(time * 0.9) * 0.006;
        floatEl.style.transform = `translateY(${bob.toFixed(2)}px) rotate(${sway.toFixed(2)}deg) scale(${breathe.toFixed(4)})`;
        floatEl.style.filter = `drop-shadow(0 0 ${((active ? 30 : 16) + open * 22).toFixed(0)}px color-mix(in srgb, ${color} 65%, transparent))`;
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
      <div
        ref={auraRef}
        className="absolute rounded-full border"
        style={{ height: "60vh", width: "60vh", maxWidth: "660px", maxHeight: "660px", transition: "box-shadow .18s" }}
      />
      <div
        ref={floatRef}
        className="relative flex items-center justify-center"
        style={{ willChange: "transform" }}
      >
        {hasPhoto ? (
          <div className="relative" style={{ height: "84vh", maxHeight: "920px" }}>
            <img
              src="/avatar.png"
              alt="avatar"
              className="h-full w-auto select-none object-contain"
            />
          <div
            ref={mouthRef}
            className="absolute rounded-[50%]"
            style={{
              left: "var(--mouth-x, 49%)",
              top: "var(--mouth-y, 38.5%)",
              height: "2.4%",
              width: "6.5%",
              mixBlendMode: "screen",
              transition: "opacity .09s",
            }}
          />
        </div>
        ) : (
          <FallbackFace svgMouthRef={svgMouthRef} />
        )}
      </div>
    </div>
  );
}

function FallbackFace({ svgMouthRef }: { svgMouthRef: RefObject<SVGEllipseElement | null> }) {
  return (
    <svg
      viewBox="0 0 300 440"
      className="relative"
      style={{ height: "80vh", maxHeight: "880px", filter: "drop-shadow(0 0 26px rgba(34,211,238,.3))" }}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="hair" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#67e8f9" />
          <stop offset="0.5" stopColor="#22d3ee" />
          <stop offset="1" stopColor="#e879f9" />
        </linearGradient>
        <linearGradient id="skin" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#12314a" />
          <stop offset="1" stopColor="#0a1a2e" />
        </linearGradient>
        <radialGradient id="core" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#a5f3fc" />
          <stop offset="0.4" stopColor="#22d3ee" />
          <stop offset="1" stopColor="transparent" />
        </radialGradient>
      </defs>

      {/* hombros / chaqueta */}
      <path d="M40 440 Q60 320 110 300 L190 300 Q240 320 260 440 Z" fill="#0b1830" stroke="#22d3ee" strokeWidth="1.4" opacity="0.9" />
      <path d="M150 300 L150 440" stroke="#22d3ee" strokeWidth="1" opacity="0.5" />
      {/* núcleo del pecho */}
      <circle cx="150" cy="360" r="26" fill="url(#core)" opacity="0.9" />
      <circle cx="150" cy="360" r="10" fill="#e0fbff" />

      {/* cuello */}
      <path d="M128 300 Q128 268 150 262 Q172 268 172 300 Z" fill="url(#skin)" stroke="#22d3ee" strokeWidth="1" />

      {/* cabello atrás */}
      <path d="M92 150 Q70 250 96 300 Q120 250 118 170 Z" fill="url(#hair)" opacity="0.55" />
      <path d="M208 150 Q230 250 204 300 Q180 250 182 170 Z" fill="url(#hair)" opacity="0.55" />

      {/* rostro */}
      <path d="M150 70 Q206 74 206 160 Q206 230 150 262 Q94 230 94 160 Q94 74 150 70 Z" fill="url(#skin)" stroke="#22d3ee" strokeWidth="1.6" />

      {/* mechones frontales neón */}
      <path d="M150 62 Q96 62 92 150 Q112 120 132 118 Q120 90 150 80 Q180 90 168 118 Q188 120 208 150 Q204 62 150 62 Z" fill="url(#hair)" />
      <path d="M96 150 Q104 210 120 250" stroke="#e879f9" strokeWidth="2" fill="none" opacity="0.8" />
      <path d="M204 150 Q196 210 180 250" stroke="#22d3ee" strokeWidth="2" fill="none" opacity="0.8" />

      {/* ojos */}
      <g>
        <path d="M112 168 Q126 158 140 168 Q126 178 112 168 Z" fill="#0a1a2e" />
        <path d="M160 168 Q174 158 188 168 Q174 178 160 168 Z" fill="#0a1a2e" />
        <circle cx="126" cy="168" r="4.5" fill="#67e8f9" style={{ filter: "drop-shadow(0 0 5px #22d3ee)" }} />
        <circle cx="174" cy="168" r="4.5" fill="#67e8f9" style={{ filter: "drop-shadow(0 0 5px #22d3ee)" }} />
        <path d="M110 158 Q126 150 142 158" stroke="#e879f9" strokeWidth="1.6" fill="none" opacity="0.8" />
        <path d="M158 158 Q174 150 190 158" stroke="#e879f9" strokeWidth="1.6" fill="none" opacity="0.8" />
      </g>

      {/* nariz */}
      <path d="M150 176 L146 200 Q150 204 154 200 Z" fill="none" stroke="#22d3ee" strokeWidth="1.2" opacity="0.7" />

      {/* boca animada */}
      <ellipse ref={svgMouthRef} cx="150" cy="222" rx="15" ry="2.5" fill="#22d3ee" />
      <path d="M133 222 Q150 214 167 222" stroke="#e879f9" strokeWidth="1.2" fill="none" opacity="0.7" />

      {/* circuitos en mejilla/cuello */}
      <path d="M186 190 L206 190 L214 200 M150 262 L150 250 M120 240 L108 252" stroke="#22d3ee" strokeWidth="1" fill="none" opacity="0.6" />
      <circle cx="206" cy="190" r="2" fill="#e879f9" />
      <circle cx="214" cy="200" r="1.5" fill="#22d3ee" />
    </svg>
  );
}
