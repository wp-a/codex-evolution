# Codex Evolution 发布文案

以下是可复制的渠道文案。仓库目标地址为 `https://github.com/wp-a/codex-evolution`；发布前应确认仓库公开可访问。配图统一使用 `docs/marketing/` 中的图片，画面内的记录与统计均为合成演示数据。本文不代表已向任何社交平台发帖。

## 小红书

**标题：做了个工具，回看我怎么使用 Codex**

用 Codex 做了很多任务之后，我想把分散的对话整理起来：提示词有什么变化？某条观察对应哪些原文？项目里的规则有没有重复？哪些做法可以留到下一次？

于是做了 Codex Evolution，一个在本机运行的协作复盘工具。

它主要做四件事：

① 回看使用习惯：按月查看常用表达、任务信号与变化。
② 找到原文依据：点开统计，查看消息、来源文件与上下文。
③ 检查项目规则：审阅 AGENTS.md、Skill 和项目计划，得到带引用的建议。
④ 整理可复用方法：编辑提示词，把重复流程整理成待审阅的 Skill 草稿。

这次也把界面整理成了简洁的 macOS 风格，支持浅色和深色。第一次打开可以直接看示例，不用先交出自己的历史记录。

Python 3.10+ 就能从源码运行，零运行时依赖。记录默认留在本机；可选模型分析需要单独预览材料并同意。

图里的内容全部是合成演示数据。统计只描述记录中的行为，不能证明能力提升，也不会自动修改你的项目规则。

项目：github.com/wp-a/codex-evolution
MIT 开源许可，欢迎试用，也欢迎反馈导入格式和实际使用中的问题。

#Codex #开源项目 #AI编程 #开发者工具 #独立开发

**配图顺序：** `cover-zh.png` → `feature-overview.png` → `feature-evidence.png` → `feature-rules.png` → `feature-workflows.png`。封面介绍用途，后四张各讲一个具体动作。

## 朋友圈

最近做了 Codex Evolution：把与 Codex 的对话记录整理成一份可以回看的协作复盘。

能看提示习惯的变化、点开原文核对依据、检查项目规则，也能整理提示词与 Skill 草稿。用了简洁的 macOS 风格，默认在本机处理，Python 3.10+ 即可从源码运行。

图里是合成示例，产品不会给人的能力打分。代码采用 MIT 许可，欢迎试用和提建议。

https://github.com/wp-a/codex-evolution

**建议配图：** `cover-zh.png`、`feature-overview.png`、`feature-evidence.png`，三张即可。

## X / English

I built Codex Evolution: a local workspace to review prompting habits, trace observations to original messages, audit project rules, and draft reusable Skills.

Python 3.10+, zero runtime dependencies, MIT. Images use synthetic data.

https://github.com/wp-a/codex-evolution

**Suggested image:** `cover-en.png`. Optional second image: `feature-evidence.png` (the current app interface is in Chinese).

## 中文开源发布介绍

**标题：Codex Evolution：把历史对话整理成下一次协作的参考**

使用 Codex 的时间越长，历史里越容易积累许多值得回看的信息：最初如何描述需求，任务中如何继续推进，什么时候要求验证，以及哪些流程反复出现。

Codex Evolution 把这些记录整理成一个本地工作台。它提供从统计到原文、从规则检查到方法复用的一条路径，方便你理解自己的协作习惯，再决定下一次如何调整。

### 四个主要用途

**回看使用习惯。** 按月份、项目与时区查看常用表达、任务信号和消息特征；复盘报告保留统计分母与观察范围，可以导出 Markdown、离线 HTML、统计 JSON 或月度 CSV。

**回到原文核对。** 点击热力图中的数字，查看命中的消息、来源文件、行号与线程上下文。统计提供线索，具体含义仍可以回到对话里判断。

**检查项目规则。** 选择 AGENTS.md、AGENTS.override.md、SKILL.md 或项目计划，查看重复要求、潜在冲突与精简建议。建议带原文引用；明确的审批和权限保护会保留，应用不会自动应用修改。

**整理可复用方法。** 使用五类可编辑提示词模板，或从至少三个独立线程支持的重复阶段模式中生成 Skill 草稿。先检查证据与适用范围，再决定是否采用；导出草稿不会自动安装。

### 本地运行，也可以先看示例

界面提供功能介绍、明暗主题和移动端布局。第一次打开可以先探索合成演示数据，规则检查与提示词模板也不要求先导入个人历史。

需要 Python 3.10+，从源码运行没有额外运行时依赖：

```bash
git clone https://github.com/wp-a/codex-evolution.git
cd codex-evolution
python3 -m codex_evolution demo --open
```

个人历史需要显式导入。应用使用独立数据库，原始文件保持只读。默认的本地功能不需要 API Key，也不会发送模型请求；可选深度解读先展示证据材料，可复制给现有 Codex 会话，或在逐次明确同意后调用单独配置的 API。

### 如何理解这些观察

“验证”相关表达变多，不等于实际执行的测试变多；短提示可能依赖已有上下文；反复出现的流程也不一定有效。因此，报告描述有来源的记录变化，不将其包装成能力、人格或效率评分。

所有公开展示的截图与宣传图都使用合成演示数据，不代表真实用户测量结果。项目是独立社区作品，与 OpenAI 无隶属或背书关系。

代码采用 MIT 许可。欢迎体验，也欢迎通过 Issue 或 PR 提供导入格式支持、可访问性改进，以及使用合成数据构造的最小问题复现。

项目地址：https://github.com/wp-a/codex-evolution

**文章配图：** 开头用 `cover-zh.png`；四个用途后分别放 `feature-overview.png`、`feature-evidence.png`、`feature-rules.png` 和 `feature-workflows.png`。
