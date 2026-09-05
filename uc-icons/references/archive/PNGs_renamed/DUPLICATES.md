# Duplicates, mislabels & look-alikes report

Historical source: the original 73-PNG archive. The bundled canonical set contains 72 unchanged PNGs; see `MANIFEST.csv` for the active original → canonical mapping. The original archive folder and removed duplicate are not bundled.

## 1. Historical duplicate (pixel-identical) — omitted from the active manifest

| Historical duplicate file | Canonical file | Prior archive evidence |
|---|---|---|
| `Pest control (Dubai) [identical to Cockroach control].png` | `Cockroach control.png` | The prior archive report records a pixel-identical render. The generic "pest control" listing reused the cockroach art. `Cockroach control` remains canonical; no active row points to the absent duplicate. |

The legacy source report identified this as its only redundant duplicate. Separate material/base filenames are now manifest aliases pointing to canonical PNGs, so they no longer create extra image copies. The eleven documented character compatibility paths remain bundled unchanged.

## 2. Mislabeled files — named by actual content (originals were filed under the wrong service)

The four `Curtains, Dubai*` source files are **not** four curtains — only one is. The other three are renders of unrelated services saved under recycled "Curtains" filenames:

| Original filename | Actually shows | Renamed to |
|---|---|---|
| `Curtains, Dubai 1.png` | beige grommet curtain on a bronze rod | `Curtains (Dubai).png` ✅ correct |
| `Curtains, Dubai-1.png` | wooden door + yellow power drill | `Door installation (Dubai) [filed as Curtains].png` |
| `Curtains, Dubai-2.png` | white toilet + red plunger | `Toilet unclogging (Dubai) [filed as Curtains].png` |
| `Curtains, Dubai.png` | wall socket/switch + Phillips screwdriver | `Electrical socket & switch (Dubai) [filed as Curtains].png` |

Other content/label notes:
- `Category icon_Ant control-1 1.png` shows a **termite**, not an ant → renamed `Termite control.png` (the grey-ant render kept as `Ant control.png`).
- `Category icon_Festive lights installation Dubai 1.png` shows a plain **glass balustrade railing with no lights** (the non-Dubai version has the string lights). Service name kept; flagging the art gap.

## 3. Near-duplicates / shared artwork — KEPT (distinct renders, distinct services)

These look similar but are genuinely different files; left in the main set. Verify against your service list before pruning.

| Group | Files | Difference |
|---|---|---|
| Cockroach (pest) | `Cockroach control.png` · `Premium pest control (Dubai).png` | Different render — premium cockroach is larger, repositioned, more detailed. NOT identical. |
| Men's salon bust | `Mens salon & massage (Dubai).png` · `Luxury Mens salon & massage (Dubai).png` | Luxury variant adds yellow sparkles. |
| Women's salon bust | `Womens salon & spa (Dubai).png` · `Luxury Womens salon & spa (Dubai).png` | Luxury variant adds sparkles / styling. |
| Helper bust | `All in one help (Dubai).png` · `Insta help (India).png` · `Premium helper (Dubai).png` | Same pose family, different outfit colors/uniform. |
| Split AC | `Premium AC cleaning (Dubai).png` (grey) · `Appliance & AC repair (India).png` (white) | Different color/unit. |
| Water purifier | `Water purifier repair.png` (wall-mount white/blue) · `Native RO Water Purifiers (India).png` (grey RO, NATIVE logo) | Different products. |
| Electrician socket | `Electrician (Dubai).png` (flathead screwdriver) · `Electrical socket & switch (Dubai) [filed as Curtains].png` (Phillips) | Different screwdriver; near-identical concept. |
| Massage tables | `Massage for men.png` (black) · `Spa for women.png` (pink) · `Couples massage (Dubai).png` (both) | Color / count. |

## 4. Avatar base assets (added to `../PNGs/` on 2026-06-12, 15:09)

Four base 3D head renders were present that aren't services — they are the source faces the salon/helper busts are built from. Kept and labeled:
`Avatar base - female (eyes open/closed).png`, `Avatar base - male (eyes open/closed).png`.
