# PowerPoint

## Profile

| name | uia_view | workflow_bias | visual_planning | fixed_strategy |
| --- | --- | --- | --- | --- |
| powerpoint | control-first | file-or-com-before-ui | false | true |

## Planner Guidance

- Prefer deterministic file generation or editing for slide content. Use PowerPoint UI automation for export, verification, dialogs, and visual inspection.
- Resolve the active deck window with `list-apps --query PowerPoint` or `observe PowerPoint` before invoking UI commands.
- Use UIA for ribbon controls, dialogs, and save/export windows. Use targeted OCR only when the UIA tree omits visible labels.
- For destructive deck edits, save a copy or confirm the target file path before acting.
- When exporting to PDF or images, verify the output file exists and, when feasible, inspect the exported artifact rather than trusting a UI toast.
