# Material / Type icon index

A reference index of the icon archive for an icon generator. Each manifest alias describes **what the source is made of and what type of thing it is**, so the generator can retrieve material/form evidence for a new icon. Composition and lighting are not independently annotated in this legacy archive.

72 icons (73 original source entries minus 1 documented duplicate — see `../PNGs_renamed/DUPLICATES.md`). The unchanged canonical PNGs live in `../PNGs_renamed/`. This folder contains an alias manifest, not duplicate PNGs. Resolve each `image_path` relative to the skill directory containing `SKILL.md`; do not open `material_index_file` as a physical path.

## Filename scheme

```
<type>__<materials>__<objects>.png
```

- `__` (double underscore) separates the three fields; `-` (hyphen) separates tokens within a field.
- **type** — one of: `appliance` `composite` `furniture` `human` `material` `object` `textile` `tool`
- **materials** — finishes/materials, most prominent first (e.g. `glossy-ceramic-chrome-rubber`, `matte-plastic`, `brushed-steel`, `tufted-velvet-acrylic`).
- **objects** — the actual subjects, most prominent first (e.g. `sink-faucet-adjustable-wrench`).
- On a rare name collision a color token is appended (e.g. `…cockroach-prohibition-sign__brown-red.png`).

### Examples
```
appliance__matte-plastic__hair-dryer.png
composite__glossy-ceramic-chrome-rubber__sink-faucet-adjustable-wrench.png
furniture__leather-wood-cotton__massage-table-towel-headrest.png
human__stylized-3d-render-skin__woman-bust-eyes-open.png
material__wood-marble-fluted-plaster__wall-panel-swatches-3.png
```

## How to use as a generator reference index
1. Parse the target service into desired **type** + **materials** + **objects**.
2. Filter the index by `type` (prefix match), then rank candidates by material/object token overlap.
3. Use the top match's render as the style/material/lighting reference for the new icon.

`MANIFEST.csv` retains the legacy columns (`type, materials, objects, colors`) plus original and service filenames. It adds `asset_id`, `image_path`, `sha256`, `source_role`, `approval_status`, `provenance_source`, `material_tags`, and `finish_tags`. The ID and hash are shared by all aliases of a canonical source. `existing_curated` records legacy provenance; it does not claim a fresh visual review. Split material/finish tags are derived only from the existing material labels, with `unknown` retained where those labels provide no evidence.

## Counts by type
| type | count |
|---|---|
| appliance | 17 |
| composite | 18 |
| object | 13 |
| human | 11 |
| furniture | 9 |
| tool | 2 |
| material | 1 |
| textile | 1 |

> Note: `composite` = two+ material/object categories with none clearly dominant (e.g. ceramic sink **+** metal/rubber wrench). When searching for a single-material reference, also check `object`/`appliance`/`tool`.
