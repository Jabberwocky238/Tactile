# Jianying / CapCut

## Profile

| name | workflow_mode | visual_planning | fixed_strategy |
| --- | --- | --- | --- |
| jianying | ax-rich-with-visual-fallback | true | true |

## Match Terms

- 剪映
- 剪映专业版
- Jianying
- CapCut
- VideoFusion
- VideoFusion-macOS
- com.lemon.lvpro
- /Applications/VideoFusion-macOS.app

## Planner Guidance

- For editing tasks, operate the visible Jianying UI. Do not bypass the app with local video-processing libraries or macOS media APIs when the user explicitly asks to use Jianying.
- Resolve the app with `list-apps --match '剪映|CapCut|Jianying|VideoFusion|lvpro' --compact`. On this machine, the installed app can appear as `/Applications/VideoFusion-macOS.app` with bundle id `com.lemon.lvpro`.
- Opening `/Applications/VideoFusion-macOS.app` may start only `VideoFusion-macOSTrayHelper`. If observation shows `VideoFusion-macOSTrayHelper` or no editor window, launch the main executable directly:

```bash
'/Applications/VideoFusion-macOS.app/Contents/MacOS/VideoFusion-macOS'
```

- After launch, use `pgrep -afil 'VideoFusion|CapCut|Jianying|Lemon|lvpro|剪映'` to identify the main `VideoFusion-macOS` PID. Prefer `observe --pid <main_pid>` for the editor; targeting the `.app` path can resolve to the tray helper instead of the main window.
- The editor is partly AX-visible but many useful controls expose implementation names such as `root_素材`, `root_转场`, `barImportViewBtn_`, `MainTimeLineRoot`, and `MainWindowTitleBarExportBtn`. Use AX for these stable hints, and use screenshots/OCR for visual-only state such as selected clips, timeline order, and hover-only buttons.
- The new project entry point can appear as visible text `开始创作` on the home screen. In the 2026-05-12 run, the AX text was `HomePageStartProjectName HomePageStartProjectDesp`; click the observed center or OCR-visible `开始创作`.
- To import local media, click the import card/button in the media panel. In the editor, the AX hint `barImportViewBtn_` identified the import button. The native file picker may appear as a sheet titled `请选择媒体资源`.
- In the native file picker, list view on Desktop exposed file rows through AX/OCR. Select exact target rows by name, for example `1 - Lark & WeChat` and `2 - Meeting`, then click the blue `导入` button. Importing large files can take several seconds; wait until the media panel shows both thumbnails.
- If the file picker or editor observation becomes slow or returns too much AX output, switch to a fresh screenshot plus OCR instead of repeatedly traversing the whole tree.
- Imported media thumbnails reveal the circular `+` / `添加到轨道` control only on hover. Move the mouse over the target thumbnail first, then click the visible plus button. Re-screenshot to confirm the clip appeared in the timeline.
- Jianying adds a thumbnail to the timeline at the current playhead. For ordered concatenation, add clip 1 first, then move the playhead to the end of clip 1 before adding clip 2. If clip 2 was added at the start by mistake, use `cmd+z`, click near the end boundary of clip 1, and add clip 2 again.
- Verify sequence order visually in the timeline before applying speed changes. A correct two-clip timeline should show `1 - ...` immediately followed by `2 - ...`, with the playhead at their boundary if clip 2 was inserted after clip 1.
- When a timeline clip is selected, the right inspector shows tabs including `画面`, `变速`, `动画`, `调整`, and `AI效果`. Use the `变速` tab to set speed. For a user request such as "每个视频十倍速", apply `10x` to each clip individually and verify the total duration shrinks by roughly 10x.
- For two clips, set the first clip to 10x, select the second clip, set it to 10x, then verify both clip durations/timeline total. Do not assume a speed setting applied globally unless the UI visibly says all selected clips are affected.
- To add a fade-style transition between clips, open top tab `root_转场`, search or browse for a simple transition such as `叠化`, `淡入淡出`, or `溶解`, then place it on the boundary between the two timeline clips. Re-screenshot and verify the transition marker appears at the cut.
- Before export, click `MainWindowTitleBarExportBtn` / visible `导出`. Choose Desktop as the output folder when requested. If the export dialog defaults elsewhere, use the dialog path/location control rather than assuming the visible project save path is the export destination.

## Pitfalls

- The `.app` target can resolve to the tray helper. If the observation app name is not `剪映专业版` or the visible elements are only menu items, switch to the main `VideoFusion-macOS` PID.
- Coordinates may be negative on multi-display layouts. Negative coordinates are valid only when they come from a fresh AX/OCR observation for the active Jianying window or file picker.
- The native file picker can obscure the editor and make OCR/AX calls slow. Save screenshots with unique filenames and verify current foreground state before clicking.
- The hover plus button on media thumbnails is easy to miss. A plain thumbnail click often only previews/selects media; it does not necessarily add it to the timeline.
- Adding the second clip while the playhead is still at `00:00` inserts it at the beginning and breaks numeric order. Always move the playhead to the end of the previous clip before clicking `添加到轨道`.
- Timeline total duration is a useful sanity check. The two source clips from the 2026-05-12 run were about `00:03:38:16` and `00:11:00:10`; before speed changes, the combined timeline showed about `00:14:38:26`.
- Some right-panel state changes depend on the selected timeline clip. If the right inspector still shows project/draft parameters, click the actual timeline clip before trying to set speed or visual properties.
- Do not trust a highlighted media thumbnail as proof it is on the timeline. Verify the timeline itself shows a clip block with the source filename.
- If clip order is wrong, `cmd+z` immediately after the mistaken add is safer than dragging long clips around on the timeline.
- Export can be slow for long 1440p H.264 videos. After starting export, wait for completion and then verify the expected output file exists on Desktop.
