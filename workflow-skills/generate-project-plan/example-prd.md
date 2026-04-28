# PRD: Markdown → FigJam Sync (v1)

**Owner:** Caroline Okun · **Target:** Ship at Config 2026 (~2 months) · **Status:** Draft

## Problem

Engineering teams author system documentation in markdown in GitHub, but markdown is a poor medium for visual communication — hierarchies render flatly, and diagrams live as inert code fences. Teams that want visual docs duplicate effort: once in `README.md`, once in FigJam. The duplicate drifts and the FigJam is stale within weeks.

## Users

Teams (Figma internal first, external dev teams second) who maintain architecture, onboarding, or process docs in markdown and want a living visual companion that stays in lockstep with `master`.

## V1 Goals

1. A user can link one markdown file (a path on `master`) to one FigJam file.
2. When that markdown file changes on `master`, the linked FigJam is automatically regenerated to reflect the new content.
3. The regenerated FigJam is **structurally visual**, not a raw dump:
   - Top-level headers → top-level sections; nested headers → nested sub-sections.
   - Prose under each header → stickies / text blocks in its section.
   - Code blocks → code blocks; tables → tables.
   - **Mermaid (and other supported) diagrams render as native FigJam diagrams**, not source code.
4. The synced FigJam is **locked from manual edits** — it is a read-only mirror.
5. Zero-config visual quality good enough to share without tuning.

## Non-Goals (v1)

- Two-way sync (FigJam edits do not flow back to markdown).
- Conflict/merge UI (file is locked, so no conflicts).
- Folder- or repo-wide sync (strictly one file ↔ one FigJam).
- Sync from branches other than `master`.
- Commenting, review, or approval flows inside the synced FigJam.

## Product Behavior

- **Linking:** user establishes a 1:1 link between `owner/repo/path/to/doc.md` and a FigJam file.
- **Regeneration:** on change to the file on `master`, the FigJam is regenerated end-to-end within a target latency (tens of seconds; exact bound TBD).
- **Freshness indicator:** FigJam surfaces the commit SHA and timestamp it was generated from.
- **Lock:** manual edits disabled; users who want to customize must fork, breaking the link.

## Success Criteria

- **Adoption:** N teams link M files during Config week (targets TBD).
- **Freshness:** ≥ 95% of linked FigJams reflect latest `master` within the latency target.
- **Quality:** ≥ 80% of sampled regenerated FigJams rated "usable as-is" by the linking user.

## Implementation Options (resolved in design doc, not here)

- **Delivery surface:** Figma plugin · native Figma feature · external service (GitHub App + REST API writer).
- **Trigger:** GitHub webhook · polling · GitHub Actions step · manual + webhook hybrid.
- **Auth model:** GitHub App · OAuth · PAT.

## Open Questions

1. Visual treatment of prose under a header — one rich text block, stickies (chunked how?), or both?
2. Markdown elements with no clean FigJam analog (footnotes, HTML, inline math) — drop, render as text, or flag in-doc?
3. Scale ceiling for v1 — max file size, max diagrams per file, max concurrent re-syncs?
4. Does the link track a path or a file identity? (i.e., path-follows-renames — yes or no?)
