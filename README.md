<p align="center">
  <img src="assets/logo.png" alt="Tactile logo" width="160">
</p>

# Tactile

**让 Agent 优先通过无障碍语义操作软件。**

> Stop guessing pixels. Start touching semantics.  

Tactile 不是另一个 computer-use agent。
它是一套让 agent 优先通过无障碍语义操作软件的 skill、协议和工具层。

当 agent 需要操作软件时，Tactile 希望它不要一开始就看截图、猜坐标、点像素，而是先尝试读取软件已经暴露出来的无障碍语义：

- 这个元素是什么角色？
- 它有没有名字？
- 它现在是否可点击、已选中、已聚焦？
- 它在界面层级里处于什么位置？
- 它是否提供可以直接执行的动作？

就像盲杖一样。

这些信息本来是为了屏幕阅读器和辅助技术而存在的。Tactile 希望把它们也变成 agent 操作软件的第一入口。

**Agent-ready software should also be human-accessible software.**

---

## Demo

**Tactile gives agents a sense of touch.**

---

## 如何使用Tactile？

对任意agent输入"帮我配置这个skill：https://github.com/yliust/Tactile"
环境中配置好api key即可:
~~~txt
export OPENAI_BASE_URL=xxxxxxx
export OPENAI_API_KEY=xxxxxxx
~~~

---

## 为什么需要 Tactile？

今天的 computer-use agent 往往从屏幕截图开始：

```txt
看截图 -> 猜元素 -> 预测坐标 -> 点击 -> 再看截图
```

这种方式很通用，但也很脆弱，Tactile 尝试把操作顺序换过来：

```txt
先读无障碍语义 -> 再用 OCR 辅助定位 -> 最后才退回截图识别和坐标操作
```

Agent 不应该只是在屏幕上“看见”软件。  
更理想的方式，是先“触摸”软件的结构。

---

## Tactile v0 

Tactile v0 会先以 skill 的形式出现。

它的目标是把一套 accessibility-first 的操作方法封装给 agent：

1. **优先使用无障碍语义**

   如果系统或应用暴露了可用的无障碍信息，agent 应该优先通过元素角色、名称、层级、状态和动作来理解并操作界面。

2. **语义不足时使用 OCR + 坐标定位**

   如果目标元素没有完整的无障碍适配，但屏幕文字仍然可读，agent 可以使用系统 OCR。在文字清晰的按钮操作下，这可以消耗更少的token及时间，快捷，方便，无障碍的建设助力人类和agent。

3. **最后退回 agent 自己的视觉操作逻辑**

   如果无障碍构建不可用，OCR 也无法定位目标，或者当前应用本身是画布、游戏、远程桌面、图片化界面等场景，agent 可以退回自身或其他工具的操作逻辑。

Tactile 提供的是操作策略和方法工具，不强行接管 agent 的全部判断。  
具体什么时候降级、什么时候重试、什么时候交还给 agent 自己的逻辑，仍然由 agent 根据任务上下文决定。

---

## 工作流程

Tactile 推荐 agent 遵循下面的操作阶梯：

```txt
Level 1: Accessibility semantics
  读取无障碍语义树
  根据元素名称、角色、状态和动作操作界面
  适合按钮、输入框、菜单、表格、弹窗、列表等标准 UI

Level 2: OCR-grounded coordinates
  使用系统 OCR 读取屏幕文字及其坐标
  通过文字位置辅助点击、输入和验证
  适合无障碍适配不完整但文字可见的界面

Level 3: Native visual computer use
  使用 agent 原有的截图识别、视觉推理和坐标操作
  适合图像化界面或语义完全缺失的场景
```

人类和agent，可以在一条路上快速通行。

---

## 验证原则

Tactile 关注的不只是“点到了哪里”，还包括“是否真的完成了任务”。

因此每次操作后，agent 应该尽量进行验证：

1. **优先用无障碍状态验证**

   例如按钮是否变为 disabled、复选框是否 selected、输入框 value 是否更新、弹窗是否关闭、列表是否出现新条目。

2. **无障碍状态不足时，用 OCR 验证**

   如果界面文字发生变化，agent 可以用 OCR 检查目标文本、错误提示、成功状态或页面标题是否出现。

3. **最后再用截图视觉验证**

   当语义和 OCR 都不足以判断时，再使用截图识别和视觉推理确认结果。

验证失败不一定意味着操作失败，但它应该提醒 agent：当前界面缺少足够可靠的语义反馈，可能需要重试、换路径，或者退回更通用的视觉操作逻辑。

---

## 为什么做这样的生态？

很多时候，让agent更好用，需要更多的设计agent friendly的接口，但是有没有一种接口，可以既服务于人，同时服务于agent？我们发现，如果agent使用无障碍入口，可以获得很好的工作效果。同时，如果 agent 开始优先依赖无障碍入口，很多过去不容易被发现的问题会变得更明显：

- 按钮没有可读名称
- 控件 role 不准确
- 弹窗无法被语义树读取
- 状态变化没有暴露给辅助技术
- 自定义组件只对视觉用户可见
- 键盘和屏幕阅读器路径不完整

这些问题会影响 agent，也会影响真实用户，尤其是依赖屏幕阅读器、键盘导航和辅助技术的人。

Tactile 的远景不是只让 agent 更会操作电脑。

它也希望推动软件生态更认真地暴露语义结构，让“agent-ready software”同时也成为 “all human-accessible software”。

---

## 当前状态

Tactile 目前处于早期阶段。

以skills的形式接入codex，在早期测试中，对于无障碍适配较好的 macOS 应用，accessibility-first 流程可以显著减少截图推理和坐标重试。

我们发现，当前即使是top100的应用也并没有足够多的无障碍适配，同时适配不断变迁的agent接口也已让人应接不暇，何不并入同一条轨道？

为尚为做好无障碍适配的软件做interface是我们的进一步目标。

---

## Join us

如果你关心 Agentic AI、桌面自动化、操作系统，无障碍技术、或者只是相信软件应该更容易被agent和所有人使用，欢迎一起参与 Tactile。

**Accessible to humans. Operable by agents.**
