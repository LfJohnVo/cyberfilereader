import type { ComponentType, LazyExoticComponent } from "react";

/**
 * Un avatar es autónomo: lee `useAgentStore` (estado + talking) por su cuenta y reacciona.
 * `kind` decide cómo lo monta la escena:
 *   - "webgl": es un conjunto de elementos R3F, se monta DENTRO del <Canvas> compartido.
 *   - "dom":   es un componente React 2D normal, se monta SIN <Canvas> (sin WebGL).
 */
export interface AvatarDescriptor {
  id: string;
  label: string;
  kind: "webgl" | "dom";
  component: LazyExoticComponent<ComponentType>;
}
