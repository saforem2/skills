---
name: scientific-figure-typography
description: "Use when standardizing fonts across scientific figures."
version: 1.0.0
author: Hermes Curator
license: MIT
metadata:
  hermes:
    category: research
    tags: [figures, typography, matplotlib, graphviz, latex, publication]
---

# Scientific Figure Typography

## When to Use

Use for publication figures when chart and diagram fonts must match a LaTeX manuscript across Matplotlib, Graphviz, XeLaTeX/LuaLaTeX, and portable build environments.

## Goal

Make every source-backed chart and diagram visually match the paper at its final physical size. Use Libertinus Serif for prose and chart labels, Libertinus Sans only where sans is intentional, JetBrains Mono for commands/code, and Libertinus Math or a metrically compatible math face.

## 1. Inventory before editing

Enumerate every included figure from the LaTeX sources, then map each PDF to its generator (`*.py`, `*.dot`, TikZ, or external/legacy asset). Inspect embedded fonts before changing anything:

```bash
pdffonts figures/name.pdf
```

Separate source-backed figures from legacy PDFs. Normalize all source-backed assets; explicitly report legacy assets that cannot be regenerated instead of claiming complete normalization. Audit the complete deliverable set in one pass (all included figure PDFs, the manuscript PDF, and any standalone appendix) and reduce `pdffonts` output to unique families. Treat six-letter PDF subset prefixes as normal; distinguish a wrong family from legacy Type 3 encoding and from an intentional math font instead of reporting all three as the same defect.

## 2. Centralize Matplotlib typography

Create one importable style module and make every plotting script call it. Keep family policy global but allow size presets for single-column, double-column, and tall multi-panel figures.

The shared configuration should set at least:

```python
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Libertinus Serif", "STIX Two Text", "DejaVu Serif"],
    "font.sans-serif": ["Libertinus Sans", "DejaVu Sans"],
    "font.monospace": ["JetBrains Mono", "Libertinus Mono", "DejaVu Sans Mono"],
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})
```

Register TeX Live fonts with Matplotlib when the OS font index does not expose them. Resolve portable paths with `kpsewhich`, then call `matplotlib.font_manager.fontManager.addfont(path)` before applying `rcParams`. If strict PDF-family consistency is required, avoid invoking Matplotlib mathtext merely for ordinary labels such as arrows, minus signs, multiplication signs, or Greek letters; use native Unicode glyphs when they are semantically plain text, because `mathtext.fontset = "stix"` embeds STIX resources even when all surrounding text is Libertinus.

Preserve each figure's effective print-size typography while centralizing it; blindly assigning one point size to every canvas makes small-column and tall appendix figures inconsistent after scaling.

For comparative training curves, normalize provenance before styling: load every requested run independently, reconstruct a monotonic x-axis from global step when exported token counters reset across restarts, and apply the same explicit token cutoff to all compared traces. State the cutoff in the legend and caption, and update the title, axis labels, and caption together so the manuscript never describes a superseded trace set. Do not add endpoint markers unless they encode requested information; for trend-only overlays, use distinct colors and dash patterns. When discrete evaluation samples are requested, draw them as open circles with a light neutral edge so they do not conceal coincident curves. When dense telemetry is noisy, prefer the stable training stream where sources overlap, aggregate into token bins with median statistics, then apply a light EMA; validate that smoothing removes logging excursions without erasing real regime changes, and ensure every trace visibly reaches the common cutoff.

Construct dense legends semantically rather than accepting plot order. Collect handles and labels, specify the desired order explicitly, and remember that Matplotlib fills a multi-column legend top-to-bottom within each column. For a two-family, three-row legend, order all three left-column entries first and all three right-column entries second. Put the most important reference signal first. Use an opaque white legend frame and a z-order above annotations when stage lines pass behind it; keep subdued swatches dark enough to survive print. If a requested corner is occupied by data, reserve a compact strip immediately above that axes and move the title or top margin accordingly instead of hiding curves. For two metrics that share an x variable in a single-column figure, prefer vertically stacked panels with `sharex=True`: each panel keeps the full column width and token/event positions align directly. Remove the duplicate upper x-label, reserve figure-level space for the legend, and update captions from “left/right” to “top/bottom.” For small multiples, do not reuse one annotation coordinate across every panel: identify open space per panel, place text in axes-fraction coordinates, and check the first, middle, and last panels independently. Put callout text away from the target curve and use a short or curved leader aimed at the exact event; matching the callout color to the curve is useful only when contrast remains strong. Re-render after every placement adjustment because standalone and manuscript scaling can change collisions.

Build comparative-curve palettes around semantic families and visual priority, not an arbitrary rainbow cycle. Reuse the manuscript's established semantic palette before introducing a standalone “optimal” color: cross-figure consistency usually matters more than a locally attractive hue. When an overview diagram establishes canonical hues, read the exact hex values from its source, centralize them in one chart-palette module, and remap every source-backed chart through semantic role dictionaries; do not approximate the hues or leave hidden one-off literals in individual generators. Preserve neutral greys for references, grids, and raw telemetry. Treat the canonical hues as anchors, not an artificial hard limit: when a multi-series or multi-panel figure needs more distinct identities, add a small number of compatible secondary accents such as a clearly separated orange and light magenta-pink. Prefer unique, perceptually separated colors when repetition would make panels harder to scan, and retain redundant marker or line-style encoding for related traces and grayscale reproduction.

Keep reference data neutral: use open light-gray circles for discrete validation points so they do not hide coincident curves, a pale solid gray for raw telemetry, and a slightly darker but still subordinate dashed gray for its EMA. Give the primary comparison a saturated solid theme color, and encode related scale variants with distinct solid, dotted, dashed, or dash-dot patterns. Carry the primary comparison color into residual panels and annotations. Judge the hierarchy at publication size: the EMA and validation markers must remain legible without becoming visually heavier than the run being compared. If coincident reference lines disappear beneath a focal curve, fix draw order (`zorder`) before repeatedly darkening or thickening them; occlusion is a layering defect, not necessarily a palette defect.

## 3. Make XeLaTeX/LuaLaTeX selection portable

Use `iftex` to preserve a pdfTeX fallback and `unicode-math` for Unicode engines. Family-name lookup is not sufficient: TeX Live can contain Libertinus while XeTeX's system-font lookup cannot resolve `Libertinus Serif`.

Use family names first and TeX Live filenames as the tested fallback:

```tex
\IfFontExistsTF{Libertinus Serif}{%
  \setmainfont{Libertinus Serif}%
}{%
  \setmainfont{LibertinusSerif-Regular.otf}[
    BoldFont=LibertinusSerif-Bold.otf,
    ItalicFont=LibertinusSerif-Italic.otf,
    BoldItalicFont=LibertinusSerif-BoldItalic.otf]%
}
```

Apply the same pattern to Libertinus Sans and Libertinus Math. For monospace, try the installed Nerd Font family, then `JetBrains Mono`, then `JetBrainsMono-Regular.otf` with explicit bold/italic filenames, and finally retain the document's default typewriter face.

Compile a tiny font smoke-test document before rebuilding the full paper, and verify the resulting PDF with `pdffonts`. Do not accept a successful LaTeX exit as proof of correct fonts; fallback substitutions can still produce a PDF.

## 4. Normalize Graphviz diagrams

Set `fontname="Libertinus Serif"` on graph, node, and edge defaults. Use `face="JetBrains Mono"` only for commands, flags, paths, signals, return-code expressions, and other literal identifiers in HTML labels; keep conceptual state names and explanatory prose in Libertinus Serif.

Before rendering, locate the actual font file and verify Fontconfig resolves the requested family rather than silently choosing a fallback:

```bash
kpsewhich JetBrainsMono-Regular.otf
FONTCONFIG_FILE="$PWD/scripts/fonts.conf" fc-match "JetBrains Mono"
```

Include the directory returned by `kpsewhich` in `scripts/fonts.conf`; TeX Live's JetBrains Mono may live below `fonts/opentype/SIL/jetbrainsmono-otf`, so do not assume a `public/jetbrainsmono` path.

Graphviz can emit SVG carrying the requested family even when direct PDF output substitutes Helvetica. Render DOT to SVG, convert the SVG, and validate the produced PDF before replacing the tracked artifact:

```bash
FONTCONFIG_FILE="$PWD/scripts/fonts.conf" dot -Tsvg scripts/name.dot -o /tmp/name.svg
FONTCONFIG_FILE="$PWD/scripts/fonts.conf" \
  inkscape /tmp/name.svg --export-type=pdf \
  --export-filename=/tmp/name.pdf
qpdf --check /tmp/name.pdf
pdffonts /tmp/name.pdf
cp /tmp/name.pdf figures/name.pdf
```

If reliable font embedding is unavailable but exact visual typography is required, export text as paths and validate visually at high resolution; record that the resulting figure no longer has searchable text.

Size command nodes for the widest monospaced line with explicit width and padding, then route loopback arrows to an unobstructed border port. Mixed-font fragments placed side by side can collide after SVG/PDF conversion, so put code and explanatory prose on separate lines when final-size rendering shows crowding.

Treat alignment as a correctness requirement, not a cosmetic follow-up. For structured state diagrams, establish a shared centerline, equal-size peer nodes, mirrored branch geometry, centered border ports, and an unmistakable external retry loop before polishing fonts. Verify command semantics against the real CLI and wrapper scripts before labeling states: scheduler submission, allocated-job setup, inner launch, and retry monitoring are distinct stages. Include only stages that belong to the diagram's claimed scope. If scheduler submission is merely setup context for an in-job retry state machine, omit it rather than placing `qsub`/`sbatch` beside the launcher; if it is essential, put it in a separate upstream node with an explicitly directed edge. Never stack sequential commands as unlabeled peers. If automatic Graphviz layout produces crooked spines, inner-corner arrow landings, or hooked return paths, switch to explicit `neato -n2` positions and waypoint nodes rather than nudging labels around a bad layout. See [references/state-diagram-layout.md](references/state-diagram-layout.md) for the reusable construction and QA recipe.

For architecture diagrams, first classify the requested change as **visual repair** or **semantic redesign**. When the user complains about alignment, centering, typography, spacing, clipping, or box construction, preserve the existing visual metaphor, block inventory, labels, relationships, and color identity; make surgical layout improvements rather than replacing the architecture. Combine or reinterpret blocks only when the user explicitly requests it. When semantic restructuring is requested, define the primary claim and relationship types before drawing: separate orchestration from runtime, place data and checkpoints as lateral services, give checkpoint write/restore explicit bidirectional semantics, and keep communication libraries distinct from devices and named systems.

When integrating figures between a compact paper and a longer report, start from what the user asked for. If they asked to bring a redesigned figure or theme across, **adopt the redesigned source verbatim and rewrite the caption to match it** — a caption is generated text, not a veto on the figure. Treat “same design” as the whole visual grammar, not palette-and-font similarity: preserve the source medium where it enables the look, fieldset/notched-border construction, pale semantic fills, title tabs, corner radii, spacing rhythm, connector grammar, hierarchy, and typography roles. A recolored legacy topology is not a themed port. Detail the compact design drops is a reason to add that detail back into the redesign or to say so in prose, never a reason to silently keep the old figure. Copy the generator source (`.tex`/`.dot`), not just the rendered PDF, so the target repo can regenerate it; delete the superseded generator and update the render script in the same commit.

Layout is the only legitimate reason to decline an asset swap, and it is a reason to port the *encodings* into the wider generator, not to keep the old styling: a 6x1 single-column stack at ~234 pt wide cannot drop into a wide two-column report page. Compare aspect ratio and final placement width, and when they are compatible, prefer the exact asset — verify with `shasum -a 256` on both PDFs that the target really matches the source.

When an integration spans many figures, build an explicit per-figure disposition list before editing — exact replacement / full design-system port / chart-encoding port / deliberately unchanged — and report it to the user with the reason for every entry that is not exact. For each full design-system port, compare the rendered source and target side by side at final placement size; require the same component language, not merely matching hex values or font names. A silent omission reads as an oversight even when it was considered; an enumerated "not swapped, because the report version carries more data" is reviewable.

A delegated audit's recommendation is advisory, not authorization. When a subagent argues for preserving existing work and the user asked for the change, the user's request wins; re-read the actual request before acting on a child's conclusion.

Use fixed dimensions for peer boxes, centered ports, consistent padding, and a grid before tuning decoration. Place repeated rows on an explicit coordinate pitch larger than the card height; deriving each card position from independently spaced child nodes can make peer borders overlap even when every node is individually valid. Render at the exact LaTeX placement width early: a standalone figure can look polished while becoming unreadable or changing pagination in the paper. Compute the effective text size (`authored point size × placed width / native width`) and reject layouts that shrink secondary labels below the manuscript's readable range. Also estimate total placed height—including subcaptions and gaps—against `\textheight` before iterative float tuning. If the content cannot fit legibly, split it into semantically complete sequential figures with rewritten captions and cross-references; a `[p]` float does not make an over-height figure fit. If one-column placement makes labels too small, simplify content or use a compact full-width layout only after checking the page limit. Do not compensate with a sprawling redesign.

For border-legend or fieldset styling, use a true notched border whose label mask matches the page—not the box fill—so only the representative colored foreground title remains visible; the mask should cover only a short segment of the rule. Do not fake the effect with a full-width header strip or tinted title pill. Apply the treatment consistently to every peer title. Keep command and configuration inputs in separate, equal-size nodes with explicit center coordinates; ambiguous relative-position anchors can collapse them into one malformed compound shape. Enforce equality with explicit `text width` or fixed dimensions—not only `minimum width`, because longer copy can still expand one node and break symmetry. Keep code fragments in JetBrains Mono and wrap long commands before they approach a border. Reserve a connector lane that never crosses a border legend. When a connector must enter a top-center port, move the title notch away from that port; otherwise enter through a clear side port. A side rail may remain color-coded when color reinforces layer identity, but build each differently colored segment from the shared rail toward its destination; never begin it on the preceding segment's arrowhead, because overlapping strokes create split-color heads and slivers. See [references/architecture-diagram-layout.md](references/architecture-diagram-layout.md) for the scoped redesign decision table and QA recipe.

Verify regular, bold, italic, and mono faces are embedded when text remains live. Do not rely on `dot -Tpdf` merely because the DOT source names the desired font; the PDF backend may silently substitute Helvetica.

## 5. Normalize chart style and accessibility before release

Before applying this skill's publication defaults, inspect the target repository's existing chart generators and obey its established house style. For example, when a project specifies Ambivalent + Iosevka + transparent gray-text output, that contract overrides the Libertinus/opaque-paper defaults in this skill: require `ambivalent` rather than silently falling back, set `font.family` to `["Iosevka", "DejaVu Sans Mono", "monospace"]`, use the same family for mathtext, and save SVG/PNG with `transparent=True`. A checkerboard in an image preview indicates transparency and must not be “fixed” by forcing a white facecolor. Verify the real result by resolving the font with `font_manager.findfont`, checking PNG corner alpha, parsing the SVG, and visually reviewing the final image; source rcParams alone are not proof.

Run one paper-wide pass over every source-backed chart rather than polishing only the figures discussed most recently. Centralize defaults, but preserve intentional hierarchy: focal traces should normally be about 1.4–1.8 pt, raw/reference traces 0.7–1.0 pt, marker outlines 0.6–0.8 pt, and grids 0.4 pt in a pale neutral. Treat these as starting bands, then judge the rendered physical size.

Encode series identity redundantly whenever multiple traces share an axes: combine color with distinct markers and clearly different solid/dotted/dashed/dash-dot patterns. In dense checkpoint plots, increase marker size slightly but use `markevery` or subsampling so markers identify a run without becoming a beaded wall. Do not put a white edge on a tiny filled marker: the edge can consume the visible fill, especially for triangles on dotted lines. For small triangular markers, prefer a larger hollow white marker with a saturated series-colored outline, then verify its silhouette in both color and grayscale. Keep random baselines visually distinct from grids by changing both weight and dash pattern. For raw-versus-smoothed overlays, provide a compact style key and ensure the raw trace survives grayscale without competing with the focal trend.

Normalize legends by placement semantics: use frameless legends in reserved whitespace, opaque white legends when they overlap data on an opaque-paper figure, and a dedicated empty panel for crowded small multiples. On transparent house-style figures, keep legend frames transparent and move the legend into truly empty space; check its line samples as well as its text, because a reference line can cross the handles without obscuring the labels. Re-render and inspect after every legend move: a position clear of a reference line may still cover a low-valued data point. Order entries by meaning rather than plotting order. Normalize annotations similarly: use series color for series-specific callouts, neutral text for global notes, short leaders aimed at exact events, and explicit keys for symbolic markers such as minima or divergence placeholders.

Do not add `(a)`, `(b)`, and similar panel labels merely because a figure has multiple axes. Add them only when the prose or caption refers to panels by letter; otherwise retain descriptive panel titles or semantic references such as “top,” “lower,” or the metric name. Decorative labels add clutter without improving navigation.

Render every revised chart in color and true grayscale at its final publication dimensions. In grayscale, verify identities from line style and marker shape—not inferred color luminance. If a review flags a visually merged trace, first distinguish dash pattern, marker frequency, or z-order before making all lines heavier. Use the detailed checklist and decision table in [references/chart-style-accessibility.md](references/chart-style-accessibility.md).

## 6. Regenerate and validate as one release unit

Regenerate all source-backed figures that import the shared palette—even when their own source file did not change—then rebuild the paper and any standalone artifact description. Inspect the actual rendered pages and the key figures standalone; page-number assumptions are brittle after float reflow, so locate the rendered figure or use a uniquely named standalone preview rather than reviewing a guessed page filename.

Verify:

1. Every expected font family is embedded with `pdffonts`.
2. Labels remain legible at final column width.
3. No panel, trace, legend, or annotation disappeared during regeneration.
4. No clipping or overlap was introduced.
5. All counted figures remain inside the venue's page limit.
6. LaTeX has no unresolved references or overfull boxes.
7. `qpdf --check` and `git diff --check` pass.

Treat visual review as a correctness check: a typography migration can expose a pre-existing empty panel, caption/figure mismatch, or visibly crooked graph. When the user supplies a reference screenshot or names a source PDF, load it and compare it directly with the target render before claiming a match; source equality, shared colors, and embedded fonts do not prove visual equivalence. Inspect both the standalone asset and its rendered manuscript page, and explicitly audit centerlines, gutters between peer cards, symmetry, parent/child containment, arrow endpoints and direction, fieldset-title clearance, label clearance, text containment, trace identity, common cutoffs, and endpoint visibility. Make connector style agree literally with the caption's visual key: if dashed means cross-device communication, every cross-device edge—including stage handoffs and rings—must use that encoding, while local compute flow must not. Generate a uniquely named preview after the final render and inspect that exact file; stale preview paths can make a corrected source appear unchanged. Extract PDF text as a semantic check when source-only style tokens could leak into labels; search it for palette identifiers and unexpected words. Compare the result against the user's stated intent, not merely against generic design principles. When the user specifies an exact encoding—open versus filled markers, solid versus dashed lines, label order, or a palette role—implement it literally before applying generic aesthetic advice. Do not commit or push merely because the source builds or one visual pass says “no defects”; first inspect the final paper-sized rendering after the last edit and verify the requested semantics directly. Once the scoped change passes build and visual QA, commit and push in the same run when publication was already requested; do not report completion while verified changes remain only local.

## 7. Commit source and generated outputs together

For ML experiment and campaign reports, treat charts as part of the reporting deliverable rather than optional decoration. Before publication, map each decision-bearing table to a figure (training dynamics, checkpoint selection, full-test comparison, and capability/retention trade-off); if a figure is deferred, state that visibly in the report instead of silently shipping a table-only narrative.

Stage the shared style module, every migrated generator, diagram sources, regenerated PDFs, and LaTeX font configuration in one coherent commit. Verify the remote hash after pushing.

## Pitfalls

- **Probe font resolution before the full build** — family names may fail even when the files are present in TeX Live.
- **Inspect embedded fonts, not source declarations** — Graphviz and render backends can silently substitute Helvetica or another system face. Audit every final PDF, not only the manuscript: included PDFs retain their own font resources, and the manuscript-level font list can conceal which asset introduced a mismatch.
- **Separate family mismatches from encoding differences** — a Type 3 Libertinus subset is a legacy-output quality issue, while Libertinus Mono where JetBrains Mono is required is a semantic family mismatch; report and prioritize them differently.
- **Keep code typography semantic** — use JetBrains Mono for commands, paths, flags, signals, return codes, and identifiers; explanatory diagram text should match the paper serif.
- **Measure boxes after applying the mono face** — monospace commands are often wider than proportional text, so explicit node width and margin must be validated after the font change.
- **Separate adjacent mixed-font fragments when they crowd** — SVG/PDF converters can position independently styled spans too tightly, while line breaks remain stable at publication size.
- **Review at final physical size** — uniform source point sizes do not produce uniform perceived sizes after different LaTeX scaling factors.
- **Use open markers for secondary observations over coincident curves** — filled markers create a heavy beaded path and obscure the primary line; use a light-gray edge with no fill unless masking is intentional.
- **Keep reference smoothing subordinate but visible** — use a medium neutral dashed EMA and reserve the strongest chroma and weight for the focal run; if overlap hides the reference, raise its draw order before increasing visual weight.
- **Honor exact visual encodings literally** — if the user asks for an open marker, solid line, or specific semantic ordering, do not silently substitute a theoretically preferable style; render the requested mapping first and judge only legibility defects.
- **Encode related traces redundantly** — light/dark shades alone fail in grayscale; pair them with visibly different solid, dotted, dashed, or dash-dot patterns, while preserving any exact line style the user selected.
- **Preserve the requested visual concept during polish** — replacing a familiar diagram with a theoretically cleaner architecture can make it less immediately meaningful to its audience. This protects an *unrequested* redesign only; it never overrides an explicit instruction to adopt one. When the user names a custom theme, matching only palette and fonts is a failed port; reproduce component construction, hierarchy, whitespace, and connector language too.
- **Audit every shared figure, not just the ones under discussion** — a figure whose palette was updated can still be running the old generator and old design; diff each shared generator against its counterpart and hash the rendered PDFs, or a half-migrated figure ships looking finished.
- **Fold vertical-connector edge labels into the destination node** — Graphviz places an edge label on the line's midpoint, so a label on a long vertical arrow overprints the arrow and any cluster title it crosses; move the text into the node it points at and leave the connector bare.
- **Shrink the box, not just the font, when an HTML label overflows** — Graphviz sizes `shape=note` and similar shapes from label metrics, but a long unbroken monospace token (a module path, a full command line) still spills past the border. Break the token across explicit `<br align="left"/>` lines at semantic boundaries and re-render; repeated point-size reductions alone will not contain it.
- **Do not solve legibility by changing float width blindly** — full-width placement can alter pagination; simplify or compact first, then verify every counted float remains within the page limit.
- **Treat border legends as geometry, not decoration** — mask only the short rule segment, keep the mask neutral, and retain identity color in the title foreground and border.
- **Keep implementation color names out of rendered text** — TikZ style-argument mistakes can silently typeset palette tokens; extract PDF text and search for them before sign-off.
- **Simplify overview figures before shrinking type** — keep one or two role-level phrases per layer and move backend lists, environment variables, counts, and command matrices to prose; the figure should communicate its hierarchy at first glance rather than serve as a second implementation table.
- **Assign distinct layers perceptually distinct hues** — neighboring purples read as one category even when their hex codes differ; use a separate family such as teal. Once those layer hues become the paper palette, propagate their exact source values through one shared module and use style/marker redundancy when more series than hues must coexist.
- **Retain meaningful connector color when it aids layer identity** — build adjacent colored rail segments as separate paths that begin on the shared outer rail, not on the preceding segment's arrowhead, to avoid split-color heads and overprint slivers.
- **Preserve data provenance fallbacks deliberately** — figure regeneration should locate a canonical checked-out dataset or stop clearly, never silently retain an old PDF while claiming regeneration.
- **Model operational layers accurately in diagrams** — a scheduler submission command, allocated-job setup, inner launcher, and retry monitor are different stages; verify the executable call chain and label their ordering instead of compressing them into an ambiguous command list.
