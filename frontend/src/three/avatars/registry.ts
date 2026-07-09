import { lazy } from "react";
import type { AvatarDescriptor } from "./types";

/** Registro de avatares. `lazy(import)` => cada avatar es un chunk aparte (code-splitting):
 *  el navegador solo descarga el que está seleccionado. Añadir uno = una línea aquí. */
export const AVATARS: AvatarDescriptor[] = [
  { id: "nexus", label: "Núcleo Nexus", kind: "webgl", component: lazy(() => import("./NexusCore")) },
  { id: "orbe", label: "Orbe de plasma", kind: "webgl", component: lazy(() => import("./Orbe")) },
  { id: "helix", label: "Hélice de datos", kind: "webgl", component: lazy(() => import("./Helix")) },
  { id: "onda", label: "Onda (2D, sin WebGL)", kind: "dom", component: lazy(() => import("./Onda")) },
];

export const DEFAULT_AVATAR = "nexus";

export const avatarById = (id: string): AvatarDescriptor =>
  AVATARS.find((a) => a.id === id) ?? AVATARS[0];
