# 改进工作台 · Improvement workbench

[项目介绍](../README.zh-CN.md) · [Usage guide](USAGE.md) · [用量数据说明](USAGE_DATA.md)

改进工作台帮助你把复盘后的想法带进下一次任务：准备任务简报，试一项改变，再把实际结果记下来。它在本机运行，不需要模型请求，也可以在没有导入历史时直接使用。

## 从哪里打开

运行应用后，点击侧栏的 **改进工作台**，或在当前服务地址后使用 `#improve`。例如默认地址为 `http://127.0.0.1:8765/#improve`。

演示数据下可以先试用操作；切换到个人数据后，简报和试验记录使用另一组本地保存空间。建议来自当前记录中的词面信号，是帮助你选方向的线索。

## 准备一次任务

四栏简报分别回答：

| 简报字段 | 要写什么 | 一个修复问题的例子 |
|---|---|---|
| 目标 · Goal | 这次要得到什么具体结果 | 修复筛选后列表仍显示旧结果的问题。 |
| 上下文 · Context | 当前状态、已有证据和相关材料 | 在搜索框输入关键词后切换月份即可复现；相关页面为列表页。 |
| 范围 · Scope | 涉及的区域和需要保留的限制 | 调整筛选与列表刷新流程，保留现有导出格式。 |
| 验收标准 · Success | 怎么确认目标已经达到 | 按复现步骤操作后显示对应月份结果；清空筛选可恢复全部记录。 |

填写后，点 **生成任务提示** 生成并保存右侧提示内容；未填写的项会标注“待补充”。可以继续编辑右侧内容，再点 **复制任务提示** 带到 Codex。**保存草稿** 可以保存后续编辑，**导出文本** 可以下载提示词文件。再次生成会更新右侧内容。

复制不会自动创建任务或发起模型调用。

## 尝试一项改变

1. 从页面建议里选一个适合当前任务的方向，点 **试试这个方法** 填入尝试表单，或自行填写。一次只试一项便于回顾。
2. 填写“这次调整什么”和“用什么判断是否有帮助”，点 **保存这次尝试**。例如：“任务开始前写清可重现的验收步骤”，标准是“完成时能逐项核对，不需要再解释期望结果”。
3. 在实际任务中使用它。工作台不会监控任务执行，也不会替你判定验收通过。
4. 任务结束后补充结果笔记。写下发生了什么、有哪些证据、还不确定什么。
5. 选择自己的判断，点 **保存结果**。状态包括“待观察”“有帮助”“没有帮助”和“暂不确定”；后三种需要填写观察依据才能保存。下一次遇到类似任务时，可以回看这份记录再决定是否沿用。

例如，结果笔记可以写：“这次给出两条复现步骤后，最终回复逐项说明了检查结果；仍需要在另一类问题上继续观察。”这比只写“效率提升了”更方便日后判断。

保存时会附上当前记录的基线：日期范围、自然消息数、单独“继续”率和验证词命中率。它们说明你是在什么记录背景下做了尝试，不是效果评分，也不会自动把后续变化归因于这项调整。编辑尝试会保留最初的基线。

已保存条目可用 **编辑尝试** 修改，也可以删除，删除需要再确认。每种数据模式最多保留 100 条记录；达到上限时先导出备份，再删除不再需要的条目。

## 记录如何保存

输入时内容先留在当前页面内存；点击 **生成任务提示**、**保存草稿**、**保存这次尝试** 或 **保存结果** 才会写入浏览器 `localStorage`。若页面提示保存失败，先导出留存，关闭页面可能丢失未保存的内容。

已保存简报和试验记录与应用的 SQLite 历史数据库分开。保存范围是当前浏览器、同一服务地址，包括协议、主机名与端口：

- `127.0.0.1:8765` 与 `127.0.0.1:9000` 使用不同的保存空间。
- `localhost:8765` 与 `127.0.0.1:8765` 也不同。
- 换浏览器、浏览器配置文件，或清除站点数据后，原记录不会自动出现。
- 演示与个人数据的简报、试验记录相互隔离。

使用固定端口和同一浏览器便于连续回顾。需要留存时，点 **导出改进记录** 下载 JSON；导出包含当前简报、尝试草稿、已保存条目及其基线汇总，也包含自己写入的目标、上下文、验收标准和结果笔记，分享前请检查。当前不提供跨设备同步，不要把只存在浏览器里的记录当作已有备份。

## 怎样理解建议与结果

词面信号只描述已导入记录中的表达，不能判断所有实际操作。出现“验证”不等于已经执行验证；短提示也可能依赖充分上下文。页面建议需要结合当次任务决定是否采用。

“有帮助／没有帮助／暂不确定／待观察”是你主动记录的判断，应用不会据此生成能力排名或自动效率评分。不同任务的难度、上下文和工具状态可能不同，一次结果不能证明某种提示方法产生了因果上的提升。

Token 用量可以提供另一条观察线索，但用量减少不一定意味着结果更好。应把它与自己的验收标准和实际结果一起看；数据覆盖与累计快照规则见[用量数据说明](USAGE_DATA.md)。

## English reference

Open **改进工作台** (`#improve`) to prepare a brief with **goal, context, scope and success criteria**. Click **生成任务提示** to generate and save it, then **复制任务提示** to use it in your next Codex task. Save one change to try with an acceptance criterion, and return after the task to add a result note and your own helpful/not-helpful/inconclusive/pending assessment. A non-pending assessment requires a written observation.

The workbench runs without model configuration or imported history. Suggestions are based on recorded wording, not automatic judgments of task success. Your assessment is a personal observation, not a causal finding or an efficiency score.

Inputs remain in page memory until a generate or save action. Saved briefs and trials use browser `localStorage`, scoped to the current browser and service origin. Demo and imported-data entries are separate. Changing the hostname or port creates another storage space; clearing browser data may remove entries. Export JSON to retain a copy, and review its written contents before sharing. There is no cross-device synchronization.
