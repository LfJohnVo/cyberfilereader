/**
 * Polyfill de `crypto.randomUUID` para CONTEXTOS NO SEGUROS (HTTP plano en LAN).
 *
 * `crypto.randomUUID` (igual que `crypto.subtle`) solo existe en un "secure
 * context": páginas HTTPS o http://localhost. Cuando la app se sirve por HTTP
 * a una IP de la red (p. ej. http://192.168.40.1:5000), `crypto.randomUUID`
 * es `undefined` y la primera llamada lanza `TypeError`, tumbando toda la app
 * antes de montar React (pantalla en blanco).
 *
 * `crypto.getRandomValues`, en cambio, SÍ está disponible sobre HTTP, así que
 * generamos un UUID v4 (RFC 4122) con él. Este módulo debe importarse ANTES que
 * cualquier otro para blindar también a dependencias que llamen a randomUUID.
 */
function uuidv4(): string {
  const b = new Uint8Array(16);
  crypto.getRandomValues(b);
  b[6] = (b[6] & 0x0f) | 0x40; // versión 4
  b[8] = (b[8] & 0x3f) | 0x80; // variante RFC 4122
  const h: string[] = [];
  for (let i = 0; i < 16; i++) h.push(b[i].toString(16).padStart(2, "0"));
  return `${h[0]}${h[1]}${h[2]}${h[3]}-${h[4]}${h[5]}-${h[6]}${h[7]}-${h[8]}${h[9]}-${h[10]}${h[11]}${h[12]}${h[13]}${h[14]}${h[15]}`;
}

if (typeof crypto !== "undefined" && typeof crypto.randomUUID !== "function") {
  try {
    // `crypto` puede ser de solo lectura; defineProperty es la vía más segura.
    Object.defineProperty(crypto, "randomUUID", {
      value: uuidv4,
      configurable: true,
      writable: true,
    });
  } catch {
    // Si ni siquiera se puede redefinir, no rompemos nada: el código propio usa
    // `newId()` (nanoid), que no depende de este polyfill.
  }
}
