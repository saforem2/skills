# State-diagram layout

Use this recipe when Graphviz's automatic layout produces a technically valid but visibly crooked publication diagram.

## Build geometry before typography

1. Pick a primary axis and place all main states on it.
2. Give peer terminal states identical dimensions and equal offsets from the axis.
3. Route the main flow through exact north/south ports.
4. Route branches from one centered fork to each terminal's top center so they are true mirror images.
5. Route retries outside the state boxes with explicit waypoint nodes; keep the arrowhead at the destination and the label beside, not on, the return path.
6. Add label-only `shape=plain` nodes after connector geometry is stable. This avoids Graphviz moving edges to accommodate multiline labels.

For deterministic placement, use pinned `pos="x,y!"` coordinates with `layout=neato` and render using `neato -n2`. Hidden point nodes are useful for forks and loop corners. Prefer straight segments or a small number of deliberate bends over generated splines with hooks.

## Node and label rules

- Center every multiline label as one block; do not visually align each line by manual spaces.
- Use equal width and height for sibling outcome nodes even when their text lengths differ.
- Keep commands, flags, paths, signals, and return-code expressions in the configured monospace family; keep state names and explanatory prose in the manuscript face.
- Size command boxes after applying the monospace face, with visible padding on every side.
- Put mixed-font fragments on separate lines when conversion makes adjacent spans collide.
- Keep edge labels on a consistent side of their edge with enough clearance that color is not the only association cue.

## Render and validate

Render to a temporary artifact first, validate it, then replace the tracked PDF:

```bash
FONTCONFIG_FILE="$PWD/scripts/fonts.conf" \
  neato -n2 -Tsvg scripts/diagram.dot -o /tmp/diagram.svg
FONTCONFIG_FILE="$PWD/scripts/fonts.conf" \
  inkscape /tmp/diagram.svg --export-text-to-path \
  --export-filename=/tmp/diagram.pdf
qpdf --check /tmp/diagram.pdf
```

Then rebuild the manuscript and inspect both the standalone diagram and the final page raster. Check explicitly:

- one continuous centered main spine;
- centered text inside every node;
- equal and aligned peer nodes;
- mirrored branches landing at top centers;
- clearly directed retry loop outside the nodes;
- no label/line near-collisions;
- no clipping or overflow at final column size;
- no Graphviz routing warnings or missing arrows.

If review finds a geometry defect, fix the source and rerender before committing. A successful build and readable text do not compensate for visibly poor alignment.