# Best Practices for `figma-generate-design`

- **Always search before building.** The design system likely has the component, variable, or style you need. Manual construction and hardcoded values should be the exception, not the rule.
- **Search unresolved gaps, one intent per query.** Try synonyms and partial terms as separate `{ entity, query }` entries in one `queries` call, never combined into one string—a "NavigationPill" might be found under "pill", "nav", "tab", or "chip", so pass those as four component entries. For variables, use `entity: "variable"` with queries like "color", "spacing", and "radius". Do this only for unresolved construction gaps, and stop once a suitable asset is found.
- **Prefer design system tokens over hardcoded values.** Use variable bindings for colors, spacing, and radii. Use text styles for typography. Use effect styles for shadows. This keeps the screen linked to the design system.
- **Prefer component instances over manual builds.** Instances stay linked to the source component and update automatically when the design system evolves.
- **Componentize by default.** Build repeated or reusable elements as a component once, then place instances. Do not ship a flat tree of one-off frames that needs a second "make it componentized" pass.
- **Work in retry-safe construction phases.** Batch related sections into one `use_figma` call when the script stays safe to retry; split only at page-context boundaries, hard-to-recover mutations, or a targeted retry after an actual failure.
- **Return node IDs and validation evidence from every call.** Return created IDs plus the relevant counts, names, and bounds — this is your default structural validation, and you'll need the IDs to compose sections and for error recovery.
- **Validate visually with one composition screenshot.** Take one full-view screenshot after composition, and one more only after a targeted visual fix; the most recent passing screenshot is final.
- **Assert the font family, not just a successful load.** A script can load the wrong font without error. After building, verify rendered text uses the product font identified in Step 1 (see Step 5).
- **Match existing conventions.** If the file already has screens, match their naming, sizing, and layout patterns.
