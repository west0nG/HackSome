# Audit summary — provenance/attribution inventory across all runtime skills

- **Date**: 2026-07-10
- **Method**: 5 parallel full-read audits (every `.md` under `agents/assets/skills/` read in full; execution closure traced from each entry `SKILL.md`; every vendored file byte-compared against upstream via curl+cmp; git history checked for post-vendor edits).
- **Detail files** (the per-item ledger — item IDs below refer to these):
  - `audit-inhouse.md` — 14 in-house skills (FO-*, IP-*, KDP-*, ETSY-*, GUM-*, DD-*, DC-*, CR-*)
  - `audit-voice-visual.md` — mine-customer-voice + visual-iterate (MCV-*, VI-*)
  - `audit-de-ai-ify.md` — de-ai-ify (H*, E*, D*, Z*, F*)
  - `audit-gen-image.md` — gen-image (host + smixs + codex items)
  - `audit-design-asset.md` — design-asset (A*, B*, G*, J*, F1, D1)

## Headline results

1. **Byte-exact verification: 82/82 vendored files VERIFIED-EXACT** against upstream
   (voice-visual 8, de-ai-ify 16, gen-image 29, design-asset 29). Git shows zero
   post-vendor edits anywhere. Consequence: **every provenance item inside a vendored
   file is upstream's own content** — in-place edits are forbidden by the byte-exact/
   verbatim claims (PRD R5/AC4). All 35 `Source concept` comments in gen-image
   patterns and all guizang in-file notes are upstream-authored.
2. **Host-editable C1 items: ~30 items across 14 files** — 7 host `SKILL.md` files
   (find-opportunity, decide-direction, create-role, mine-customer-voice,
   visual-iterate, de-ai-ify, gen-image, design-asset), 6 find-opportunity/
   decide-direction reference files, and `design-asset/references/superdesign/
   token-checklist.md` (an extraction, NOT byte-exact — freely editable).
3. **8 HTML provenance comments** total in host-authored files, all in-closure:
   find-opportunity ×5 (SKILL + 4 refs), decide-direction ×2 (SKILL + direction-critic),
   create-role ×1. The when-idle comment named in the PRD **no longer exists**
   (removed by the 07-10 rewrite, 35b4bdf; content preserved in git history +
   `archive/2026-07/07-08-proactive-idle/`).
4. **10 skills are completely clean** (check-email, claim-mailbox, company-state,
   deploy-site, provision-ga4, receive-goal, review-objective, review-role,
   send-goal, set-objective) — zero provenance content.
5. **New ATTRIBUTION.md needed ×3**: find-opportunity, decide-direction, create-role.
   All 5 existing ATTRIBUTION.md files stay canonical and absorb migrated content.
6. **Execution→bypass pointers (R2 violations) exist today**: "see `ATTRIBUTION.md`"
   in mine-customer-voice SKILL.md (×2 sites), visual-iterate SKILL.md, de-ai-ify
   SKILL.md, token-checklist.md. All removed by the same migration that deletes the
   surrounding provenance text.
7. **R4 mixed sentences requiring rewrite (not deletion)**: create-role SKILL.md L95
   (`07-06 capability-first stance` — keep stance, drop decision pointer); optional
   neutralizations MCV-2/3/4/5 ("upstream/vendored" wording on functional mapping
   rules); gen-image SKILL.md L8/26/34 and design-asset SKILL.md A-items are partial
   rewrites (keep routing, drop sourcing vocabulary).

## Legal/record corrections discovered (must land in ATTRIBUTION.md files)

- **superdesign upstream NOW HAS a license (AGPLv3 dual)** — design-asset
  ATTRIBUTION.md's "No license file (NOASSERTION) + user-approved exception" is
  outdated and must be corrected while keeping the 2026-07-02 approval history.
- **Missing commit pins**: visual-iterate (guizang "main @ 2026-07-03", no SHA),
  de-ai-ify (all three sources "2026-07-01, main", no SHA). Today's verification
  resolved current-main SHAs — record them.
- **Unresolvable pointers**: gen-image ATTRIBUTION.md cites "research doc §4.5" and
  "task prd AC4" (task now archived); find-opportunity FO-1 comment cites deleted
  task `07-01-ceo-monetization`. audit-inhouse.md resolved all research paths to
  their `archive/` locations — carry the resolved paths into the new files.

## Behavioral hazard noted (out of task scope, flagged for follow-up)

`gen-image/references/codex/cli-reference.md:149` (upstream, byte-exact, in-closure)
says "Open an issue on this skill's repo" and `codex/SECURITY.md` carries upstream
maintainer contact — an agent debugging the codex path could contact a third-party
repo (same class as the first-test longrun's unauthorized external PR). Cannot be
edited in place (byte-exact). Candidate fixes belong to a separate decision:
host-layer counter-rule or fleet-level guardrail.

## Category totals

| Group | C1 host-editable | C1-nature frozen in vendored | C2 bypass items | C3 functional (stay) |
|---|---|---|---|---|
| in-house (14 skills) | 8 comments + 1 mixed + 1 borderline | — | license tokens/history inside the 8 comments | Publisher Rocket, eRank/EverBee etc., incident-calibration sentences |
| voice + visual | 6 | ~4 (upstream layout residue) | 2 ATTRIBUTION + 2 LICENSE | quote/source capture rules, path-mapping rules, SOURCES.md/CC credit |
| de-ai-ify | 2 | 9 | ATTRIBUTION + 3 LICENSE + 2 frozen frontmatter + zh sources.md | F1–F9 (routing, corpus checks, style baselines) |
| gen-image | 3 | 40 (35 Source-concept + codex items) | ATTRIBUTION + 2 LICENSE | 5 (RU-normative constraints, format rules, version baseline) |
| design-asset | ~11 | ~12 | ATTRIBUTION + 4 LICENSE + COMMERCIAL_LICENSING + approvals | inert-citation block, escape hatch, token discipline, product-attribution rules |
