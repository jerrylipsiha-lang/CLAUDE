#!/usr/bin/env node
// Генератор иконок приложения. Рисует две перекрывающиеся «головы» (Будько и Позов)
// в виде кругов на тёплом фоне и кодирует результат в PNG без внешних зависимостей.
const zlib = require('zlib');
const fs = require('fs');
const path = require('path');

function rgba(r, g, b, a = 255) { return [r, g, b, a]; }

// --- минимальный кодировщик PNG (8-бит, RGBA, color type 6) ---
const CRC_TABLE = (() => {
  const t = new Int32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c;
  }
  return t;
})();
function crc32(buf) {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
function chunk(type, data) {
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length, 0);
  const typeBuf = Buffer.from(type, 'ascii');
  const body = Buffer.concat([typeBuf, data]);
  const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(body), 0);
  return Buffer.concat([len, body, crc]);
}
function encodePNG(width, height, pixels) {
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  const raw = Buffer.alloc(height * (width * 4 + 1));
  for (let y = 0; y < height; y++) {
    raw[y * (width * 4 + 1)] = 0; // filter: none
    for (let x = 0; x < width; x++) {
      const i = (y * width + x) * 4;
      const o = y * (width * 4 + 1) + 1 + x * 4;
      raw[o] = pixels[i]; raw[o + 1] = pixels[i + 1];
      raw[o + 2] = pixels[i + 2]; raw[o + 3] = pixels[i + 3];
    }
  }
  const idat = zlib.deflateSync(raw, { level: 9 });
  return Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', idat), chunk('IEND', Buffer.alloc(0))]);
}

function lerp(a, b, t) { return a + (b - a) * t; }

function drawIcon(size, { maskable = false } = {}) {
  const px = new Uint8ClampedArray(size * size * 4);
  const cx = size / 2, cy = size / 2;
  // палитра
  const bgTop = rgba(43, 34, 28);      // тёплый тёмно-коричневый
  const bgBot = rgba(28, 22, 18);
  const budko = rgba(124, 152, 74);    // деревенский хаки-зелёный
  const pozov = rgba(86, 110, 140);    // городской сине-серый
  const ring = rgba(244, 241, 234);    // кремовый контур
  const inset = maskable ? size * 0.16 : 0; // запас для maskable

  const headR = (size - inset * 2) * 0.27;
  const cyH = cy + (size - inset * 2) * 0.02;
  const budkoC = { x: cx - headR * 0.62, y: cyH };
  const pozovC = { x: cx + headR * 0.62, y: cyH };

  function dist(ax, ay, bx, by) { return Math.hypot(ax - bx, ay - by); }

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const i = (y * size + x) * 4;
      // фон-градиент
      const t = y / size;
      let r = lerp(bgTop[0], bgBot[0], t);
      let g = lerp(bgTop[1], bgBot[1], t);
      let b = lerp(bgTop[2], bgBot[2], t);

      // Позов (рисуем первым — он сзади справа)
      const dP = dist(x, y, pozovC.x, pozovC.y);
      if (dP < headR + 3) {
        if (dP > headR - 1) { const a = Math.max(0, 1 - Math.abs(dP - headR) / 3); r = lerp(r, ring[0], a); g = lerp(g, ring[1], a); b = lerp(b, ring[2], a); }
        if (dP < headR) { r = pozov[0]; g = pozov[1]; b = pozov[2]; }
      }
      // Будько (спереди слева, перекрывает)
      const dB = dist(x, y, budkoC.x, budkoC.y);
      if (dB < headR + 3) {
        if (dB > headR - 1) { const a = Math.max(0, 1 - Math.abs(dB - headR) / 3); r = lerp(r, ring[0], a); g = lerp(g, ring[1], a); b = lerp(b, ring[2], a); }
        if (dB < headR) { r = budko[0]; g = budko[1]; b = budko[2]; }
      }

      px[i] = r; px[i + 1] = g; px[i + 2] = b; px[i + 3] = 255;
    }
  }
  return encodePNG(size, size, px);
}

const outDir = path.join(__dirname, 'icons');
fs.writeFileSync(path.join(outDir, 'icon-192.png'), drawIcon(192));
fs.writeFileSync(path.join(outDir, 'icon-512.png'), drawIcon(512));
fs.writeFileSync(path.join(outDir, 'icon-maskable-512.png'), drawIcon(512, { maskable: true }));
fs.writeFileSync(path.join(outDir, 'apple-touch-icon.png'), drawIcon(180));
console.log('Иконки сгенерированы в', outDir);
