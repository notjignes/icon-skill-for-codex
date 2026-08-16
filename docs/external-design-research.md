# External workflow research

The practical pattern across public icon-generation systems is not “add every good
output to one gallery.” It is:

```text
stable style grammar -> constrained generation -> human review -> selective promotion -> set-level browsing
```

## Evidence used for v0.2

- [Waterlemon](https://sohna.dev/waterlemon/) hides stable style and palette choices
  behind a short subject prompt. Its public material does not publish a consistency
  benchmark or reference-selection algorithm, so it is useful UX evidence rather than
  a proven retrieval design.
- [My:Thiings](https://my.thiings.co/) documents a reference-plus-style-guide loop in
  which good outputs are adjusted and deliberately returned to the guide. Its creator
  also describes programmatic reference selection and an approval dashboard in a
  [creator-authored workflow note](https://www.reddit.com/r/SideProject/comments/1kxne0a/i_made_an_infinite_grid_of_1200_free_aigenerated/).
- Airbnb describes a dimensional icon and motion system developed as part of a wider
  product language rather than a single prompt trick. The public evidence supports a
  maintained visual grammar and long set-level calibration: [Airbnb release](https://news.airbnb.com/en-au/2025-may-release-now-you-can-airbnb-more-than-an-airbnb/)
  and [design-lead interview](https://www.itsnicethat.com/articles/airbnb-app-redesign-140525).
- GPT Image 2 accepts multiple high-fidelity inputs and arbitrary valid output sizes,
  while OpenAI notes that precise composition and cross-generation consistency can
  still fail. This favors a small number of role-labelled references over a large
  attachment set: [OpenAI image-generation guide](https://developers.openai.com/api/docs/guides/image-generation).
- Optical rather than purely geometric centering, consistent detail/weight, and
  small-size review are established icon-system practices: [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/icons)
  and [Adobe Spectrum](https://spectrum.adobe.com/page/iconography/).

## Decisions

- Keep `form`, `material`, `composition`, and `style` as separate responsibilities.
- Attach no more than three references and no more than one per role.
- Grow coverage across archetype, material, view/layout, and composition—not SKU or
  color count.
- Generate three candidates per gap, grid-review all three, and shortlist no more than
  one.
- Promote only after held-out transfer evidence and explicit owner approval.
- Review full-size, equal-size neighboring rows, grayscale/blur/silhouette, and
  32/48/64/96-pixel deliveries.
- Treat Airbnb as a quality benchmark, not a style target. UC should own “competence
  with warmth”: truthful service objects, tactile premium materials, clean completion,
  locally recognizable forms, and a restrained UC accent grammar.
