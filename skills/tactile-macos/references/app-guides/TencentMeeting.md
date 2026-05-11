# Tencent Meeting

## Profile

| name | workflow_mode | visual_planning | fixed_strategy |
| --- | --- | --- | --- |
| tencent_meeting | ax-poor | true | true |

## Match Terms

- Tencent Meeting
- TencentMeeting
- 腾讯会议
- VooV
- com.tencent.meeting
- /Applications/TencentMeeting.app

## Planner Guidance

- For scheduling meetings, prefer the manual `observe`/OCR/AX/input path instead of `workflow`. The Tencent Meeting scheduling UI is picker-heavy and AX-poor enough that workflow runs can stall or spend many steps on slow dropdown scrolling; use workflow only for inspection if absolutely necessary, not for executing the booking.
- Tencent Meeting scheduling controls can expose AX elements while still ignoring direct value writes. A command such as `axsetvalue` may report success even when the visible picker-backed field remains unchanged. Trust the latest visible AX/OCR observation, not the command success text.
- For scheduled meetings, resolve relative dates to a concrete calendar date before touching the UI. Example: if the current date is 2026-05-12 in Asia/Shanghai, "一个周三下午两点到三点" should be treated as 2026-05-13 14:00-15:00 unless the user states otherwise.
- Use pickers/dropdowns for date, start time, and duration whenever possible. Do not directly type or AX-write values into these fields as the first strategy.
- Date setting: open the start-date calendar/selector, navigate to the target month if needed, and choose the target day from the selector. After closing the picker, re-observe and verify the visible date and weekday label. Avoid typing strings such as `2026/5/13` unless the selector is inaccessible or blocked.
- Start time setting: open the `时间编辑框` dropdown and select the exact visible option such as `14:00`. If the dropdown shows offset options such as `00:15`, `01:15`, etc., do not assume text entry will correct it. Use the dropdown/scroll selector to reach the target hour and minute, then verify the closed field reads `时间编辑框 14:00`.
- Start time dropdown efficiency: options are 15-minute slots. Compute the slot delta from the current visible/selected time to the target time before scrolling or pressing keys; for example, from `00:30` to `09:00` is 510 minutes, or 34 down-arrow steps. Prefer sending the calculated bounded number of `down`/`up` keypresses followed by `enter`, or use larger bounded scrolls based on the visible time range, instead of repeatedly small-scrolling and rechecking every few slots.
- Duration setting: open the meeting duration control, usually labeled `选择会议时长`, and choose `60分钟` or `1小时` from the dropdown. Do not directly set a text field to `60分钟` unless the dropdown cannot be operated.
- Re-observe after each picker commit: date, start time, and duration should each be verified independently before pressing `预定`.
- Do not press `预定` until the latest observation shows the intended concrete date, `14:00` start time, and `60分钟` duration. If any one visible value is stale, fix that selector before proceeding.
- If the workflow starts repeatedly scrolling the start-time dropdown without reaching the target time, stop it and take over manually. Run OCR on the Tencent Meeting PID, find the visible time options, scroll the dropdown in larger bounded increments, and click only an OCR-visible exact option such as `14:00`.
- After selecting a start-time option, verify both OCR and AX when possible. The reliable closed-field AX text looks like `时间编辑框 14:00`; the reliable OCR line shows the concrete date and visible time near the `开始` label.
- For duration, the dropdown may expose options such as `15分钟`, `30分钟`, `45分钟`, `1小时`, `2小时`, and `3小时` as children in the current window. Click the visible `1小时` option for a 14:00-15:00 meeting, then re-observe the closed duration field before booking.
- After booking succeeds, Tencent Meeting may show the full invite in an `AXTextArea` inside a system dialog. Prefer extracting the invitation text, URL, meeting number, and meeting time from that AX text area over OCR, because OCR can misread Chinese names and URL letter case.
- Before sending a copied invite onward, verify the post-booking invite text contains the intended interval, for example `2026/05/13 14:00-15:00`, the meeting URL, and the meeting number. Use that trusted AX text as the source for downstream messaging.

## Pitfalls

- Do not use the end-to-end `workflow` execution path for routine Tencent Meeting scheduling tasks. It is slower and more failure-prone than manual observations plus targeted AX/OCR/input actions for date, time, duration, booking, and invite extraction.
- Direct AX writes to picker-backed fields can silently fail from the user's perspective even when the tool reports success.
- The start-time field may retain a stale value such as `00:15` after a direct write to `14:00`. Re-observation must catch this before scheduling.
- The duration field can look like a text field in AX, but scheduling intent is safer when selected through the duration dropdown.
- Calendar/date controls and time controls may appear in detached popups. Treat each popup as a separate active window and avoid using stale coordinates from the main scheduling form.
- OCR screenshots and TSV coordinates can use negative screen coordinates on multi-display or off-origin desktop layouts. Negative coordinates are valid for `input click` only when they come from the latest OCR/AX observation for the active Tencent Meeting window.
