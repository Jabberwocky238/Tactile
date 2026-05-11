# Tencent Meeting

## Profile

| name | uia_view | workflow_bias | visual_planning | fixed_strategy |
| --- | --- | --- | --- | --- |
| tencent-meeting | raw-uia-plus-popup-ocr | relist-after-dialog | true | true |

## Match Terms

- 腾讯会议
- Tencent Meeting
- WeMeet
- wemeetapp
- wemeetapp.exe

## Planner Guidance

### Lessons From Scheduling Runs

- If an old invitation window titled like `会议号：...` is open, `observe wemeetapp` may select it instead of the home window. Re-run `list-apps --query wemeetapp`, choose the `腾讯会议` home window or the `预定会议` dialog explicitly, and close only stale invite popups when they block scheduling.
- In Tencent Meeting 3.43, `uia set_value` on the start-time combo and keyboard navigation can report success without changing the visible time. Treat the visible field as authoritative. Open the time combo with `uia press`, target the `Qt680QWindowPopupSaveBits` popup, and use OCR/raw UIA after every wheel action.
- Do not click offscreen time rows even if RawView exposes them. Scroll until the target row is actually visible, then click the current visible UIA element or OCR center. In one verified run, positive wheel delta moved from early-morning slots toward later slots and a small negative delta moved back; probe direction with OCR before relying on it.
- The duration menu may render inside the schedule dialog rather than as a separate top-level popup. Click the duration arrow, choose the visible row such as `1小时`, then verify the raw/visible value changed. `set_value` on the duration edit can fail because the edit is disabled even though the menu is usable.
- If a warning says meetings with more than two participants may have a 40-minute limit, do not treat it as failed duration selection. Preserve the requested duration, mention the limitation only if it affects the user's expectation, and do not enable add-time-card options unless requested.

- Resolve Tencent Meeting from installed apps or windows first. On many systems the executable is `wemeetapp.exe`; keep the returned `hwnd`, `title`, and `frame`.
- To schedule a meeting, click or UIA-invoke `预定会议` once, then immediately re-run `list-apps --query wemeetapp`. The schedule surface commonly opens as a separate top-level window titled `预定会议`; do not keep retrying the main window when the click reports success but the main view does not visibly change.
- Inspect the schedule dialog with `elements --hwnd <schedule-hwnd> --view raw --all`. Recent Tencent Meeting builds expose the subject edit, date spinner, start-time combo box, duration edit, and `预定` button in RawView even when ControlView is sparse.
- Use UIA `set_value` for plain text fields such as subject only after focusing or selecting the correct edit element. If a time combo box accepts `set_value` but the visible value does not change, treat that result as inconclusive.
- For start-time selection, expand the time combo and treat the dropdown as a new popup window. Re-run `list-apps --query wemeetapp` and target the popup class/title, then use raw UIA elements or targeted OCR to locate the desired 15-minute slot.
- Scroll the time popup itself, not the parent schedule window. Use fresh popup coordinates or a popup `hwnd`; after each wheel action, re-read popup elements/OCR until the target slot is visible, then click the slot's current UIA element or OCR center.
- Before pressing `预定`, verify the subject, date, start time, and duration from the schedule dialog. OCR may render `10:30` as `1030`; accept that only when the same line also shows the expected date and end time/duration.
- After pressing `预定`, re-run `list-apps --query wemeetapp` and look for a new invitation window titled like `会议号：...`. Extract the invitation from the UIA `Edit` element value when available; use OCR only as a visual cross-check.
- Treat the UIA invitation text as the source of truth for meeting links and IDs. OCR often confuses link characters such as lowercase `l`, digit `1`, and uppercase `I`, or renders meeting numbers with noisy punctuation.
- When forwarding details to WeChat, use a single-line message or split into short sequential messages, then run one visual/OCR check of the target chat to confirm the sent time, link, and meeting number are visible.

## Scheduling Checklist

1. Resolve/open Tencent Meeting.
2. Invoke `预定会议`.
3. Re-list `wemeetapp` windows and switch to the `预定会议` dialog.
4. Fill subject/date/time/duration, handling the time dropdown as a separate popup.
5. Verify visible schedule details.
6. Click `预定`.
7. Re-list windows and read the invitation dialog's UIA `Edit` value.
8. Notify the requested chat recipient with preserved invite details.

## Pitfalls

- Do not assume a successful UIA invoke changed the current window. Tencent Meeting often reports success while the real state appears in a detached dialog.
- Do not mix UIA paths from the main window, schedule dialog, time popup, and invitation dialog. Each has its own `hwnd`.
- Do not rely on whole-window OCR for the meeting link. Prefer UIA text from the invitation field.
- Do not send a multiline meeting invitation through a shell command without verifying the visible chat result; line breaks may be truncated or interpreted unexpectedly.
