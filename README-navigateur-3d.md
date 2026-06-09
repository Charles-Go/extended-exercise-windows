# Navigateur 3D — 14 rue du Cherche-Midi, Paris VIe

Maquette 3D interactive (web) d'un appartement de réception dans un hôtel
particulier du XVIIIe siècle, reconstituée d'après le **plan projet de
réhabilitation** (DCE, éch. 1/50, 05/05/2026, maîtrise d'œuvre Camille
Thouvenet).

## Lancer

Application 100 % statique, sans build ni dépendance réseau
(three.js est embarqué dans `vendor/`) :

```bash
python3 -m http.server 8080
# puis ouvrir http://localhost:8080/
```

N'importe quel serveur statique convient (`npx serve`, nginx, GitHub Pages…).
Un serveur est nécessaire car la page utilise des modules ES.

## Fonctionnalités

- **Visite** à la première personne : clic pour capturer la souris,
  ZQSD / WASD / flèches, `Maj` pour courir, collisions avec murs et mobilier.
- **Mobile / tablette** : joystick virtuel (marche), glisser pour regarder,
  pincer pour zoomer en orbite, bouton « ☰ Pièces » pour la liste, résolution
  et ombres allégées automatiquement sur écrans tactiles.
- **Orbite** : vue maquette « dollhouse » (plafonds masqués), rotation/zoom.
- **Plan** : vue zénithale orthogonale ; cliquer une pièce téléporte.
- **Visite guidée** (`T`) : parcours automatique des 13 pièces avec panoramiques.
- **Jour / nuit** (`N`) : soleil côté rue ou lustres et appliques allumés.
- **Mini-carte** interactive (clic = téléportation) avec position et orientation.
- Fiche de pièce (surface et hauteur sous plafond du plan) affichée en continu,
  liste des pièces dans le panneau latéral, aide intégrée (`H`).

## Fidélité au plan

- Distribution : enfilade de réception sur rue (Salon 28,26 m² → Petit
  Salon / Salle à Manger 28,37 m² → Bureau 21,40 m² → Chambre 1 28 m²),
  pièces de service sur cour (Entrée 8,70 m², Cuisine 23,60 m², Chambre 2
  23,50 m², salles de bains, dressing, buanderie, WC, placard, dégagement).
- Onze portes-fenêtres sur rue (FN ≈ 131×260, allèges 42–48 cm,
  garde-corps fer forgé), porte palière P:127×262, porte de service P:126×260.
- Hauteurs sous plafond du plan (2,63 m à 3,32 m selon les pièces).
- **Parquet de Versailles** procédural dans les pièces de réception et les
  chambres, dallage pierre à cabochons dans l'entrée, marbre dans les salles
  de bains ; boiseries, corniches, rosaces, cheminées de marbre à trumeau.

La géométrie est une reconstitution indicative à partir du plan 2D :
les cloisonnements secondaires sont approchés, les surfaces affichées sont
celles du plan. La maquette est bâtie en coordonnées plan puis réfléchie en
`z` (three.js est direct, y vers le haut) afin de restituer la chiralité
exacte du plan — vue en plan et mini-carte sont orientées comme le document
d'origine (rue en bas, ouest à gauche).

## Structure

```
index.html          interface et styles
js/data.js          modèle du plan (pièces, murs, percements, luminaires)
js/textures.js      textures procédurales (canvas) et matériaux
js/builder.js       bâti : murs percés, menuiseries, boiseries, cheminées
js/furniture.js     mobilier et luminaires procéduraux
js/main.js          rendu, navigation, mini-carte, visite guidée, interface
vendor/             three.js 0.160 (MIT, licence incluse)
```
