# Design-token checklist (extracted from superdesign)

> Provenance: extracted verbatim from `superdesigndev/superdesign` `src/tools/theme-tool.ts`
> (the `cssSheetDescription` prompt string, lines 20-35, plus the two forcing-function
> tool parameters), fetched 2026-07-03 from raw.githubusercontent.com @ main.
> Upstream has NO license file (copyright reserved by default) — vendored under the
> user's explicit 2026-07-02 approval for internal use. See ATTRIBUTION.md.

Every asset's stylesheet must carry a `:root` block of CSS custom properties. The
upstream checklist of required variables:

```
:root selector - Must contain CSS custom properties
CSS custom properties format - --variable-name: value;
Semicolon-terminated - Each property must end with ;
--background, --foreground (basic colors)
--primary, --primary-foreground (brand colors)
--secondary, --muted, --accent (semantic colors)
--destructive, --border, --input, --ring (UI elements)
--card, --popover + their foreground variants
--chart-1 through --chart-5 (data visualization)
--sidebar-* variables for navigation
--font-sans, --font-serif, --font-mono
--radius, --spacing
--shadow-* variables (xs, sm, md, lg, xl, etc.)
```

Upstream note kept as-is: "You can add more relevant ones based on use cases, but make
sure to include all the above classes."

Two forcing-function fields the upstream tool requires alongside the sheet — keep them
as a discipline even without the tool:

- `theme_name` — name the theme you are building.
- `reasoning_reference` — "Think through the theme design to make it coherent and what
  reference you used."

## Host adaptation notes (not upstream)

For static single-canvas social assets, `--sidebar-*` and `--chart-1..5` are usually
N/A — declare them anyway (map to accent scale) or mark `/* n/a: no nav/data viz */`
explicitly rather than silently omitting; the point of the checklist is that omissions
are decisions, not accidents.
