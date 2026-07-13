import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { type ComplianceResult, checkCompliance, getAreas } from "../lib/api";

const VERDICT_STYLE: Record<string, string> = {
  cumple: "border-emerald-400/70 text-emerald-200 bg-emerald-500/10",
  parcial: "border-amber-400/70 text-amber-200 bg-amber-500/10",
  no_cumple: "border-rose-400/70 text-rose-200 bg-rose-500/10",
  indeterminado: "border-cyan-400/70 text-cyan-200 bg-cyan-500/10",
};

export default function ComplianceModal() {
  const [open, setOpen] = useState(false);
  const [areas, setAreas] = useState<string[]>([]);
  const [area, setArea] = useState("*");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ComplianceResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAreas()
      .then((r) => setAreas(r.areas ?? []))
      .catch(() => {});
  }, []);

  const run = async () => {
    if (!file || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await checkCompliance(file, area));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <aside className="neon neon-mag clip-hud pointer-events-auto w-[248px] p-3 font-mono text-[11px]">
        <h2 className="glow mb-2 tracking-[0.25em] text-fuchsia-300">CUMPLIMIENTO</h2>
        <p className="mb-2 text-cyan-500/70">
          Sube un documento y verifica si cumple con las políticas/ISO del SGI.
        </p>
        <button
          onClick={() => setOpen(true)}
          className="clip-hud w-full border border-fuchsia-500/60 bg-fuchsia-500/10 px-2 py-1 tracking-widest text-fuchsia-100 hover:bg-fuchsia-500/20"
        >
          ⧉ VERIFICAR ARCHIVO
        </button>
      </aside>

      {open &&
        createPortal(
          <div
            className="pointer-events-auto fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 font-mono"
            onClick={() => setOpen(false)}
          >
          <div
            className="neon clip-hud flex max-h-[86vh] w-full max-w-2xl flex-col p-5 text-sm"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between">
              <h3 className="glow tracking-[0.2em] text-cyan-300">VERIFICACIÓN DE CUMPLIMIENTO</h3>
              <button onClick={() => setOpen(false)} className="text-cyan-400 hover:text-cyan-200">
                ✕
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-3 border-b border-cyan-500/20 pb-3 text-xs">
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md,.xlsx,.csv"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="text-cyan-100 file:mr-2 file:border file:border-cyan-500/50 file:bg-black/50 file:px-2 file:py-1 file:text-cyan-200"
              />
              <select
                value={area}
                onChange={(e) => setArea(e.target.value)}
                className="border border-fuchsia-500/40 bg-black/50 px-2 py-1 text-fuchsia-200 outline-none"
              >
                <option value="*" className="bg-[#0a0f1e]">
                  Todas las áreas / ISO
                </option>
                {areas.map((a) => (
                  <option key={a} value={a} className="bg-[#0a0f1e]">
                    {a}
                  </option>
                ))}
              </select>
              <button
                onClick={run}
                disabled={!file || loading}
                className="clip-hud border border-emerald-400/70 bg-emerald-500/10 px-4 py-1 tracking-widest text-emerald-200 hover:bg-emerald-500/20 disabled:opacity-40"
              >
                {loading ? "EVALUANDO…" : "EVALUAR"}
              </button>
            </div>

            <div className="mt-3 min-h-0 flex-1 overflow-y-auto pr-2">
              {loading && (
                <p className="animate-pulse text-cyan-400/80">
                  ◈ Analizando el documento contra los requisitos del SGI…
                </p>
              )}
              {error && <p className="text-rose-300">Error: {error}</p>}
              {result && (
                <div>
                  <p
                    className={`clip-hud mb-3 inline-block border px-3 py-1 tracking-widest ${VERDICT_STYLE[result.verdict] ?? VERDICT_STYLE.indeterminado}`}
                  >
                    VEREDICTO: {result.verdict.replace("_", " ").toUpperCase()}
                  </p>
                  <p className="whitespace-pre-wrap leading-relaxed text-[#e0f7ff]">{result.report}</p>
                  {result.sources.length > 0 && (
                    <div className="mt-4 border-t border-cyan-500/20 pt-2 text-[11px] text-cyan-300/80">
                      <p className="mb-1 tracking-widest text-fuchsia-300">REQUISITOS CONSULTADOS</p>
                      {result.sources.map((sourc) => (
                        <p key={sourc.n}>
                          [{sourc.n}] {sourc.file_name} · área {sourc.area}
                          {sourc.page ? ` · pág. ${sourc.page}` : ""}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {!loading && !result && !error && (
                <p className="text-cyan-600">
                  Elige un archivo (PDF/DOCX/TXT/XLSX/CSV) y el área o ISO contra la que evaluar, y
                  pulsa EVALUAR. La asistente comparará tu documento con los requisitos del SGI y te
                  dirá si cumple, con recomendaciones y citas.
                </p>
              )}
            </div>
          </div>
          </div>,
          document.body,
        )}
    </>
  );
}
