# Feishu / Lark

## Profile

| name | uia_view | workflow_bias | visual_planning | fixed_strategy |
| --- | --- | --- | --- | --- |
| feishu-lark | auto-raw-after-control | uia-sparse-electron | false | true |

## Match Terms

- Feishu
- 飞书
- Lark
- com.electron.lark

## Planner Guidance

- Start with `elements --view control`, then use `elements --view raw` if the tree contains only windows, panes, or misses obvious list rows and buttons.
- Prefer UIA paths for exposed buttons and rows. For sparse WebView areas, use app-profile regions, targeted OCR, and `probe` before clicking.
- For organization switching, prefer the bottom-left organization dock. Use `feishu-switch-org --target Feishu --name <org>` when available.
- For message sends that involve an org switch, first run `feishu-switch-org`, then open the chat and draft the message. Keep the returned top-level `hwnd` and latest `frame`.
- Do not activate or reopen the target after a transient popup appears; re-observe the current `hwnd` so the popup does not close.
- Use `Ctrl+K` for global search when no search edit is exposed. For Chinese text, try `streamtext` first; if Unicode input fails, use `pastetext`.
- After entering a contact name in global search, OCR the result list as result rows. Click only a row whose primary/title text is the target contact, for example `张三` with a subtitle such as `示例部门`. Refuse rows where the target appears only in secondary text, snippets, or metadata such as `包含：张三`, `群消息更新于...`, `问一问：张三`, or a group name that merely contains the person.
- Before typing or sending a message, verify the visible chat title or compose placeholder matches the target recipient.
- Treat a cleared compose box after `Enter` as useful send evidence only after the target chat was verified. Recent-message OCR is helpful, but not always reliable on sparse Electron surfaces.
- `feishu-send-message` should run this fallback automatically. If `Enter` or `Ctrl+Enter` against the top-level Feishu `hwnd` returns success but the draft remains visible during a manual flow, target the Chromium child window that owns the compose surface:
  1. Run `elements --target 飞书 --view raw` or `probe` around the compose/input region.
  2. Identify the visible `Chrome_RenderWidgetHostHWND` child under the chat pane and use its `native_window_handle`.
  3. Click the verified compose center once, then run `input keypress enter --hwnd <child-native-hwnd>`.
  4. Verify the bottom compose region shows the "send to <chat>" placeholder or no longer contains the draft text.
  Do not re-run the full open-chat flow or paste the message again unless OCR shows the draft is missing or wrong.
- If a UIA action succeeds but the visible state is unchanged, re-observe and choose a different route before using one current center-coordinate fallback.

## Pitfalls

- AX-style value writes or semantic selection can report success without triggering Chromium search or compose behavior.
- Top-level Feishu window input can report keypress success while Chromium keeps the draft unsent. Use the compose child `native_window_handle` fallback before trying send buttons by raw coordinates.
- Search history, group-message history, snippets, and left-rail labels can contain the target name without being the active chat. Treat those as rejected OCR rows, not lower-priority candidates.
- RawView paths can change after focus, search, or virtualized list updates. Use the latest observed path.
- Coordinate clicks in Feishu/Lark are high risk on mixed DPI or moved windows. Use the latest `frame`, UIA center, OCR center, or profile region only once before re-planning.
