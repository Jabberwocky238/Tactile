# Debugging WindowsOS App Workflow Runs

Prefer the low-level interface script when diagnosing a failure. It separates
target resolution, UI Automation traversal, direct UIA action, coordinate
fallback, OCR, and LLM planning.

```powershell
python scripts\windows_interface.py observe Calculator --output $env:TEMP\calculator_observation.json
```

## Interface Checks

List real text inputs and virtual fallback regions from an observation:

```powershell
python scripts\windows_interface.py elements --hwnd 123456 --output $env:TEMP\window_interactives.json
python scripts\windows_interface.py elements --hwnd 123456 --view raw --output $env:TEMP\window_raw_interactives.json
python scripts\windows_interface.py traverse --hwnd 123456 --output $env:TEMP\window_tree.json
python scripts\windows_interface.py traverse --hwnd 123456 --view raw --output $env:TEMP\window_raw_tree.json
python scripts\windows_interface.py probe --hwnd 123456 --x 250 --y 59 --output $env:TEMP\point_probe.json
```

Start with `elements` for debugging normal app automation. It is the compact
UIA-derived list of actionable controls, including `uia_path`, frame, center, and
action hints. Use the full `traverse` output only when the compact list is not
enough.

For Electron/Chromium apps such as Feishu/Lark, Slack, Teams, and embedded
browser surfaces, ControlView may expose only windows/panes. Probe RawView before
using OCR:

```powershell
python scripts\windows_interface.py elements --target 飞书 --view control --output $env:TEMP\feishu_control.json
python scripts\windows_interface.py elements --target 飞书 --view raw --output $env:TEMP\feishu_raw.json
```

Raw `uia_path` values include the view segment, for example
`uia:123456:raw:root.children[4]`, and can be used with `uia` and targeted OCR.
If Feishu still reports only `Chrome Legacy Window`, inspect the
`accessibility_hint` field. The SDK will add app-profile `VirtualRegion` entries
with concrete frames for the profile/avatar verifier, bottom organization dock,
search, first result, and compose input.
Use `probe` on a `VirtualRegion.center` before clicking when a hover tooltip or
local label could disambiguate the target.

Directly operable elements expose `uiaPath` or `uia_path` values:

```powershell
python scripts\windows_interface.py uia click 123456 "uia:123456:root.children[3]"
python scripts\windows_interface.py uia click 123456 "uia:123456:raw:root.children[3]"
python scripts\windows_interface.py uia press 123456 "uia:123456:root.children[3]"
```

Use `uia click` for chat rows, search results, tabs, and other virtualized
surfaces where UIA `SelectionItem.Select()` reports success but the visible app
does not navigate. It resolves the UIA frame first and clicks the element center.

Open, traverse, and OCR without the LLM workflow:

```powershell
python scripts\windows_interface.py open Calculator --output $env:TEMP\calculator_open.json
python scripts\windows_interface.py elements --hwnd 123456 --output $env:TEMP\calculator_elements.json
python scripts\windows_interface.py traverse --hwnd 123456 --output $env:TEMP\calculator_tree.json
python scripts\windows_interface.py ocr --hwnd 123456 --uia-path "uia:123456:root.children[3]" --output $env:TEMP\calculator_element_ocr.json
python scripts\windows_interface.py ocr --hwnd 123456 --rect 100,200,360,80 --output $env:TEMP\calculator_rect_ocr.json
```

OCR output includes local OCR frames and `screen_frame`/`center` coordinates when
the OCR source was a window, element, or rect capture. Prefer these targeted OCR
calls over full-window screenshots.

Summarize a workflow log:

```powershell
python scripts\windows_interface.py plan-log $env:TEMP\windows_app_workflow.json
```

## Run Summary

Check:

- `final_status`
- target `hwnd` and `pid`
- number of steps
- whether execution mode was `uia_coordinate_click`, `coordinate`, `keyboard`,
  `unicode_stream`, or `clipboard_paste`

If UIA exposes only a top-level `Window` and a few panes, use OCR and cautious
coordinate hints. Do not retry the same stale element after a new top-level
window or dialog appears; list windows and switch to the new matching `hwnd`.
If a scan/login/auth page is observed even though the app is already logged in,
list running windows for the target app and prefer the larger or foreground
matching top-level window before asking the user to authenticate.
For WeChat specifically, verify `open 微信` returns either a recovered chat
window or `authentication_required: true`. The SDK tries Ctrl+Alt+W once to
restore the tray-hidden chat window before treating the QR login window as a
real blocker.

For Feishu/Lark specifically, use `Ctrl+K` for search when possible, and use the
bottom-left organization dock for account/organization switching. The top-left
avatar/profile card is only a verifier because the visible top-left name can be
the user display name and stay unchanged across organizations. Prefer:

```powershell
python scripts\windows_interface.py feishu-switch-org --target 飞书 --name 个人用户
```

If switching manually, click one bottom dock organization icon, open the
top-left profile card, and targeted-OCR that card to verify the requested
profile subtitle/team text. Do not click join, create, log-in-more-account, or
exit-login entries unless the user explicitly requested
account changes.
