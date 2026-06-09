// ---------------------------------------------------------------------------
// Modèle de données — RÉHABILITATION D'UN APPARTEMENT
// 14 rue du Cherche-Midi, 75006 Paris — Hôtel particulier XVIIIe
// Reconstruit depuis le PLAN PROJET (DCE, éch. 1/50, 05/05/2026)
// Maîtrise d'œuvre : Camille Thouvenet
// ---------------------------------------------------------------------------
// Coordonnées : x = est (le long de la façade rue), y = nord (vers la cour).
// La façade sur rue est en y=0 ; la cour en y=10.45. Unités : mètres.
// Les surfaces affichées sont les surfaces officielles du plan.
// ---------------------------------------------------------------------------

export const APT = {
  title: "14 rue du Cherche-Midi",
  subtitle: "Paris VIe — Hôtel particulier du XVIIIe siècle",
  width: 18.75,
  depth: 10.45,
  wallH: 3.34,
};

// floor: versailles | plank | stone | marble | tile
export const ROOMS = [
  { id: "salon",      name: "Salon",                      area: "28.26 m²", hsp: 328, floor: "versailles", ceil: 3.28, boiserie: true,
    rects: [[0, 0, 4.30, 6.45]], desc: "Grand salon de réception sur rue, parquet de Versailles, cheminée de marbre." },
  { id: "psalon",     name: "Petit Salon / Salle à Manger", area: "28.37 m²", hsp: 327, floor: "versailles", ceil: 3.27, boiserie: true,
    rects: [[4.70, 0, 9.20, 6.45]], desc: "Pièce de réception en enfilade, table pour huit couverts." },
  { id: "bureau",     name: "Bureau",                     area: "21.40 m²", hsp: 326, floor: "versailles", ceil: 3.26, boiserie: true,
    rects: [[9.60, 0, 14.10, 4.30]], desc: "Bureau-bibliothèque sur rue, en enfilade des salons." },
  { id: "chambre1",   name: "Chambre 1",                  area: "28.00 m²", hsp: 332, floor: "versailles", ceil: 3.32, boiserie: true,
    rects: [[14.50, 0, 18.75, 6.41]], desc: "Chambre principale sur rue, cheminée d'époque, dressing attenant." },
  { id: "dgt",        name: "Dégagement",                 area: "7.85 m²",  hsp: 326, floor: "versailles", ceil: 3.26, boiserie: false,
    rects: [[9.60, 4.70, 12.10, 6.12]], desc: "Couloir de distribution vers chambres et salle de bains." },
  { id: "sdb2",       name: "Salle de Bains 2",           area: "5.40 m²",  hsp: 300, floor: "marble", ceil: 3.00, boiserie: false,
    rects: [[12.20, 4.70, 14.30, 6.12]], desc: "Salle de bains de la chambre 2, faux plafond technique." },
  { id: "chambre2",   name: "Chambre 2",                  area: "23.50 m²", hsp: 326, floor: "versailles", ceil: 3.26, boiserie: true,
    rects: [[9.40, 6.52, 14.30, 10.45]], desc: "Chambre sur cour, deux fenêtres, cheminée de marbre." },
  { id: "cuisine",    name: "Cuisine",                    area: "23.60 m²", hsp: 327, floor: "stone", ceil: 3.27, boiserie: false,
    rects: [[3.49, 6.85, 9.20, 10.45]], desc: "Cuisine sur cour avec îlot central, réfrigérateur-congélateur encastré." },
  { id: "entree",     name: "Entrée",                     area: "8.70 m²",  hsp: 327, floor: "stoneCab", ceil: 3.27, boiserie: true,
    rects: [[1.20, 6.85, 3.39, 10.45], [0, 7.95, 1.10, 8.95]], desc: "Entrée depuis le palier, dallage pierre à cabochons." },
  { id: "wc",         name: "WC",                         area: "1.50 m²",  hsp: 326, floor: "tile", ceil: 3.26, boiserie: false,
    rects: [[0, 9.05, 1.10, 10.45]], desc: "WC d'entrée avec lave-mains." },
  { id: "pl",         name: "Placard",                    area: "1.20 m²",  hsp: 298, floor: "plank", ceil: 2.98, boiserie: false,
    rects: [[0, 6.90, 1.00, 7.85]], desc: "Penderie de l'entrée." },
  { id: "sdb1",       name: "Salle de Bains 1",           area: "4.80 m²",  hsp: 300, floor: "marble", ceil: 3.00, boiserie: false,
    rects: [[14.50, 6.81, 16.40, 9.25]], desc: "Salle de bains principale : baignoire et douche à l'italienne." },
  { id: "dressing",   name: "Dressing",                   area: "6.40 m²",  hsp: 332, floor: "plank", ceil: 3.32, boiserie: false,
    rects: [[16.50, 6.81, 18.75, 9.25]], desc: "Dressing de la chambre principale, penderies toute hauteur." },
  { id: "vestibule",  name: "Vestibule de service",       area: "1.60 m²",  hsp: 263, floor: "stone", ceil: 2.63, boiserie: false,
    rects: [[14.50, 9.35, 15.95, 10.45]], desc: "Accès de service depuis la cour." },
  { id: "buanderie",  name: "Buanderie",                  area: "3.70 m²",  hsp: 263, floor: "tile", ceil: 2.63, boiserie: false,
    rects: [[16.05, 9.35, 18.75, 10.45]], desc: "Buanderie : lave-linge et sèche-linge en colonne." },
];

// Murs : segments à axe central. dir 'x' (horizontal) ou 'y' (vertical).
// c = coordonnée de l'axe ; a,b = étendue ; t = épaisseur ; h = hauteur.
// openings: { at, w, sill, head, type } — at le long du segment.
// type: fwin (porte-fenêtre, garde-corps), win, door, ddoor (double), entry, opening
const H = APT.wallH;
export const WALLS = [
  // ---- façade sur rue (sud) — 11 portes-fenêtres FN ~131x260, allèges 42–48
  { dir: "x", c: -0.25, a: -0.50, b: 19.25, t: 0.50, h: H, openings: [
    { at: 0.85,  w: 1.31, sill: 0.47, head: 3.07, type: "fwin" },
    { at: 2.15,  w: 1.31, sill: 0.47, head: 3.07, type: "fwin" },
    { at: 3.45,  w: 1.31, sill: 0.47, head: 3.07, type: "fwin" },
    { at: 5.45,  w: 1.31, sill: 0.48, head: 3.08, type: "fwin" },
    { at: 6.95,  w: 1.31, sill: 0.48, head: 3.08, type: "fwin" },
    { at: 8.45,  w: 1.30, sill: 0.49, head: 3.07, type: "fwin" },
    { at: 10.85, w: 1.31, sill: 0.47, head: 3.07, type: "fwin" },
    { at: 12.85, w: 1.31, sill: 0.48, head: 3.08, type: "fwin" },
    { at: 15.25, w: 1.32, sill: 0.47, head: 3.08, type: "fwin" },
    { at: 16.60, w: 1.32, sill: 0.47, head: 3.08, type: "fwin" },
    { at: 17.95, w: 1.33, sill: 0.47, head: 3.07, type: "fwin" },
  ]},
  // ---- façade sur cour (nord)
  { dir: "x", c: 10.70, a: -0.50, b: 19.25, t: 0.50, h: H, openings: [
    { at: 0.55,  w: 0.59, sill: 2.00, head: 2.66, type: "win"  },   // FN:59x66 WC
    { at: 2.30,  w: 1.27, sill: 0.00, head: 2.62, type: "entry" },  // P:127x262 palier
    { at: 4.80,  w: 1.32, sill: 0.42, head: 3.04, type: "fwin" },   // cuisine
    { at: 7.20,  w: 1.31, sill: 0.45, head: 3.05, type: "fwin" },   // cuisine
    { at: 10.40, w: 1.33, sill: 0.45, head: 3.05, type: "fwin" },   // chambre 2
    { at: 12.70, w: 1.31, sill: 0.42, head: 3.03, type: "fwin" },   // chambre 2
    { at: 15.20, w: 1.26, sill: 0.00, head: 2.60, type: "entry" },  // P:126x260 service
  ]},
  // ---- pignons mitoyens
  { dir: "y", c: -0.25, a: -0.50, b: 10.95, t: 0.50, h: H, openings: [] },
  { dir: "y", c: 19.00, a: -0.50, b: 10.95, t: 0.50, h: H, openings: [] },

  // ---- refends et cloisons
  // Salon / entrée (mur nord du salon)
  { dir: "x", c: 6.65, a: -0.25, b: 4.50, t: 0.40, h: H, openings: [
    { at: 2.60, w: 1.30, sill: 0, head: 2.58, type: "ddoor" },      // P:130x258
  ]},
  // Salon / petit salon — enfilade
  { dir: "y", c: 4.50, a: 0, b: 6.45, t: 0.40, h: H, openings: [
    { at: 1.15, w: 1.30, sill: 0, head: 2.60, type: "ddoor" },
  ]},
  // Petit salon / cuisine
  { dir: "x", c: 6.65, a: 4.50, b: 9.40, t: 0.40, h: H, openings: [
    { at: 6.90, w: 1.80, sill: 0, head: 2.60, type: "opening" },
  ]},
  // Petit salon / bureau + dégagement
  { dir: "y", c: 9.40, a: 0, b: 6.45, t: 0.40, h: H, openings: [
    { at: 1.15, w: 1.30, sill: 0, head: 2.60, type: "ddoor" },      // enfilade
    { at: 5.40, w: 0.93, sill: 0, head: 2.60, type: "door" },       // vers DGT
  ]},
  // Bureau / dégagement (mur nord du bureau)
  { dir: "x", c: 4.50, a: 9.40, b: 14.30, t: 0.40, h: H, openings: [
    { at: 10.60, w: 0.93, sill: 0, head: 2.60, type: "door" },
  ]},
  // Bureau / chambre 1 — enfilade  P:131x261
  { dir: "y", c: 14.30, a: 0, b: 4.30, t: 0.40, h: H, openings: [
    { at: 1.15, w: 1.31, sill: 0, head: 2.61, type: "ddoor" },
  ]},
  // Chambre 1 / bloc nord-est (SDB1, dressing)
  { dir: "x", c: 6.61, a: 14.30, b: 19.00, t: 0.40, h: H, openings: [
    { at: 15.40, w: 0.83, sill: 0, head: 2.60, type: "door" },      // vers SDB 1
    { at: 17.60, w: 0.83, sill: 0, head: 2.60, type: "door" },      // vers dressing
  ]},
  // Chambre 2, mur sud (sur DGT + SDB2)
  { dir: "x", c: 6.32, a: 9.30, b: 14.50, t: 0.40, h: H, openings: [
    { at: 10.00, w: 0.93, sill: 0, head: 2.60, type: "door" },
  ]},
  // DGT / SDB2
  { dir: "y", c: 12.15, a: 4.70, b: 6.12, t: 0.10, h: H, openings: [
    { at: 5.40, w: 0.73, sill: 0, head: 2.50, type: "door" },
  ]},
  // Cuisine, mur est / chambre 2
  { dir: "y", c: 9.30, a: 6.45, b: 10.70, t: 0.20, h: H, openings: [] },
  // Entrée / cuisine
  { dir: "y", c: 3.44, a: 6.85, b: 10.70, t: 0.10, h: H, openings: [
    { at: 8.60, w: 1.20, sill: 0, head: 2.60, type: "ddoor" },
  ]},
  // WC
  { dir: "y", c: 1.15, a: 9.05, b: 10.70, t: 0.10, h: H, openings: [
    { at: 9.65, w: 0.73, sill: 0, head: 2.50, type: "door" },
  ]},
  { dir: "x", c: 9.00, a: 0, b: 1.15, t: 0.10, h: H, openings: [] },
  // Placard
  { dir: "y", c: 1.05, a: 6.85, b: 7.90, t: 0.10, h: H, openings: [
    { at: 7.35, w: 0.80, sill: 0, head: 2.50, type: "door" },
  ]},
  { dir: "x", c: 7.90, a: 0, b: 1.05, t: 0.10, h: H, openings: [] },
  // Bloc NE : SDB1 / dressing
  { dir: "y", c: 16.45, a: 6.81, b: 9.25, t: 0.10, h: H, openings: [
    { at: 8.10, w: 0.73, sill: 0, head: 2.50, type: "door" },
  ]},
  // Bloc NE : séparation vestibule/buanderie ↔ SDB1/dressing
  { dir: "x", c: 9.30, a: 14.50, b: 19.00, t: 0.10, h: H, openings: [
    { at: 15.20, w: 0.80, sill: 0, head: 2.50, type: "door" },
  ]},
  // Vestibule / buanderie
  { dir: "y", c: 16.00, a: 9.35, b: 10.70, t: 0.10, h: H, openings: [
    { at: 9.95, w: 0.80, sill: 0, head: 2.50, type: "door" },
  ]},
  // Chambre 2 / vestibule + SDB2 est
  { dir: "y", c: 14.40, a: 4.70, b: 10.70, t: 0.20, h: H, openings: [] },
];

// Cheminées : pièce, mur ('W'|'E'|'N'|'S'), position le long du mur
export const FIREPLACES = [
  { room: "salon",    wall: "W", at: 3.20 },
  { room: "psalon",   wall: "E", at: 3.40 },
  { room: "chambre1", wall: "E", at: 3.20 },
  { room: "chambre2", wall: "W", at: 8.50 },
];

// Lustres / points lumineux principaux (x, y, type)
export const LIGHTS = [
  { room: "salon",    x: 2.15,  y: 3.22, type: "chandelier" },
  { room: "psalon",   x: 6.95,  y: 3.22, type: "chandelier" },
  { room: "bureau",   x: 11.85, y: 2.15, type: "chandelier" },
  { room: "chambre1", x: 16.62, y: 3.20, type: "chandelier" },
  { room: "chambre2", x: 11.85, y: 8.48, type: "chandelier" },
  { room: "cuisine",  x: 6.35,  y: 8.65, type: "pendant" },
  { room: "entree",   x: 2.30,  y: 8.65, type: "lantern" },
  { room: "dgt",      x: 10.85, y: 5.41, type: "lantern" },
  { room: "sdb1",     x: 15.45, y: 8.03, type: "flush" },
  { room: "sdb2",     x: 13.25, y: 5.41, type: "flush" },
  { room: "dressing", x: 17.62, y: 8.03, type: "flush" },
  { room: "wc",       x: 0.55,  y: 9.75, type: "flush" },
  { room: "buanderie",x: 17.40, y: 9.90, type: "flush" },
  { room: "vestibule",x: 15.22, y: 9.90, type: "flush" },
  { room: "pl",       x: 0.50,  y: 7.37, type: "flush" },
];

// Parcours de visite guidée
export const TOUR = [
  "entree", "cuisine", "psalon", "salon", "bureau", "chambre1",
  "dressing", "sdb1", "chambre2", "sdb2", "dgt", "wc", "buanderie",
];

export function roomAt(x, y) {
  for (const r of ROOMS)
    for (const [x0, y0, x1, y1] of r.rects)
      if (x >= x0 && x <= x1 && y >= y0 && y <= y1) return r;
  return null;
}

export function roomCenter(r) {
  const [x0, y0, x1, y1] = r.rects[0];
  return { x: (x0 + x1) / 2, y: (y0 + y1) / 2 };
}
