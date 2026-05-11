# WeChat

## Profile

| name | workflow_mode | visual_planning | fixed_strategy |
| --- | --- | --- | --- |
| wechat | ax-poor | true | true |

## Match Terms

- WeChat
- 微信
- Weixin
- XinWeChat
- com.tencent.xinWeChat

## Planner Guidance

- WeChat often exposes incomplete Accessibility elements; use OCR lines, screenshot context, and profile regions when AX elements are missing.
- If `list-apps --best` selects WeCom/企业微信 for a plain WeChat task, rerun the compact matched list and explicitly choose `/Applications/WeChat.app` or bundle `com.tencent.xinWeChat`.
- To message a contact, first focus the search field candidate and type only the contact name.
- If `writetext` does not visibly populate the search field, paste the contact name with UTF-8 clipboard (`LC_ALL=en_US.UTF-8 pbcopy` plus `cmd+v`) and re-run OCR before selecting a result.
- After typing the contact name, select a visible matching OCR or AX result only when it is clearly inside the search-result or chat-list region and corresponds to a contact/conversation row.
- Use the top search-result profile region only after OCR or screenshot context confirms the target contact/conversation is the first result; otherwise wait and re-observe.
- When search results contain sections such as `最常使用`, `群聊`, `聊天记录`, or `包含：<name>`, prefer the direct contact row under the contact/frequent section. Do not select group rows or chat-history snippets that merely contain the same name.
- Only after the intended conversation is visibly selected in the chat header or conversation body should you focus the compose region and type the message body.
- Do not press Enter or finish unless the message body is visibly present in the compose box or appears in the sent message history.
- For sending meeting links or other structured messages, build the outgoing body from the trusted source text, paste it into the compose box via UTF-8 clipboard, then verify the visible draft contains the stable fields: recipient chat title, date/time, URL, meeting number or equivalent identifier, and requested reminder text.
- OCR can misread similar Chinese characters and URL case, especially after a message has wrapped or moved into chat history. For final verification, combine OCR with screenshot/visual inspection and the original clipboard/source string; do not "correct" a URL from OCR output alone.
- After pressing Enter to send, re-observe and treat the task as complete only when the compose box is empty and the just-sent message appears in the conversation history under the intended chat.
- For contact profile or Moments tasks, first verify the intended contact is selected in the chat header. Open the top-right chat info panel, click the contact avatar/name in that panel, and verify the profile card contains the intended name plus stable details such as nickname or WeChat ID before using profile actions.
- To open a contact's Moments from the profile card, click the "朋友圈" row content or thumbnails, then verify a separate Moments window/profile timeline is foreground. Clicking only the text label may leave the profile card unchanged.
- When a Moments detail or media popup appears, treat it as a separate window. Re-observe the popup title and frame before clicking visual-only controls.

## Moments, Likes, And Comments

- Interpret "first Moments post" as the first visible post in the opened timeline unless the user asks for the latest or non-pinned post. If a "置顶" label is visible, verify whether the visible first post is pinned and keep that distinction in the user-facing status.
- Before liking or commenting, verify the post context from the latest observation: contact name, popup title, visible caption/text, and, if present, date or "置顶".
- Moments action controls may be unlabeled or visual-only. Reveal them with hover or by opening the post detail, then re-run OCR/observe. Do not act on stale visual-planner coordinate summaries.
- If the controls are still unlabeled, use only one coordinate click derived from the latest active Moments window frame or same-step visual coordinate space. Re-observe immediately and stop to re-plan if no like/comment menu, input field, or visible state change appears.
- For comments, open the comment field, type or paste the exact requested text, and require the draft text to be visible in the comment field before submitting. Submit only after the active popup still shows the intended post.
- After a like or comment submission, re-observe the Moments popup. Treat the action as complete only when the liked state, comment text, or equivalent visible confirmation appears.

## Pitfalls

- Do not type the message body into the global search box.
- Do not treat every OCR match for the contact name as a selectable recipient; message history, files, meeting cards, and generic search suggestions can contain the same text.
- Do not assume the first chat list row or top search result is the intended recipient unless OCR or screenshot context confirms it.
- If AX is sparse, prefer OCR text match inside the relevant left-column result/list region before falling back to profile region centers.
- Do not rely on OCR alone for exact spelling of a contact name in the message body; OCR may confuse visually similar characters. Verify the active chat header and selected row instead.
- Do not mix screen coordinates from the main chat window, the right chat-info panel, profile card, Moments timeline, and Moments detail popup. Each can have a different active frame.
- Do not repeat nearby clicks on Moments visual controls after one failed attempt; re-observe or change strategy.
- Do not press Return to publish a Moments comment unless the comment draft is visible and WeChat's current UI indicates Return submits in that field or a visible submit button has focus.

## Profile Regions

| id | description | x | y | width | height |
| --- | --- | --- | --- | --- | --- |
| wechat_search_field | WeChat left-column search field; focus here before typing a contact name when AX search field is missing | 76px | 15px | 190px | 34px |
| wechat_top_search_result | WeChat first visible search result row; use only after OCR or screenshot context confirms this row is the intended contact/conversation | 64px | 50px | 250px | 78px |
| wechat_chat_list | WeChat conversation/contact list; use matching OCR text in this region to select a conversation | 64px | 90px | 250px | 70% |
| wechat_compose_box | WeChat bottom message compose box; use only after the intended chat is visibly selected | 37% | 72% | 60% | 24% |
| wechat_chat_info_panel | Right-side chat info panel after clicking top-right "..." in a chat; use only after the intended chat header is visible | 78% | 8% | 21% | 85% |
| wechat_profile_moments_row | Contact profile card Moments row; click the row content/thumbnails, then verify the Moments window opens | 54% | 30% | 40% | 12% |
