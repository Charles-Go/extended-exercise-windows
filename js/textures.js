// ---------------------------------------------------------------------------
// Textures procédurales (canvas) — parquet de Versailles, pierre, marbre…
// ---------------------------------------------------------------------------
import * as THREE from "three";

function canvas(size) {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  return [c, c.getContext("2d")];
}

function tex(c, repeat = 1) {
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat, repeat);
  t.anisotropy = 8;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

const rnd = (() => { let s = 42; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();

function woodStrip(ctx, x, y, w, h, base, vertGrain) {
  const l = 0.86 + rnd() * 0.30;
  ctx.fillStyle = shade(base, l);
  ctx.fillRect(x, y, w, h);
  ctx.strokeStyle = "rgba(60,35,15,0.35)";
  ctx.lineWidth = 1;
  ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
  // veinage
  ctx.strokeStyle = "rgba(80,48,20,0.18)";
  const n = 3 + Math.floor(rnd() * 4);
  for (let i = 0; i < n; i++) {
    ctx.beginPath();
    if (vertGrain) {
      const gx = x + rnd() * w;
      ctx.moveTo(gx, y);
      ctx.bezierCurveTo(gx + 3 - rnd() * 6, y + h * 0.3, gx + 3 - rnd() * 6, y + h * 0.7, gx + 2 - rnd() * 4, y + h);
    } else {
      const gy = y + rnd() * h;
      ctx.moveTo(x, gy);
      ctx.bezierCurveTo(x + w * 0.3, gy + 3 - rnd() * 6, x + w * 0.7, gy + 3 - rnd() * 6, x + w, gy + 2 - rnd() * 4);
    }
    ctx.stroke();
  }
}

function shade([r, g, b], l) {
  return `rgb(${Math.min(255, r * l) | 0},${Math.min(255, g * l) | 0},${Math.min(255, b * l) | 0})`;
}

// --- Parquet de Versailles : panneau carré, treillis diagonal sous cadre ----
export function versaillesTexture() {
  const S = 1024;
  const [c, ctx] = canvas(S);
  const OAK = [166, 124, 82];
  const B = 64; // bordure du panneau
  ctx.fillStyle = shade(OAK, 1);
  ctx.fillRect(0, 0, S, S);

  // treillis diagonal (lames à 45°) dans le champ central
  ctx.save();
  ctx.beginPath();
  ctx.rect(B, B, S - 2 * B, S - 2 * B);
  ctx.clip();
  ctx.translate(S / 2, S / 2);
  ctx.rotate(Math.PI / 4);
  const lw = 88; // largeur de lame
  for (let i = -14; i <= 14; i++) {
    for (let j = -14; j <= 14; j++) {
      if ((i + j) % 2 === 0)
        woodStrip(ctx, i * lw, j * lw * 3, lw, lw * 3, OAK, true);
      else
        woodStrip(ctx, i * lw, j * lw * 3, lw, lw * 3, OAK, true);
    }
  }
  // entrelacs : bandes croisées
  ctx.globalAlpha = 0.95;
  for (let k = -8; k <= 8; k++) {
    woodStrip(ctx, k * lw * 3 + lw, -S, lw, 2 * S, OAK, true);
  }
  ctx.rotate(Math.PI / 2);
  for (let k = -8; k <= 8; k++) {
    if ((k & 1) === 0) woodStrip(ctx, k * lw * 3 + lw, -S, lw, 2 * S, OAK, true);
  }
  ctx.globalAlpha = 1;
  ctx.restore();

  // cadre du panneau (frises périphériques avec coupes d'onglet)
  woodStrip(ctx, 0, 0, S, B, OAK, false);
  woodStrip(ctx, 0, S - B, S, B, OAK, false);
  woodStrip(ctx, 0, B, B, S - 2 * B, OAK, true);
  woodStrip(ctx, S - B, B, B, S - 2 * B, OAK, true);
  ctx.strokeStyle = "rgba(50,28,10,0.55)";
  ctx.lineWidth = 3;
  ctx.strokeRect(B, B, S - 2 * B, S - 2 * B);
  ctx.strokeRect(1.5, 1.5, S - 3, S - 3);
  // onglets
  ctx.beginPath();
  ctx.moveTo(0, 0); ctx.lineTo(B, B);
  ctx.moveTo(S, 0); ctx.lineTo(S - B, B);
  ctx.moveTo(0, S); ctx.lineTo(B, S - B);
  ctx.moveTo(S, S); ctx.lineTo(S - B, S - B);
  ctx.lineWidth = 2;
  ctx.stroke();
  // patine
  const g = ctx.createRadialGradient(S / 2, S / 2, S * 0.2, S / 2, S / 2, S * 0.75);
  g.addColorStop(0, "rgba(255,235,200,0.06)");
  g.addColorStop(1, "rgba(60,30,5,0.12)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, S, S);
  return tex(c);
}

// --- Parquet à lames droites ------------------------------------------------
export function plankTexture() {
  const S = 512;
  const [c, ctx] = canvas(S);
  const OAK = [172, 132, 92];
  const pw = S / 6;
  for (let i = 0; i < 6; i++) {
    let y = -((i * 137) % 200);
    while (y < S) {
      const h = 150 + rnd() * 120;
      woodStrip(ctx, i * pw, y, pw, h, OAK, true);
      y += h;
    }
  }
  return tex(c, 2);
}

// --- Dallage pierre ----------------------------------------------------------
export function stoneTexture(cabochon = false) {
  const S = 512;
  const [c, ctx] = canvas(S);
  const n = 4, q = S / n;
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) {
      const l = 0.92 + rnd() * 0.13;
      ctx.fillStyle = shade([214, 206, 192], l);
      ctx.fillRect(i * q, j * q, q, q);
      ctx.strokeStyle = "rgba(120,112,100,0.6)";
      ctx.lineWidth = 2;
      ctx.strokeRect(i * q + 1, j * q + 1, q - 2, q - 2);
      // moucheture
      ctx.fillStyle = "rgba(150,140,125,0.25)";
      for (let k = 0; k < 60; k++)
        ctx.fillRect(i * q + rnd() * q, j * q + rnd() * q, 1.5, 1.5);
      if (cabochon) {
        ctx.save();
        ctx.translate(i * q, j * q);
        ctx.fillStyle = "#2b2b30";
        ctx.beginPath();
        const s = q * 0.16;
        ctx.moveTo(0, -s); ctx.lineTo(s, 0); ctx.lineTo(0, s); ctx.lineTo(-s, 0);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      }
    }
  if (cabochon) {
    // cabochons aux angles bas/droite pour boucler la répétition
    ctx.fillStyle = "#2b2b30";
    for (let i = 0; i <= n; i++)
      for (let j = 0; j <= n; j++) {
        ctx.save();
        ctx.translate(i * q, j * q);
        const s = q * 0.16;
        ctx.beginPath();
        ctx.moveTo(0, -s); ctx.lineTo(s, 0); ctx.lineTo(0, s); ctx.lineTo(-s, 0);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      }
  }
  return tex(c, 2);
}

// --- Marbre -------------------------------------------------------------------
export function marbleTexture(base = [232, 230, 226], vein = "rgba(120,125,135,0.35)") {
  const S = 512;
  const [c, ctx] = canvas(S);
  ctx.fillStyle = shade(base, 1);
  ctx.fillRect(0, 0, S, S);
  for (let v = 0; v < 22; v++) {
    ctx.strokeStyle = vein;
    ctx.lineWidth = 0.5 + rnd() * 2.2;
    ctx.beginPath();
    let x = rnd() * S, y = rnd() * S;
    ctx.moveTo(x, y);
    for (let s = 0; s < 6; s++) {
      x += (rnd() - 0.4) * 140;
      y += (rnd() - 0.4) * 140;
      ctx.quadraticCurveTo(x + (rnd() - 0.5) * 60, y + (rnd() - 0.5) * 60, x, y);
    }
    ctx.stroke();
  }
  const g = ctx.createLinearGradient(0, 0, S, S);
  g.addColorStop(0, "rgba(255,255,255,0.10)");
  g.addColorStop(1, "rgba(180,180,190,0.10)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, S, S);
  return tex(c, 2);
}

// --- Carrelage ------------------------------------------------------------------
export function tileTexture() {
  const S = 512;
  const [c, ctx] = canvas(S);
  const n = 8, q = S / n;
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) {
      ctx.fillStyle = shade([225, 228, 228], 0.94 + rnd() * 0.09);
      ctx.fillRect(i * q, j * q, q - 2, q - 2);
    }
  ctx.strokeStyle = "rgba(150,150,150,0.8)";
  for (let i = 0; i <= n; i++) {
    ctx.beginPath(); ctx.moveTo(i * q, 0); ctx.lineTo(i * q, S); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, i * q); ctx.lineTo(S, i * q); ctx.stroke();
  }
  return tex(c, 2);
}

// --- Plâtre / murs -----------------------------------------------------------------
export function plasterTexture(base = [240, 236, 226]) {
  const S = 256;
  const [c, ctx] = canvas(S);
  ctx.fillStyle = shade(base, 1);
  ctx.fillRect(0, 0, S, S);
  for (let k = 0; k < 2200; k++) {
    ctx.fillStyle = `rgba(${180 + rnd() * 60 | 0},${175 + rnd() * 55 | 0},${160 + rnd() * 50 | 0},0.05)`;
    ctx.fillRect(rnd() * S, rnd() * S, 2, 2);
  }
  return tex(c, 4);
}

// --- Tapis -----------------------------------------------------------------------
export function rugTexture() {
  const S = 512;
  const [c, ctx] = canvas(S);
  ctx.fillStyle = "#7d2f33";
  ctx.fillRect(0, 0, S, S);
  ctx.strokeStyle = "#caa86a";
  ctx.lineWidth = 10;
  ctx.strokeRect(18, 18, S - 36, S - 36);
  ctx.lineWidth = 4;
  ctx.strokeRect(44, 44, S - 88, S - 88);
  ctx.fillStyle = "rgba(202,168,106,0.55)";
  for (let i = 0; i < 8; i++)
    for (let j = 0; j < 8; j++) {
      ctx.save();
      ctx.translate(64 + i * 55, 64 + j * 55);
      ctx.rotate(Math.PI / 4);
      ctx.fillRect(-9, -9, 18, 18);
      ctx.restore();
    }
  const t = tex(c, 1);
  t.repeat.set(1, 1);
  return t;
}

export function makeMaterials() {
  const M = {};
  M.versailles = new THREE.MeshStandardMaterial({ map: versaillesTexture(), roughness: 0.55, metalness: 0.05 });
  M.plank      = new THREE.MeshStandardMaterial({ map: plankTexture(), roughness: 0.6 });
  M.stone      = new THREE.MeshStandardMaterial({ map: stoneTexture(false), roughness: 0.85 });
  M.stoneCab   = new THREE.MeshStandardMaterial({ map: stoneTexture(true), roughness: 0.8 });
  M.marble     = new THREE.MeshStandardMaterial({ map: marbleTexture(), roughness: 0.25 });
  M.tile       = new THREE.MeshStandardMaterial({ map: tileTexture(), roughness: 0.4 });
  M.wall       = new THREE.MeshStandardMaterial({ map: plasterTexture(), roughness: 0.92 });
  M.wallExt    = new THREE.MeshStandardMaterial({ map: plasterTexture([214, 204, 184]), roughness: 0.95 });
  M.ceiling    = new THREE.MeshStandardMaterial({ color: 0xf7f4ec, roughness: 0.95 });
  M.trim       = new THREE.MeshStandardMaterial({ color: 0xf2eee2, roughness: 0.7 });
  M.doorWood   = new THREE.MeshStandardMaterial({ color: 0xefebdd, roughness: 0.5 });
  M.darkWood   = new THREE.MeshStandardMaterial({ color: 0x5a3d26, roughness: 0.55 });
  M.glass      = new THREE.MeshPhysicalMaterial({ color: 0xcfe6f0, transmission: 0.92, transparent: true, opacity: 0.35, roughness: 0.05, ior: 1.45, thickness: 0.01, side: THREE.DoubleSide });
  M.iron       = new THREE.MeshStandardMaterial({ color: 0x22252a, roughness: 0.5, metalness: 0.8 });
  M.brass      = new THREE.MeshStandardMaterial({ color: 0xb8923e, roughness: 0.3, metalness: 0.9 });
  M.marbleFire = new THREE.MeshStandardMaterial({ map: marbleTexture([225, 222, 220], "rgba(90,90,100,0.5)"), roughness: 0.2 });
  M.mirror     = new THREE.MeshStandardMaterial({ color: 0x9fb2bc, roughness: 0.22, metalness: 0.85 });
  M.fabricA    = new THREE.MeshStandardMaterial({ color: 0x8a97a8, roughness: 0.95 });
  M.fabricB    = new THREE.MeshStandardMaterial({ color: 0xc9bfa8, roughness: 0.95 });
  M.fabricC    = new THREE.MeshStandardMaterial({ color: 0x6e7d6a, roughness: 0.95 });
  M.linen      = new THREE.MeshStandardMaterial({ color: 0xf0ece2, roughness: 0.95 });
  M.counter    = new THREE.MeshStandardMaterial({ map: marbleTexture([210, 208, 204], "rgba(70,70,80,0.5)"), roughness: 0.3 });
  M.kitchen    = new THREE.MeshStandardMaterial({ color: 0x39424d, roughness: 0.6 });
  M.appliance  = new THREE.MeshStandardMaterial({ color: 0xd8dadc, roughness: 0.35, metalness: 0.6 });
  M.rug        = new THREE.MeshStandardMaterial({ map: rugTexture(), roughness: 1 });
  M.paper      = new THREE.MeshStandardMaterial({ color: 0xdfe4e6, roughness: 0.9 });
  M.gold       = new THREE.MeshStandardMaterial({ color: 0xc9a227, roughness: 0.35, metalness: 0.85 });
  return M;
}
