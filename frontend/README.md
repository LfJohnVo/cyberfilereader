# SGI-Agent · Frontend

Interfaz conversacional de **SGI-Agent**: chat sobre la documentación del Sistema de Gestión
Integral con **núcleo 3D interactivo y avatares intercambiables**. Construida con **React 19 +
TypeScript + Vite**, **React Three Fiber** (Three.js) para el núcleo 3D, **Tailwind CSS** para el
estilo y **Zustand** para el estado.

## Scripts

```bash
npm install
npm run dev       # servidor de desarrollo (http://localhost:5173)
npm run build     # type-check (tsc -b) + build de producción (Vite)
npm run preview   # sirve el build de producción localmente
npm run lint      # Oxlint
```

## Configuración

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `VITE_API_URL` | `http://localhost:5001` | Base de la API del backend. Vacía en el build Docker (se sirve tras el proxy nginx). |

## Avatares

El núcleo 3D admite avatares intercambiables desde el selector de la interfaz. Cada avatar es un
módulo con carga diferida (`React.lazy`) registrado en `src/three/avatars/registry.ts`; puede ser
`webgl` (dentro del `<Canvas>` de React Three Fiber) o `dom` (2D, sin WebGL, como respaldo para
equipos sin GPU). La selección se persiste en el navegador.
