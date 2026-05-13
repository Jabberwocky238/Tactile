# Zoom

## Profile

| name | workflow_mode | visual_planning | fixed_strategy |
| --- | --- | --- | --- |
| zoom | ax-rich-hybrid | false | true |

## Match Terms

- Zoom
- Zoom Workplace
- zoom.us
- us.zoom.xos
- /Applications/zoom.us.app

## Planner Guidance

- Resolve relative meeting times to a concrete date before opening the scheduling UI. Use the local system date and timezone, then carry the concrete date through every verification. Example: if the system date is 2026-05-13 in Asia/Shanghai, "this Friday 8 PM to 9 PM" means 2026-05-15 20:00-21:00.
- Prefer manual AX targeting for Zoom scheduling. Zoom Workplace is a hybrid WebView app: it exposes many useful AX nodes, but the tree is large and includes duplicate or stale entries. Use filtered AX output to find schedule, date, time, calendar, and save controls instead of navigating by screenshots.
- Open Zoom by the installed app name or bundle, commonly `zoom.us` / `us.zoom.xos`. After opening, re-observe and confirm the signed-in main window before pressing `Schedule meeting`.
- The main home screen can expose both a top-level `Schedule meeting` button and a calendar-side-panel `Schedule a meeting` button. Either can open the scheduler, but prefer the main `Schedule meeting` action when present.
- Do not trust `AXValue` writes for Zoom scheduler date and time fields as the first strategy. In observed runs, date combo boxes were not settable, and direct writes to time combo boxes reported success but did not commit the visible field; one write even landed in the currently focused topic field.
- If a direct write mutates the topic field accidentally, restore the topic before continuing. Then switch to picker/dropdown selection for the remaining fields.
- For start and end dates, open the date combo box and click the exact date button from the calendar picker, such as `May 15 2026 Friday`. Re-observe after the picker closes and require both start and end date fields to show the target date, for example `5/15/26`.
- For start time, open the `Start time` combo box and select the exact visible option such as `20:00`. Re-observe the closed field and require the placeholder/value to show `20:00`.
- After setting the start time, Zoom may automatically adjust the end time to a default offset such as `20:30`. Open the `End time` combo box separately and select the requested end time, such as `21:00`; then re-observe the closed field.
- Time dropdowns may expose duplicate `AXStaticText` nodes with the same label. Choose the option under the currently expanded combo box's path and fresh frame, not a stale option from another collapsed combo box. The focused/expanded combo box is the best anchor for disambiguation.
- Use `Other Calendars` when the user only needs the Zoom meeting saved and invite text available. `iCal` or `Google Calendar` can launch an external calendar or sign-in flow and should not be chosen unless the user asked for that integration.
- Treat `Save` as the real scheduling action. If the user's initial instruction did not explicitly authorize saving/scheduling, verify all fields first and ask before pressing it. If the user already said to save directly, that is sufficient pre-approval.
- Before pressing `Save`, verify the latest observation shows the concrete date, start time, end time, calendar option, and intended topic. Do not rely on earlier action success output.
- After saving, verify success from the post-save dialog. Reliable signals include `Your meeting has been scheduled`, `Meeting Invitation`, and an `AXTextArea` containing the invite text with the topic and time, for example `Time: May 15, 2026 08:00 PM Beijing, Shanghai`.
- Do not treat the calendar side panel text `No meetings scheduled` as failure after a successful save dialog. That panel may be disconnected from Zoom Calendar or stale, while the invite dialog is the authoritative confirmation.

## Pitfalls

- Zoom AX frames can be negative or visually surprising on multi-display desktops. Negative coordinates are not inherently wrong. Prefer element-index AX actions when role, text, action, and path identify the target.
- Hybrid WebView nodes can keep stale frames or stale duplicate options after popups open and close. Refresh state after every dropdown, calendar picker, or save action before choosing the next element.
- A settable AX field is not proof that Zoom will commit the value. The closed-field text/placeholder from a fresh observation is the source of truth.
- Time options are 15-minute slots and can appear in more than one list at once. Never click a duplicate solely because its text matches; confirm it belongs to the active expanded start or end time combo box.
- Saving with external calendar options can move the task into another app. Use `Other Calendars` for a contained Zoom-only flow unless the user's task explicitly includes calendar integration.
- Post-save invite text is usually better than OCR for extracting details, because it is exposed as text in the Zoom dialog.
