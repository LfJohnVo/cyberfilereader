# Avatar de la asistente

Por defecto se muestra un rostro **SVG** cyber (con boca animada real).

## Usar tu propia imagen (la mujer del mockup)

1. Guarda tu imagen como **`frontend/public/avatar.png`** (PNG con fondo transparente
   funciona mejor; también sirve JPG renombrado a `.png`).
2. Recarga la app: el avatar usará tu foto automáticamente, con una **boca luminosa
   superpuesta** que se anima al hablar.
3. Ajusta la posición de la boca a tu foto en `frontend/src/index.css` añadiendo a `:root`:

   ```css
   :root {
     --mouth-x: 50%;  /* horizontal sobre la imagen */
     --mouth-y: 63%;  /* vertical: baja el % si la boca queda arriba */
   }
   ```

   (o edita los valores por defecto en `src/components/Avatar.tsx`).

> El lip-sync es un movimiento sincronizado con el texto y la voz (no fonémico).
> Para animación fonética real necesitarías un avatar riggeado o un servicio de talking-head.
