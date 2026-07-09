// Polyfill de crypto.randomUUID para contextos no seguros (HTTP en LAN): randomUUID solo existe en secure context.
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
    // crypto puede ser de solo lectura; defineProperty es la vía más segura.
    Object.defineProperty(crypto, "randomUUID", {
      value: uuidv4,
      configurable: true,
      writable: true,
    });
  } catch {
    // no rompemos nada: el código propio usa newId() (nanoid).
  }
}
