# WeChat

## Profile

| name | uia_view | workflow_bias | visual_planning | fixed_strategy |
| --- | --- | --- | --- | --- |
| wechat | sparse-uia-with-profile-regions | targeted-ocr | true | true |

## Match Terms

- WeChat
- 微信
- Weixin
- XinWeChat
- com.tencent.xinWeChat

## Planner Guidance

- Open WeChat first and keep the returned `hwnd` and `frame`. Skip broad app listing unless the target is ambiguous or open fails.
- For routine one-recipient messaging, prefer the fast path: `.\bin\tactile-windows.cmd wechat-send-message --chat "<name>" --message "<text>"`. It bundles search, open, compose, existing-draft replacement, OCR checks, and send into one command, uses direct Win32 input by default, then focuses the compose area and presses Enter to send.
- For high-value details such as meeting links, meeting numbers, addresses, or codes, pass a single-line message or split the notification into short sequential messages. Multiline command arguments can be truncated or interpreted differently by the shell/chat input path; visual-check the sent bubble when preservation matters.
- Do not preflight with a separate dry-run or character-code probe for normal user-supplied Chinese text. PowerShell console output can render UTF-8 JSON as mojibake while the saved JSON/string value remains correct.
- Use `--draft-only` when the user asks to prepare but not send, `--dry-run` to inspect computed coordinates only for debugging, `--sdk-input` if direct Win32 input is blocked by focus or policy, `--send-method button` only when Enter is known not to send in that WeChat setup, and `--keep-existing-draft` only when appending to an existing draft is intentional.
- Run `elements --target 微信` once. If it only returns sparse `Window`/`Pane` content, continue with frame-relative profile regions and targeted OCR instead of repeatedly scanning RawView.
- Convert local profile-region points to screen coordinates from the latest `frame` immediately before each click or OCR crop.
- Search/open a contact by clicking the search field, pressing `ctrl+a`, pasting the full contact name, waiting briefly, and pressing `enter`.
- Verify the opened chat with targeted title OCR before typing the message body. Chinese OCR may return mojibake; keep the OCR artifact in the command output and only require exact OCR matching with `--require-title-match` when OCR text is readable in the current environment.
- For Chinese contact names and messages, prefer `pastetext`; Unicode streaming may fail in WeChat.
- Before Send, refresh or trust only the latest `frame`, focus the compose area, and press Enter. Do not rely on the bottom-right Send button when the window is partially offscreen, scaled, or overlapped. Verify with one targeted check: the narrow compose region is clear or the recent sent-message region contains the outgoing text.
- For Moments, treat the timeline/detail popup as a separate window. Re-observe the popup `hwnd` and frame before likes, comments, or visual-only controls.

## Default Profile Regions

The following are local coordinates relative to the current WeChat window frame. Convert to screen points with `screenX = frame.x + localX` and `screenY = frame.y + localY`.

| id | description | local_x | local_y | width | height |
| --- | --- | --- | --- | --- | --- |
| wechat_search_center | Left-column search box center | 125 | 55 | 1 | 1 |
| wechat_title_ocr | Chat title OCR rect | 235 | 35 | 260 | 40 |
| wechat_left_results | Search/results OCR rect | 70 | 40 | 165 | 360 |
| wechat_compose_center | Compose area center | max(260,width*0.45) | height-85 | 1 | 1 |
| wechat_send_center | Send button center | width-60 | height-42 | 1 | 1 |
| wechat_draft_ocr | Compose/draft OCR rect | 220 | height-280 | width-250 | 240 |
| wechat_recent_sent_ocr | Recent sent-message OCR rect | 235 | max(90,height-590) | width-275 | 350 |

## Pitfalls

- Do not type the message body into the global search box.
- Do not assume the first chat list row or top search result is the intended recipient unless title OCR confirms the opened chat.
- Do not reuse absolute send coordinates after restore, focus change, window move, resize, or monitor/DPI change.
- Do not trust command success alone when the message contains links or codes. Confirm the recent sent-message region contains the preserved details, and send a corrective follow-up immediately if a line was dropped.
- Do not continue clicking Moments controls after one failed attempt. Re-observe or change strategy to avoid unliking or duplicate comments.
