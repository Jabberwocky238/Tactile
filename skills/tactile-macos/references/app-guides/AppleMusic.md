# Apple Music

## Profile

| name | workflow_mode | visual_planning | fixed_strategy |
| --- | --- | --- | --- |
| apple-music | ax-rich | false | true |

## Match Terms

- Apple Music
- Music
- 音乐
- com.apple.Music
- /System/Applications/Music.app

## Planner Guidance

- Apple Music is AX-rich enough for the default `workflow` path. Prefer `--mode auto` or explicit AX-rich execution with visual planning off unless a control is truly visual-only.
- Use the sidebar search text field for global music lookup. Do not confuse it with view-local filter controls that only narrow the current page.
- After setting the search field value, wait for the main content area to change into search results. Treat the query as unresolved until the query is still visible in the field and result sections such as `最佳结果`, `歌曲`, `专辑`, or `艺人` appear.
- Unless the user explicitly asks for the local library, prefer the `Apple Music` search scope over `你的资料库` and verify the visible scope toggle after the search loads.
- For track playback, prefer an exact title-and-artist match from `最佳结果` or `歌曲`. A matching album or playlist is only an intermediate navigation step, not proof that the target track is selected.
- If clicking a search result opens an album detail page, locate the exact track row in the album track list and play that row directly instead of pressing the album-level `播放` button.
- To start playback, double-click the track row or track container. If the first double-click only selects the row or opens the detail page, re-observe and then play the exact track row in the current view.
- Treat playback as complete only when the now-playing area changes to the expected song title and artist, and the progress display resets near `0:00`. A highlighted row alone is not enough evidence that the track is playing.
- If another song is already playing, verify that the prior now-playing metadata was replaced by the requested song before finishing.
- For queue actions such as `下一首播放` or `最后播放`, open the track `更多` menu or context menu from the exact track row, then verify the queue action label before clicking it.
- If the query is visible but results look stale or unrelated, clear the search field and set the full query again rather than appending more text to the existing search.

## Pitfalls

- The search field and filter field are not interchangeable. Using the filter field can leave the app on the current page without searching the Apple Music catalog.
- A single click on a track often only selects it. A single click on a top result can also drill into an album or artist page instead of starting playback.
- Album-level controls can start the wrong track for the user's request. Verify the specific track row before any play action when the request names a song.
- A selected track row is not enough evidence that playback switched. Always verify the now-playing title and artist.
- Apple Music can keep showing old now-playing metadata for a moment after navigation. Re-observe before concluding the requested track failed to play or already played.
