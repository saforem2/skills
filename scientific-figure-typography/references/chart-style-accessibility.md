# Chart Style and Accessibility

Use this reference for a paper-wide chart polish pass after typography and palette are already established.

## Procedure

1. **Inventory every source-backed chart.** Record the generator, final LaTeX width, number of series, marker use, line styles, grid, legend placement, annotations, and whether prose names any panel explicitly.
2. **Set a visual hierarchy.** Start with focal lines at 1.4–1.8 pt, references/raw traces at 0.7–1.0 pt, marker edges at 0.6–0.8 pt, and pale dotted grids at 0.4 pt. Preserve deliberate exceptions such as a stronger primary comparison.
3. **Add redundant encodings.** Give overlapping series distinct dash patterns and marker shapes. Do not rely on light/dark variants of one hue. Keep open markers for secondary observations that sit over lines.
4. **Control marker density.** For dense trajectories, use `markevery=max(2, len(x)//N)` or equivalent subsampling. Keep endpoint and event markers even when intermediate markers are sparse.
5. **Normalize legends.** Reserve whitespace when possible; otherwise use an opaque white frame above data. Order reference/baseline entries before experimental runs, or group entries by semantic family. Use an unused small-multiple cell for a shared legend when available.
6. **Normalize annotations.** Match series-specific callouts to the series color, keep global notes neutral, and use short leaders. Explain non-data symbols such as divergence placeholders or selected minima. Do not place stage labels where they collide with a legend.
7. **Decide panel labels from prose.** Add `(a)/(b)` only when the manuscript refers to those labels. If prose says “top panel,” “lower panel,” or a metric/benchmark name, descriptive titles are sufficient.
8. **Regenerate all affected outputs.** A shared palette/style edit requires rebuilding every importing generator, even when its script did not change.
9. **Run dual QA.** Rasterize both color and grayscale at the actual publication size. Check every series mapping, legend sample, baseline, marker, annotation, and endpoint. Then inspect the containing manuscript page for scaling and float effects.
10. **Validate and ship as one unit.** Run PDF integrity checks, LaTeX warning scans, page-count checks, and `git diff --check`; commit generators and regenerated PDFs together.

## Decision table

| Symptom | Preferred correction | Avoid |
|---|---|---|
| Coincident reference disappears | Raise its z-order; then modestly adjust neutral contrast | Recoloring reference data as a focal series |
| Two colored lines merge in grayscale | Assign clearly different dash patterns and markers | Depending on hue or subtle light/dark variants |
| Dense plot looks beaded | Increase marker size slightly and reduce frequency | Shrinking markers until they vanish |
| Random baseline looks like grid | Use a darker, heavier, different dash pattern | Making the entire grid darker |
| Legend hides data | Reserve a strip/empty panel or use opaque white frame | Transparent legend over active traces |
| Raw-versus-EMA meaning is unclear | Add a compact two-item style key | Repeating a full legend in every panel |
| Event annotation overlaps data | Move text to open space and use a short/curved leader | Placing text directly on the target curve |
| Panel letters have no prose references | Omit letters; retain semantic titles | Decorative `(a)/(b)` labels |
| Symbolic top-of-axis markers look measured | Break the data line and explain the marker as a placeholder | Connecting NaN/divergence symbols into the finite trajectory |

## Grayscale acceptance gate

A chart passes only if a reader can identify every overlapping series from line style or marker shape, distinguish baselines from grids, understand raw versus smoothed traces, and interpret special event markers without using color. Close overlap is acceptable when a residual/difference panel explicitly exposes the comparison and the legend mapping remains unambiguous.
