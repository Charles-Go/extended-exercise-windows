// ---------------------------------------------------------------------------
// Mobilier procédural et luminaires
// ---------------------------------------------------------------------------
import * as THREE from "three";
import { LIGHTS, ROOMS } from "./data.js";

const BOX = new THREE.BoxGeometry(1, 1, 1);
const CYL = new THREE.CylinderGeometry(0.5, 0.5, 1, 20);

function box(p, mat, w, h, d, x, y, z, ry = 0) {
  const m = new THREE.Mesh(BOX, mat);
  m.scale.set(w, h, d); m.position.set(x, y, z); m.rotation.y = ry;
  m.castShadow = m.receiveShadow = true;
  p.add(m); return m;
}
function cyl(p, mat, r, h, x, y, z, r2) {
  const m = new THREE.Mesh(CYL, mat);
  m.scale.set(r * 2, h, (r2 ?? r) * 2); m.position.set(x, y, z);
  m.castShadow = m.receiveShadow = true;
  p.add(m); return m;
}

function sofa(p, M, x, z, ry, len = 2.2) {
  const g = new THREE.Group();
  box(g, M.fabricA, len, 0.42, 0.9, 0, 0.21, 0);
  box(g, M.fabricA, len, 0.5, 0.22, 0, 0.62, -0.34);
  box(g, M.fabricA, 0.22, 0.32, 0.9, -len / 2 + 0.11, 0.55, 0);
  box(g, M.fabricA, 0.22, 0.32, 0.9, len / 2 - 0.11, 0.55, 0);
  for (const c of [-1, 1]) box(g, M.linen, len / 2 - 0.26, 0.14, 0.62, c * (len / 4 - 0.05), 0.49, 0.06);
  g.position.set(x, 0, z); g.rotation.y = ry; p.add(g);
}

function fauteuil(p, M, x, z, ry, mat) {
  const g = new THREE.Group();
  box(g, mat, 0.62, 0.38, 0.6, 0, 0.19, 0);
  box(g, mat, 0.62, 0.5, 0.14, 0, 0.6, -0.23);
  box(g, mat, 0.12, 0.24, 0.55, -0.25, 0.5, 0);
  box(g, mat, 0.12, 0.24, 0.55, 0.25, 0.5, 0);
  g.position.set(x, 0, z); g.rotation.y = ry; p.add(g);
}

function chair(p, M, x, z, ry) {
  const g = new THREE.Group();
  box(g, M.fabricB, 0.45, 0.05, 0.45, 0, 0.46, 0);
  box(g, M.darkWood, 0.42, 0.5, 0.05, 0, 0.75, -0.2);
  for (const [dx, dz] of [[-0.19, -0.19], [0.19, -0.19], [-0.19, 0.19], [0.19, 0.19]])
    box(g, M.darkWood, 0.04, 0.46, 0.04, dx, 0.23, dz);
  g.position.set(x, 0, z); g.rotation.y = ry; p.add(g);
}

function table(p, M, x, z, w, d, h = 0.75, mat) {
  const g = new THREE.Group();
  box(g, mat, w, 0.05, d, 0, h - 0.025, 0);
  for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]])
    box(g, mat, 0.07, h - 0.05, 0.07, sx * (w / 2 - 0.08), (h - 0.05) / 2, sz * (d / 2 - 0.08));
  g.position.set(x, 0, z); p.add(g);
}

function bed(p, M, x, z, ry, w = 1.8) {
  const g = new THREE.Group();
  box(g, M.darkWood, w + 0.1, 0.3, 2.1, 0, 0.18, 0);
  box(g, M.linen, w, 0.25, 2.0, 0, 0.42, 0);
  box(g, M.fabricB, w, 0.12, 0.6, 0, 0.55, -0.65);
  box(g, M.darkWood, w + 0.1, 1.1, 0.08, 0, 0.6, -1.06);
  for (const s of [-1, 1]) box(g, M.linen, 0.6, 0.15, 0.4, s * (w / 4 + 0.05), 0.62, -0.75);
  g.position.set(x, 0, z); g.rotation.y = ry; p.add(g);
  return g;
}

function nightstand(p, M, x, z) {
  box(p, M.darkWood, 0.45, 0.55, 0.38, x, 0.275, z);
  cyl(p, M.brass, 0.02, 0.3, x, 0.7, z);
  const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.16, 0.16, 16, 1, true), M.linen);
  sh.position.set(x, 0.92, z); p.add(sh);
}

function wardrobe(p, M, x, z, w, ry = 0) {
  const g = new THREE.Group();
  box(g, M.doorWood, w, 2.6, 0.6, 0, 1.3, 0);
  const n = Math.round(w / 0.55);
  for (let i = 0; i < n; i++) {
    const px = -w / 2 + (i + 0.5) * (w / n);
    box(g, M.trim, w / n - 0.06, 2.45, 0.02, px, 1.3, 0.31);
    box(g, M.brass, 0.02, 0.12, 0.02, px + w / n / 2 - 0.08, 1.3, 0.34);
  }
  g.position.set(x, 0, z); g.rotation.y = ry; p.add(g);
}

function bathtub(p, M, x, z, ry) {
  const g = new THREE.Group();
  box(g, M.marble, 1.8, 0.58, 0.8, 0, 0.29, 0);
  const inner = new THREE.Mesh(BOX, new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.1 }));
  inner.scale.set(1.6, 0.1, 0.62); inner.position.set(0, 0.55, 0); g.add(inner);
  cyl(g, M.brass, 0.02, 0.35, -0.7, 0.75, 0);
  g.position.set(x, 0, z); g.rotation.y = ry; p.add(g);
}

function vanity(p, M, x, z, ry, w = 1.2) {
  const g = new THREE.Group();
  box(g, M.doorWood, w, 0.82, 0.55, 0, 0.41, 0);
  box(g, M.counter, w + 0.04, 0.04, 0.58, 0, 0.84, 0);
  const b = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.14, 0.12, 24), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.15 }));
  b.position.set(0, 0.92, 0); g.add(b);
  box(g, M.mirror, w * 0.8, 0.9, 0.02, 0, 1.6, -0.25);
  g.position.set(x, 0, z); g.rotation.y = ry; p.add(g);
}

function toilet(p, M, x, z, ry) {
  const g = new THREE.Group();
  const white = new THREE.MeshStandardMaterial({ color: 0xfafafa, roughness: 0.2 });
  box(g, white, 0.38, 0.4, 0.5, 0, 0.2, 0);
  cyl(g, white, 0.2, 0.06, 0, 0.43, 0.1);
  box(g, white, 0.38, 0.3, 0.16, 0, 0.55, -0.2);
  g.position.set(x, 0, z); g.rotation.y = ry; p.add(g);
}

function shower(p, M, x, z) {
  const g = new THREE.Group();
  box(g, M.marble, 0.9, 0.04, 0.9, 0, 0.02, 0);
  const gl = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 2.0), M.glass);
  gl.position.set(0, 1.04, 0.45); g.add(gl);
  cyl(g, M.brass, 0.015, 2.0, -0.4, 1.0, -0.4);
  cyl(g, M.brass, 0.1, 0.02, -0.3, 2.05, -0.3);
  g.position.set(x, 0, z); p.add(g);
}

function bookshelf(p, M, x, z, w, ry) {
  const g = new THREE.Group();
  box(g, M.darkWood, w, 2.8, 0.35, 0, 1.4, 0);
  for (let s = 0; s < 6; s++) {
    box(g, M.trim, w - 0.08, 0.025, 0.3, 0, 0.3 + s * 0.42, 0.02);
    for (let b = 0; b < w / 0.09; b++) {
      const c = new THREE.Color().setHSL((b * 0.13 + s * 0.31) % 1, 0.35, 0.32);
      box(g, new THREE.MeshStandardMaterial({ color: c, roughness: 0.9 }), 0.07, 0.3 + (b % 3) * 0.03, 0.22, -w / 2 + 0.1 + b * 0.09, 0.47 + s * 0.42, 0.02);
    }
  }
  g.position.set(x, 0, z); g.rotation.y = ry; p.add(g);
}

export function buildFurniture(scene, M, colliders) {
  const g = new THREE.Group();
  scene.add(g);
  const solid = (x0, z0, x1, z1) => colliders.push({ x0, z0, x1, z1 });

  // --- Salon (0–4.3 × 0–6.45) -----------------------------------------------
  const rug1 = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 4.2), M.rug);
  rug1.rotation.x = -Math.PI / 2; rug1.position.set(2.15, 0.012, 3.2); rug1.receiveShadow = true; g.add(rug1);
  sofa(g, M, 2.15, 4.9, Math.PI, 2.3);
  sofa(g, M, 3.6, 3.2, -Math.PI / 2, 2.0);
  fauteuil(g, M, 1.0, 2.2, Math.PI / 4, M.fabricC);
  fauteuil(g, M, 2.0, 1.6, 0.2, M.fabricC);
  table(g, M, 2.15, 3.3, 1.1, 0.65, 0.42, M.darkWood);
  table(g, M, 0.6, 4.8, 0.5, 0.5, 0.55, M.darkWood);

  // --- Petit Salon / Salle à Manger (4.7–9.2 × 0–6.45) ------------------------
  table(g, M, 6.95, 3.4, 1.05, 2.6, 0.75, M.darkWood);
  solid(6.3, 2.0, 7.6, 4.8);
  for (const dz of [-0.95, -0.32, 0.32, 0.95]) {
    chair(g, M, 6.3, 3.4 + dz, Math.PI / 2);
    chair(g, M, 7.6, 3.4 + dz, -Math.PI / 2);
  }
  chair(g, M, 6.95, 2.0, 0);
  chair(g, M, 6.95, 4.8, Math.PI);
  box(g, M.darkWood, 1.6, 0.95, 0.45, 5.0, 0.475, 5.9); // console-buffet
  solid(4.7, 5.6, 5.9, 6.2);

  // --- Cuisine (3.49–9.2 × 6.85–10.45) ----------------------------------------
  // plan de travail le long du mur ouest + nord
  box(g, M.kitchen, 0.62, 0.9, 3.0, 3.85, 0.45, 8.6);
  box(g, M.counter, 0.66, 0.04, 3.05, 3.85, 0.92, 8.6);
  solid(3.5, 7.1, 4.2, 10.1);
  box(g, M.kitchen, 2.2, 0.9, 0.62, 5.6, 0.45, 10.05);
  box(g, M.counter, 2.25, 0.04, 0.66, 5.6, 0.92, 10.05);
  solid(4.4, 9.7, 6.8, 10.4);
  // îlot central avec 3 tabourets (plan : 3 assises côté sud)
  box(g, M.kitchen, 2.4, 0.9, 1.0, 6.35, 0.45, 8.55);
  box(g, M.counter, 2.5, 0.05, 1.1, 6.35, 0.925, 8.55);
  solid(5.1, 8.0, 7.6, 9.1);
  for (const dx of [-0.75, 0, 0.75]) {
    cyl(g, M.darkWood, 0.17, 0.66, 6.35 + dx, 0.33, 7.7);
  }
  // réfrigérateur-congélateur encastré (angle nord-est, cf. plan)
  box(g, M.appliance, 0.75, 2.1, 0.68, 8.75, 1.05, 10.0);
  solid(8.3, 9.6, 9.15, 10.4);
  // hotte + crédence
  box(g, M.appliance, 0.9, 0.4, 0.5, 5.6, 2.2, 10.1);

  // --- Bureau (9.6–14.1 × 0–4.3) ----------------------------------------------
  table(g, M, 11.85, 2.0, 1.7, 0.85, 0.75, M.darkWood);
  solid(11.0, 1.55, 12.7, 2.45);
  chair(g, M, 11.85, 2.7, Math.PI);
  fauteuil(g, M, 10.3, 3.5, 2.6, M.fabricC);
  bookshelf(g, M, 13.9, 2.15, 3.4, -Math.PI / 2);
  solid(13.6, 0.4, 14.1, 3.9);

  // --- Chambre 1 (14.5–18.75 × 0–6.41) ------------------------------------------
  bed(g, M, 16.62, 4.6, Math.PI, 1.8);
  solid(15.6, 3.5, 17.6, 5.8);
  nightstand(g, M, 15.45, 5.9);
  nightstand(g, M, 17.8, 5.9);
  box(g, M.fabricB, 1.5, 0.42, 0.5, 16.62, 0.21, 3.1);
  fauteuil(g, M, 18.1, 1.6, -2.2, M.fabricB);

  // --- Chambre 2 (9.4–14.3 × 6.52–10.45) -----------------------------------------
  bed(g, M, 11.4, 7.7, 0, 1.6);
  solid(10.5, 6.6, 12.3, 8.8);
  nightstand(g, M, 10.3, 7.0);
  nightstand(g, M, 12.5, 7.0);
  wardrobe(g, M, 13.95, 8.5, 2.4, -Math.PI / 2);
  solid(13.6, 7.2, 14.3, 9.8);

  // --- SDB 1 (14.5–16.4 × 6.81–9.25) : baignoire + douche ------------------------
  bathtub(g, M, 15.45, 7.35, 0);
  solid(14.55, 6.95, 16.35, 7.8);
  shower(g, M, 15.0, 8.7);
  solid(14.55, 8.25, 15.45, 9.2);
  vanity(g, M, 16.1, 8.5, -Math.PI / 2, 0.9);

  // --- SDB 2 (12.2–14.3 × 4.7–6.12) -----------------------------------------------
  vanity(g, M, 13.6, 5.95, Math.PI, 1.0);
  toilet(g, M, 14.0, 4.95, Math.PI / 2);
  bathtub(g, M, 12.8, 5.0, Math.PI / 2 * 0 + 0); // petite baignoire le long du mur sud
  solid(12.25, 4.75, 13.9, 5.35);

  // --- WC (0–1.1 × 9.05–10.45) ------------------------------------------------------
  toilet(g, M, 0.55, 10.1, Math.PI);
  vanity(g, M, 0.35, 9.3, Math.PI / 2 + Math.PI, 0.6);

  // --- Entrée -------------------------------------------------------------------------
  box(g, M.darkWood, 1.2, 0.85, 0.35, 2.3, 0.425, 7.1);
  box(g, M.gold, 0.9, 1.3, 0.04, 2.3, 1.85, 6.92);
  box(g, M.mirror, 0.78, 1.16, 0.02, 2.3, 1.85, 6.95);
  solid(1.7, 6.9, 2.9, 7.3);

  // --- Placard / Dressing ---------------------------------------------------------------
  wardrobe(g, M, 0.5, 7.0, 0.9, Math.PI);
  wardrobe(g, M, 18.65, 8.0, 2.3, -Math.PI / 2);
  solid(18.3, 6.9, 18.75, 9.2);
  wardrobe(g, M, 16.6, 7.0, 1.6, 0);
  solid(16.5, 6.85, 17.4, 7.35);

  // --- Buanderie : colonne lave-linge / sèche-linge ----------------------------------------
  box(g, M.appliance, 0.62, 0.85, 0.62, 17.0, 0.43, 10.05);
  box(g, M.appliance, 0.62, 0.85, 0.62, 17.0, 1.3, 10.05);
  cyl(g, M.iron, 0.26, 0.04, 17.0, 0.43, 9.73);
  cyl(g, M.iron, 0.26, 0.04, 17.0, 1.3, 9.73);
  solid(16.65, 9.7, 17.35, 10.4);
  box(g, M.counter, 1.2, 0.04, 0.6, 18.1, 0.9, 10.1);
  solid(17.5, 9.8, 18.7, 10.4);

  return g;
}

// ---------------------------------------------------------------------------
// Luminaires : lustres, suspensions, lanternes + lumières
// ---------------------------------------------------------------------------
export function buildLighting(scene, M) {
  const fixtures = new THREE.Group();
  scene.add(fixtures);
  const lamps = [];

  for (const L of LIGHTS) {
    const room = ROOMS.find(r => r.id === L.room);
    const ceilH = room.ceil;
    const grp = new THREE.Group();

    if (L.type === "chandelier") {
      const drop = 0.85;
      cyl(grp, M.brass, 0.012, drop, 0, ceilH - drop / 2, 0);
      cyl(grp, M.brass, 0.06, 0.12, 0, ceilH - drop, 0);
      const arms = 6;
      for (let i = 0; i < arms; i++) {
        const a = (i / arms) * Math.PI * 2;
        const ax = Math.cos(a) * 0.34, az = Math.sin(a) * 0.34;
        const arm = cyl(grp, M.brass, 0.008, 0.38, ax / 2, ceilH - drop + 0.05, az / 2);
        arm.rotation.z = Math.cos(a) * 1.2; arm.rotation.x = -Math.sin(a) * 1.2;
        cyl(grp, M.trim, 0.018, 0.1, ax, ceilH - drop + 0.16, az);
        const flame = new THREE.Mesh(new THREE.SphereGeometry(0.025, 8, 8),
          new THREE.MeshStandardMaterial({ color: 0xffd890, emissive: 0xffb84d, emissiveIntensity: 2.2 }));
        flame.position.set(ax, ceilH - drop + 0.24, az);
        grp.add(flame);
      }
      lamps.push({ x: L.x, y: ceilH - drop + 0.1, z: L.y, intensity: 22, dist: 7.5 });
    } else if (L.type === "pendant") {
      for (const dx of [-0.6, 0.6]) {
        cyl(grp, M.iron, 0.008, 0.6, dx, ceilH - 0.3, 0);
        const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.16, 0.16, 20, 1, true), M.iron);
        sh.position.set(dx, ceilH - 0.62, 0); grp.add(sh);
        const b = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 8),
          new THREE.MeshStandardMaterial({ color: 0xfff2cc, emissive: 0xffcf70, emissiveIntensity: 2 }));
        b.position.set(dx, ceilH - 0.68, 0); grp.add(b);
      }
      lamps.push({ x: L.x, y: ceilH - 0.75, z: L.y, intensity: 18, dist: 6.5 });
    } else if (L.type === "lantern") {
      cyl(grp, M.brass, 0.008, 0.4, 0, ceilH - 0.2, 0);
      box(grp, M.brass, 0.22, 0.3, 0.22, 0, ceilH - 0.55, 0);
      const gl = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.26, 0.18), M.glass);
      gl.position.set(0, ceilH - 0.55, 0); grp.add(gl);
      const b = new THREE.Mesh(new THREE.SphereGeometry(0.03, 8, 8),
        new THREE.MeshStandardMaterial({ color: 0xfff2cc, emissive: 0xffcf70, emissiveIntensity: 2 }));
      b.position.set(0, ceilH - 0.55, 0); grp.add(b);
      lamps.push({ x: L.x, y: ceilH - 0.6, z: L.y, intensity: 12, dist: 5 });
    } else {
      const d = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.14, 0.05, 16),
        new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff0d0, emissiveIntensity: 1.2 }));
      d.position.set(0, ceilH - 0.03, 0); grp.add(d);
      lamps.push({ x: L.x, y: ceilH - 0.15, z: L.y, intensity: 8, dist: 4 });
    }
    grp.position.set(L.x, 0, L.y);
    fixtures.add(grp);
  }
  return { fixtures, lamps };
}
