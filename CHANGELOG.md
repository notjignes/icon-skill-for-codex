# Changelog

## Unreleased

- Removed automatic background cleanup, shadow removal and color-based cropping. Export now contains the complete frame and composites existing alpha only, with measured output reporting.
- Added identity-aware request planning, canonical character routing, controlled composition overrides, and role-scoped reference selection with explicit missing coverage.
- Preserved local explicit-source isolation while retaining shared canonical image aliases from the repository package.
- Repaired reference metadata and index integrity; preserved all 72 unique image sources and added a reference validator.
- Shortened the main skill and character/object guides; added selected-reference intake guidance without importing new imagery.
- Added 44 routing, export, reference-integrity and role-scope regression tests.

- Added a README example gallery for representative UC skeuomorphic use-case results.
- Added unpacked `uc-icons` Codex skill as the repo source of truth.
- Bundled service archive PNGs, character bases, manifests, and lookup/export scripts.
- Kept package optimized through manifest `image_path` aliases instead of duplicate base-object/material-index PNG copies.
- Added fixed `1024x768` export behavior with UC Grey (Grey 10) background validation.
- Clarified that the skill is Codex-only and uses GPT Image 2 / Image Gen through the companion `imagegen` skill.
