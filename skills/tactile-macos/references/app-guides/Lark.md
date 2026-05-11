# Lark

## Profile

| name | workflow_mode | visual_planning | fixed_strategy |
| --- | --- | --- | --- |
| feishu-lark | ax-rich | false | true |

## Match Terms

- Feishu
- 飞书
- Lark
- com.electron.lark

## Planner Guidance

- For organization switching, prefer the bottom account or organization controls exposed as AX buttons.
- After clicking `更多账号`, choose the target organization from the visible popup in the same workflow loop.
- Do not request a fresh target activation to inspect transient organization popups; focus changes can close them.
- Default to AX-rich without visual planning. The workflow should still use local OCR after AX; turn visual planning on only for an explicitly visual-only state, and never derive click points from a resized or rendered screenshot when a fresh AX/OCR screen point is available.
- For search fields, use focus plus real text input events. The runtime uses clipboard paste so the WebView receives an input event.
- If typed search text is visible but results remain unchanged, clear the field and paste the query again instead of duplicating text.
- For contact messaging, prefer entering the organization member directory from `通讯录` when global search does not produce a selectable contact. Do not press Enter from global search unless the selected result is visibly the exact target contact.
- Before typing or sending a message, verify the current chat header or compose placeholder contains the target recipient, for example `发送给 张三`.
- For message compose boxes, use current AX/OCR text or fresh screenshot context to verify that the message body actually appeared before pressing Enter.
- If the intended compose text is already visible in the current `AXTextArea`, do not write it again. Submit, finish, or explicitly clear and replace only when the visible text is wrong.
- For Chinese or other non-ASCII text, paste through the runtime clipboard path and verify the pasted body is visible. Shell diagnostics should use `LC_ALL=en_US.UTF-8 pbcopy` and `LC_ALL=en_US.UTF-8 pbpaste` rather than inheriting `LC_ALL=C`.

## Pitfalls

- AX value writes can make Accessibility text show the query while Feishu/Lark search does not run.
- Clipboard paste can report success even when the WebView compose box did not receive the message body.
- Organization popups are transient; reactivating or re-observing the target by name can close them.
- A visible search query is not enough evidence that the contact was found. Wait for a selectable result or switch to the organization directory path.
- Search history text and chat-list labels are not proof that the conversation is active. Verify the selected conversation header or compose placeholder before composing.
- Coordinate clicks in Lark are high risk because Retina captures, resized planner images, and rendered chat screenshots use different coordinate spaces. Follow `AX > OCR > visual planner`; use current AX element centers or OCR `screenCenter`; stop after one no-op instead of repeating nearby coordinates.
