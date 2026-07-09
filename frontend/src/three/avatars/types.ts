import type { ComponentType, LazyExoticComponent } from "react";

// "webgl" se monta dentro del <Canvas> compartido; "dom" se monta sin WebGL.
export interface AvatarDescriptor {
  id: string;
  label: string;
  kind: "webgl" | "dom";
  component: LazyExoticComponent<ComponentType>;
}
