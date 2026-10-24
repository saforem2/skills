# Architecture Diagram Layout

Use this reference when polishing or restructuring architecture figures for papers.

## Decide the scope first

| User signal | Default action |
|---|---|
| Alignment, centering, padding, font size, clipping, messy arrows | Preserve blocks, labels, relationships, and color identity; repair geometry only. |
| “Combine these blocks” | Merge only the named or obviously redundant blocks; preserve the surrounding flow. |
| “Rethink the architecture” or factual relationship is wrong | Redesign semantics, then update the caption and nearby prose. |
| Reference image supplied for border treatment | Reproduce the treatment, not unrelated content or layout from the reference. |

When scope is ambiguous, choose the least destructive interpretation and proceed without repeated approval prompts.

## Geometry-first workflow

1. Record the intended reading order and every existing block before editing.
2. Choose the final LaTeX placement width before selecting font sizes.
3. Establish a grid: fixed widths for peers, shared row baselines, exact centerline for sequential nodes, and named ports for arrows.
4. Place and size text before routing connectors. Wrap monospaced commands explicitly; never trust automatic wrapping near a border.
5. Route arrows after node geometry stabilizes. Arrowheads must remain visible after PDF scaling and must land on the intended side or center port.
6. Render the standalone asset and the compiled manuscript page. Inspect both at the final physical size.
7. Check float page numbers and total pagination after any aspect-ratio or one-column/two-column change.
8. Commit source and generated outputs together only after the final rendered-page inspection.

## Fieldset-style border labels

A fieldset label should interrupt only a short segment of the border:

- Draw the box first.
- Place the label centered vertically on the border.
- Give the label a background matching the page or box interior so it masks the rule behind the text.
- Use minimal horizontal padding around the label.
- Keep a visible border stub between the nearest corner and the label.
- Do not use a full-width colored cap or header band when the requested look is a border notch.

For TikZ, place a normal node on the box anchor with `fill=white`, small `inner xsep`, and no draw. For Graphviz, HTML-table approximations often produce cap-like headers rather than true notches; switch to TikZ when exact border interruption matters.

## Relationship grammar

Use no more than three connector styles, and document them visually or in the caption:

- solid control arrow: launches/configures;
- colored data arrow: supplies batches or tensors;
- dashed bidirectional arrow: save/restore state.

Do not use color merely because each destination box has a different hue. If retaining a rainbow stack by user preference, keep box colors as identity and use consistent high-contrast arrows unless destination-color arrows are already part of the established visual language.

## Final-size QA checklist

- Every peer box has equal width, height, padding, and corner radius.
- All text blocks are centered optically and geometrically.
- No command, path, or identifier approaches the border after scaling.
- Arrowheads remain visible, including short horizontal connectors.
- No connector crosses a label or disappears into a rounded border.
- Group labels do not collide with edges or content.
- Side services do not widen the canvas enough to shrink the main story.
- Body text is readable without zooming.
- The figure preserves the user's chosen visual metaphor.
- The compiled paper still satisfies its page and float-placement constraints.
