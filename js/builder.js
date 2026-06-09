// ---------------------------------------------------------------------------
// Construction du bâti : murs percés, menuiseries, boiseries, corniches,
// cheminées, sols, plafonds. Plan (x,y) → monde (x, alt, z=y).
// ---------------------------------------------------------------------------
import * as THREE from "three";
import { APT, ROOMS, WALLS, FIREPLACES, roomAt } from "./data.js";

const BOX = new THREE.BoxGeometry(1, 1, 1);

function box(parent, mat, w, h, d, x, y, z, ry = 0) {
  const m = new THREE.Mesh(BOX, mat);
  m.scale.set(w, h, d);
  m.position.set(x, y, z);
  if (ry) m.rotation.y = ry;
  m.castShadow = m.receiveShadow = true;
  parent.add(m);
  return m;
}

export function buildApartment(scene, M) {
  const colliders = [];
  const ceilGroup = new THREE.Group();
  const wallsGroup = new THREE.Group();
  const decoGroup = new THREE.Group();
  scene.add(ceilGroup, wallsGroup, decoGroup);

  const H = APT.wallH;

  const addCollider = (x0, z0, x1, z1) => colliders.push({ x0, z0, x1, z1 });

  // --- murs percés ----------------------------------------------------------
  for (const w of WALLS) {
    const ops = [...w.openings].sort((p, q) => p.at - q.at);
    const segs = []; // {a,b,y0,y1}
    let cur = w.a;
    for (const o of ops) {
      const oa = o.at - o.w / 2, ob = o.at + o.w / 2;
      if (oa > cur + 0.001) segs.push({ a: cur, b: oa, y0: 0, y1: w.h, solid: true });
      if (o.sill > 0.01) segs.push({ a: oa, b: ob, y0: 0, y1: o.sill, solid: true });
      if (o.head < w.h - 0.01) segs.push({ a: oa, b: ob, y0: o.head, y1: w.h, solid: false });
      cur = ob;
    }
    if (cur < w.b - 0.001) segs.push({ a: cur, b: w.b, y0: 0, y1: w.h, solid: true });

    const mat = w.t >= 0.45 ? M.wallExt : M.wall;
    for (const s of segs) {
      const len = s.b - s.a, hh = s.y1 - s.y0, mid = (s.a + s.b) / 2, ymid = (s.y0 + s.y1) / 2;
      if (len <= 0.002 || hh <= 0.002) continue;
      if (w.dir === "x") {
        box(wallsGroup, mat, len, hh, w.t, mid, ymid, w.c);
        if (s.solid && s.y0 < 0.3) addCollider(s.a, w.c - w.t / 2, s.b, w.c + w.t / 2);
      } else {
        box(wallsGroup, mat, w.t, hh, len, w.c, ymid, mid);
        if (s.solid && s.y0 < 0.3) addCollider(w.c - w.t / 2, s.a, w.c + w.t / 2, s.b);
      }
    }
    // menuiseries
    for (const o of ops) addJoinery(decoGroup, M, w, o, addCollider);
  }

  // --- sols et plafonds par pièce -------------------------------------------
  for (const r of ROOMS) {
    for (const [x0, y0, x1, y1] of r.rects) {
      const wD = x1 - x0, dD = y1 - y0;
      const base = M[r.floor] || M.plank;
      const fm = base.clone();
      fm.map = base.map.clone();
      const unit = r.floor === "versailles" ? 1.08 : r.floor === "stoneCab" ? 0.9 : r.floor === "marble" ? 1.2 : r.floor === "stone" ? 1.6 : 1.3;
      fm.map.repeat.set(wD / unit, dD / unit);
      fm.map.needsUpdate = true;
      const floor = new THREE.Mesh(new THREE.PlaneGeometry(wD, dD), fm);
      floor.rotation.x = -Math.PI / 2;
      floor.position.set((x0 + x1) / 2, 0.001, (y0 + y1) / 2);
      floor.receiveShadow = true;
      scene.add(floor);

      const ceil = new THREE.Mesh(new THREE.PlaneGeometry(wD, dD), M.ceiling);
      ceil.rotation.x = Math.PI / 2;
      ceil.position.set((x0 + x1) / 2, r.ceil, (y0 + y1) / 2);
      ceilGroup.add(ceil);
    }
    addRoomTrim(decoGroup, M, r);
  }

  // --- cheminées --------------------------------------------------------------
  for (const f of FIREPLACES) addFireplace(decoGroup, M, f);

  // --- extérieur : cour et rue -------------------------------------------------
  const street = new THREE.Mesh(new THREE.PlaneGeometry(60, 14), new THREE.MeshStandardMaterial({ color: 0x4f5258, roughness: 1 }));
  street.rotation.x = -Math.PI / 2;
  street.position.set(9.4, -0.02, -7.5);
  street.receiveShadow = true;
  scene.add(street);
  const cour = new THREE.Mesh(new THREE.PlaneGeometry(60, 12), new THREE.MeshStandardMaterial({ color: 0x8d8676, roughness: 1 }));
  cour.rotation.x = -Math.PI / 2;
  cour.position.set(9.4, -0.02, 16.9);
  cour.receiveShadow = true;
  scene.add(cour);
  // façade opposée de la cour, simple volume
  box(scene, M.wallExt, 30, 9, 0.6, 9.4, 4.5, 17.5);

  return { colliders, ceilGroup, wallsGroup, decoGroup };
}

// ---------------------------------------------------------------------------
// Menuiseries : portes-fenêtres, fenêtres, portes simples/doubles, passages
// ---------------------------------------------------------------------------
function openingFrame(g, M, w, o) {
  // chambranle périphérique, légèrement saillant
  const d = w.t + 0.04;
  const place = (len, hh, off, ymid) => {
    if (w.dir === "x") box(g, M.trim, len, hh, d, o.at + off, ymid, w.c);
    else box(g, M.trim, d, hh, len, w.c, ymid, o.at + off);
  };
  place(0.10, o.head - o.sill + 0.10, -(o.w / 2 + 0.05), (o.sill + o.head) / 2 + 0.05);
  place(0.10, o.head - o.sill + 0.10, +(o.w / 2 + 0.05), (o.sill + o.head) / 2 + 0.05);
  place(o.w + 0.20, 0.10, 0, o.head + 0.05);
  if (o.sill > 0.01) place(o.w + 0.24, 0.06, 0, o.sill + 0.03);
}

function paneledLeaf(g, M, lw, lh, t) {
  // vantail mouluré : 3 panneaux en retrait
  const leaf = new THREE.Group();
  const body = box(leaf, M.doorWood, lw, lh, t, 0, lh / 2, 0);
  const panel = (py, ph) => {
    box(leaf, M.trim, lw * 0.72, ph, t * 0.4, 0, py, t * 0.45);
    box(leaf, M.trim, lw * 0.72, ph, t * 0.4, 0, py, -t * 0.45);
  };
  panel(lh * 0.18, lh * 0.20);
  panel(lh * 0.47, lh * 0.26);
  panel(lh * 0.80, lh * 0.28);
  box(leaf, M.brass, 0.025, 0.12, 0.025, -lw * 0.42, lh * 0.38, t * 0.7);
  g.add(leaf);
  return leaf;
}

function addJoinery(g, M, w, o, addCollider) {
  openingFrame(g, M, w, o);
  const horiz = w.dir === "x";
  const setOn = (obj, along, up, across) => {
    if (horiz) obj.position.set(along, up, w.c + across);
    else { obj.position.set(w.c + across, up, along); obj.rotation.y = Math.PI / 2; }
  };

  if (o.type === "fwin" || o.type === "win") {
    const grp = new THREE.Group();
    const fh = o.head - o.sill;
    // dormant
    const fr = 0.06, t = 0.07;
    box(grp, M.trim, o.w, fr, t, 0, fh - fr / 2, 0);
    box(grp, M.trim, o.w, fr, t, 0, fr / 2, 0);
    box(grp, M.trim, fr, fh, t, -o.w / 2 + fr / 2, fh / 2, 0);
    box(grp, M.trim, fr, fh, t, o.w / 2 - fr / 2, fh / 2, 0);
    box(grp, M.trim, fr, fh, t, 0, fh / 2, 0); // meneau central
    // petits bois + vitrage (2 vantaux × 3 carreaux)
    for (const sx of [-1, 1]) {
      const cx = sx * o.w / 4;
      box(grp, M.trim, o.w / 2 - fr, 0.04, t * 0.8, cx, fh / 3, 0);
      box(grp, M.trim, o.w / 2 - fr, 0.04, t * 0.8, cx, (2 * fh) / 3, 0);
      const glass = new THREE.Mesh(new THREE.PlaneGeometry(o.w / 2 - fr, fh - 2 * fr), M.glass);
      glass.position.set(cx, fh / 2, 0);
      grp.add(glass);
    }
    // crémone laiton
    box(grp, M.brass, 0.02, 0.5, 0.02, 0, fh / 2, t * 0.7);
    // garde-corps fer forgé pour portes-fenêtres sur rue
    if (o.type === "fwin") {
      const side = w.c < 5 ? -1 : 1; // saillie côté extérieur
      const rg = new THREE.Group();
      for (const by of [0.25, 0.5, 0.75]) box(rg, M.iron, o.w, 0.025, 0.025, 0, by, side * (w.t / 2 + 0.06));
      for (let i = 0; i <= 6; i++) box(rg, M.iron, 0.018, 0.78, 0.018, -o.w / 2 + (i * o.w) / 6, 0.39, side * (w.t / 2 + 0.06));
      rg.position.y = o.sill;
      grp.add(rg);
    }
    setOn(grp, o.at, o.sill, 0);
    grp.position.y = o.sill;
    g.add(grp);
  } else if (o.type === "door" || o.type === "ddoor" || o.type === "entry") {
    const leaves = o.type === "door" ? 1 : 2;
    const lw = o.w / leaves - 0.01;
    const t = 0.045;
    for (let i = 0; i < leaves; i++) {
      const leaf = paneledLeaf(new THREE.Group(), M, lw, o.head - 0.02, t);
      const grp = new THREE.Group();
      grp.add(leaf);
      // pivot au dormant
      const hinge = i === 0 ? -o.w / 2 : o.w / 2;
      leaf.position.x = (i === 0 ? lw / 2 : -lw / 2);
      let angle = 0;
      if (o.type === "entry") angle = 0; // fermée
      else angle = (i === 0 ? 1 : -1) * (o.type === "door" ? 1.45 : 1.75);
      grp.rotation.y = angle;
      const holder = new THREE.Group();
      holder.add(grp);
      setOn(holder, o.at + hinge, 0, 0);
      g.add(holder);
    }
    if (o.type === "entry") {
      // porte fermée : on bloque le passage
      if (w.dir === "x") addCollider(o.at - o.w / 2, w.c - w.t / 2, o.at + o.w / 2, w.c + w.t / 2);
      else addCollider(w.c - w.t / 2, o.at - o.w / 2, w.c + w.t / 2, o.at + o.w / 2);
      // imposte vitrée au-dessus ? non — panneau plein dans le plan
    }
  }
  // 'opening' : simple passage avec chambranle déjà posé
}

// ---------------------------------------------------------------------------
// Plinthes, cimaises, panneaux de boiserie, corniches — par pièce
// ---------------------------------------------------------------------------
function edgeGaps(axis, c, a, b) {
  // ouvertures (sol) des murs coïncidant avec l'arête de pièce
  const gaps = [];
  for (const w of WALLS) {
    if (w.dir !== axis) continue;
    if (Math.abs(w.c - c) > w.t / 2 + 0.12) continue;
    for (const o of w.openings) {
      if (o.sill > 0.2) continue;
      const oa = Math.max(a, o.at - o.w / 2 - 0.06), ob = Math.min(b, o.at + o.w / 2 + 0.06);
      if (ob > oa) gaps.push([oa, ob]);
    }
  }
  gaps.sort((p, q) => p[0] - q[0]);
  return gaps;
}

function strips(a, b, gaps) {
  const out = [];
  let cur = a;
  for (const [ga, gb] of gaps) {
    if (ga > cur + 0.05) out.push([cur, ga]);
    cur = Math.max(cur, gb);
  }
  if (b > cur + 0.05) out.push([cur, b]);
  return out;
}

function addRoomTrim(g, M, r) {
  const [x0, y0, x1, y1] = r.rects[0];
  const edges = [
    { axis: "x", c: y0, a: x0, b: x1, nx: 0, nz: 1 },
    { axis: "x", c: y1, a: x0, b: x1, nx: 0, nz: -1 },
    { axis: "y", c: x0, a: y0, b: y1, nx: 1, nz: 0 },
    { axis: "y", c: x1, a: y0, b: y1, nx: -1, nz: 0 },
  ];
  for (const e of edges) {
    const gaps = edgeGaps(e.axis, e.c, e.a, e.b);
    const segs = strips(e.a, e.b, gaps);
    for (const [sa, sb] of segs) {
      const len = sb - sa, mid = (sa + sb) / 2;
      const place = (mat, ww, hh, dd, up, off) => {
        if (e.axis === "x") box(g, mat, len * (ww || 1), hh, dd, mid, up, e.c + e.nz * off);
        else box(g, mat, dd, hh, len * (ww || 1), e.c + e.nx * off, up, mid);
      };
      // plinthe
      place(M.trim, 1, 0.15, 0.022, 0.075, 0.012);
      if (!r.boiserie) continue;
      // cimaise
      place(M.trim, 1, 0.06, 0.03, 0.98, 0.015);
      // panneaux hauts et bas (cadres moulurés)
      const nP = Math.max(1, Math.round(len / 1.4));
      const pw = len / nP;
      for (let i = 0; i < nP; i++) {
        const pc = sa + pw * (i + 0.5);
        const frame = (yC, hP, wP) => {
          const mk = (ww, hh, dx, dy) => {
            if (e.axis === "x") box(g, M.trim, ww, hh, 0.018, pc + dx, yC + dy, e.c + e.nz * 0.012);
            else box(g, M.trim, 0.018, hh, ww, e.c + e.nx * 0.012, yC + dy, pc + dx);
          };
          mk(wP, 0.035, 0, hP / 2);
          mk(wP, 0.035, 0, -hP / 2);
          mk(0.035, hP, -wP / 2, 0);
          mk(0.035, hP, wP / 2, 0);
        };
        frame(0.56, 0.55, pw * 0.74);            // soubassement
        frame((1.08 + r.ceil - 0.36) / 2, r.ceil - 1.55, pw * 0.74); // panneau haut
      }
    }
    // corniche (continue, au-dessus des portes)
    const len = e.b - e.a, mid = (e.a + e.b) / 2;
    const cor = (hh, dd, drop, off) => {
      if (e.axis === "x") box(g, M.trim, len, hh, dd, mid, r.ceil - drop, e.c + e.nz * off);
      else box(g, M.trim, dd, hh, len, e.c + e.nx * off, r.ceil - drop, mid);
    };
    cor(0.10, 0.10, 0.05, 0.05);
    if (r.boiserie) cor(0.05, 0.05, 0.125, 0.025);
  }
  // rosace de plafond
  if (r.boiserie && r.id !== "entree") {
    const cx = (x0 + x1) / 2, cz = (y0 + y1) / 2;
    const ros = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.5, 0.03, 32), M.ceiling);
    ros.position.set(cx, r.ceil - 0.015, cz);
    g.add(ros);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.32, 0.025, 8, 32), M.trim);
    ring.rotation.x = Math.PI / 2;
    ring.position.set(cx, r.ceil - 0.03, cz);
    g.add(ring);
  }
}

// ---------------------------------------------------------------------------
// Cheminées de marbre avec trumeau-miroir
// ---------------------------------------------------------------------------
function addFireplace(g, M, f) {
  const r = ROOMS.find(rr => rr.id === f.room);
  const [x0, y0, x1, y1] = r.rects[0];
  const grp = new THREE.Group();
  // construite face +Z, puis orientée
  const W = 1.45, D = 0.36, Hm = 1.12;
  box(grp, M.marbleFire, 0.22, Hm, D, -W / 2 + 0.11, Hm / 2, D / 2);
  box(grp, M.marbleFire, 0.22, Hm, D, W / 2 - 0.11, Hm / 2, D / 2);
  box(grp, M.marbleFire, W, 0.18, D, 0, Hm - 0.09, D / 2);
  box(grp, M.marbleFire, W + 0.12, 0.05, D + 0.08, 0, Hm + 0.025, D / 2);
  // foyer
  box(grp, new THREE.MeshStandardMaterial({ color: 0x17120e, roughness: 1 }), W - 0.5, Hm - 0.25, 0.06, 0, (Hm - 0.25) / 2, 0.06);
  // sole de marbre
  box(grp, M.marbleFire, W + 0.2, 0.02, 0.55, 0, 0.01, 0.45);
  // trumeau : miroir au cadre doré
  const mh = 1.9;
  box(grp, M.gold, 1.3, mh, 0.05, 0, Hm + 0.1 + mh / 2, 0.07);
  const mir = new THREE.Mesh(new THREE.PlaneGeometry(1.14, mh - 0.16), M.mirror);
  mir.position.set(0, Hm + 0.1 + mh / 2, 0.10);
  grp.add(mir);

  let px, pz, ry;
  if (f.wall === "W") { px = x0 + 0.02; pz = f.at; ry = Math.PI / 2; }
  else if (f.wall === "E") { px = x1 - 0.02; pz = f.at; ry = -Math.PI / 2; }
  else if (f.wall === "S") { px = f.at; pz = y0 + 0.02; ry = 0; }
  else { px = f.at; pz = y1 - 0.02; ry = Math.PI; }
  grp.position.set(px, 0, pz);
  grp.rotation.y = ry;
  g.add(grp);
  return grp;
}
