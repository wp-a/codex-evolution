# Token 用量：来源、统计口径与导入格式

用量页回答的是：**当前导入的记录里，有多少次响应明确记录了 Token，用在什么月份、项目和模型上下文中。** 它不连接账户账单，不估算订阅额度，不根据消息长度猜 Token，也不硬编码模型价格。

## 两类记录分开看

| 来源 | 页面如何使用 | 不代表什么 |
|---|---|---|
| Codex rollout 的 `token_usage_record.payload.usage` | 按响应去重后汇总，支持月份、项目和模型视图 | 账户全量记录、实际账单或任务价值 |
| 标准化 `type: "usage"` 事件 | 导出者明确声明的单次响应用量，使用同一套去重规则 | 对任意第三方日志格式的自动识别 |
| 旧版 `event_msg` → `token_count.info.total_token_usage` | 每线程保留最近快照，单独显示为参考 | 可逐条求和的请求消费或可准确归月的增量 |

旧版 `token_count` 中的 `last_token_usage` 是最近一次采样的用量。重复通知可能仍携带相同快照；`info` 也可能为空。Codex 在表示上下文占满时，还能人工填写一个 `total_tokens = model_context_window`、其他计数为零的快照。因此本项目不会把旧快照与逐次响应相加，也不会通过累计快照的差额拼出账单。

旧快照若出现“输入与输出都是零，但总数大于零”的形状，会标记 `context_fill: true`，提示它可能是上下文填充。即使没有该标记，旧快照仍然只供参考。累计回退或重置不被解释为负消费或新一轮消费。

`compacted.payload.latest_token_usage_record` 是压缩检查点，包含已经记录的历史用量；本项目不把它算作新响应。

## 数字如何计算

- `input_tokens`：已记录输入 Token，包含缓存输入。
- `cached_input_tokens`：其中来自缓存的输入 Token，不再加到总量上。
- `output_tokens`：已记录输出 Token，包含推理输出。
- `reasoning_output_tokens`：其中的推理输出 Token，不再加到总量上。
- `total_tokens`：记录提供的总数；项目保留它，不把缓存或推理细分再次相加。
- `response_records`：去重后的逐响应记录数。一次用户任务可能对应很多次模型响应。

缓存或推理字段缺失时保留 `null`。只要某个汇总分组存在缺失，该组相应的细分合计也显示未知；`coverage.cached_input_records` 和 `coverage.reasoning_output_records` 给出有该字段的响应数量。已记录的零和没有记录的数据是两种状态。

没有逐响应记录时，总用量为 `null`，而不是 0。月份按所选时区划分。统计期间的空月保留，Token 显示未知。未导入、未持久化、其他设备、云端记录和不包含 usage 的响应无法由现有数据恢复。

## 去重、归属与筛选

逐响应身份是 `(provider, 原始 thread_id, response_id)`。同一响应被重导、复制到另一文件，或随 fork 历史一起复制时，只统计一次。不同 response ID 即使数值相同，也保留为不同响应。

提供方来自可选元数据，复制文件可能丢失该信息。相同 `(原始 thread_id, response_id)` 只有一个明确提供方时，`unknown` 副本与该提供方兼容去重，避免把元数据缺失当成新消费。两个不同的明确提供方仍各自保留；如果这时还有 `unknown` 记录，无法知道它属于哪一方，因此不将这些歧义行计入总量，单独记入 `coverage.ambiguous_provider_records`。这不是将未知提供方自动猜成 OpenAI。官方 Codex 记录结构不提供跨所有第三方提供方的 response ID 唯一性保证，所以不会直接删去提供方这个身份维度。

去重发生在日期和项目筛选之前。相同身份存在不同计数时，按时间、来源文件、行号和规范化内容确定固定胜者，并计入 `conflicting_response_records`；不会因导入列表顺序改变结果。所有重复行计入 `duplicate_response_records`，其中可能包含冲突行。

应用仍按“来源文件 + 行号”存储各自的导入副本。重新导入一个缩短或清空的文件，会替换该来源快照；另一个来源中的同一响应不会因此丢失。无需改变现有数据库结构。

Codex 用量记录使用其自身 `payload.thread_id`，不会把 fork 复制来的用量统一改成新线程。模型来自该记录对应的、此前出现的 `turn_context.model`；没有轮次标识时使用此前活动上下文，指定轮次却找不到时显示 `unknown`。项目优先来自对应上下文的 `cwd`。缺少模型、提供方或项目时，不从上下文窗口大小或文件名推断模型价格。

计量归属与“回看原文”入口分开处理：`thread_id` 保留原始用量所属线程，`evidence_thread_id` 指向实际已导入的原文线程。导入器记录本来源中普通消息使用的线程映射，分析器再确认同一来源确有该线程的自然用户消息后才提供入口。例如只导入 fork 文件，历史用量仍属于原线程，但可以回看 fork 中保存的原文。没有确切匹配时为 `null`；不会仅因另一个线程恰好在相同文件中就跳到它。多个可用副本优先选原属主原文，否则仅在目标唯一时提供入口。分享导出不包含这两个 ID。

模型视图表示**记录的模型上下文**。实际响应可能发生重路由，压缩请求也可能使用不同模型，所以这里不声称是实际计费模型。`threads` 最多返回用量前 20 个线程；跨模型的线程标为 `multiple`。旧快照表最多返回最近 20 个线程，完整覆盖数量仍在 `coverage` 中。

覆盖线程的分母是当前筛选范围内的已导入线程，不是账户实际全部线程。`invalid_usage_records` 统计能确定日期且处于当前筛选内的无效记录；无法确定时间的记录单独记在导入范围诊断 `unlocated_invalid_usage_records` 中，不能归到某个月。导入时已经拒绝的记录见导入诊断，不会凭空出现在分析结果中。

## 标准化 JSON / JSONL 示例

每行是**单次响应的增量**，不能把累计快照放进 `usage` 冒充一次响应。下面全部是合成数据。

```json
{"type":"usage","timestamp":"2026-09-01T10:00:02Z","thread_id":"synthetic-thread-1","project":"demo-project","provider":"example-provider","model":"demo-model","response_id":"synthetic-response-1","usage":{"input_tokens":1000,"cached_input_tokens":600,"output_tokens":200,"reasoning_output_tokens":120,"total_tokens":1200}}
```

`timestamp`、非空 `response_id` 及 `usage.input_tokens`、`usage.output_tokens`、`usage.total_tokens` 必须有效。Token 数值必须是非负整数，最多为 `2^53 - 1`；布尔值、数字字符串、负数和浮点数都不接受。缓存输入不得大于输入，推理输出不得大于输出。缓存和推理字段可以省略或为 `null`。

为确保跨文件去重和项目归属准确，应提供稳定的 `thread_id`、`provider` 和 `project`。未知模型可以省略，不要编造名字。`response_id`、模型和提供方标签不超过 200 个字符。

JSONL 可以混排普通消息与上述 `usage` 事件。JSON 文件沿用现有数组格式，或放在 `messages` 数组中：

```json
{
  "messages": [
    {"role":"user","thread_id":"synthetic-thread-1","timestamp":"2026-09-01T10:00:00Z","text":"检查这个合成示例"},
    {"type":"usage","thread_id":"synthetic-thread-1","timestamp":"2026-09-01T10:00:02Z","provider":"example-provider","model":"demo-model","response_id":"synthetic-response-1","usage":{"input_tokens":1000,"output_tokens":200,"total_tokens":1200}}
  ]
}
```

用量事件在应用内部存为 `role="usage"`、`channel="usage"`、`natural=False` 的独立记录，正文仅包含白名单字段：`kind`、`provider`、`model`、`response_id`、`counters`、导入器推导的原文映射 `evidence_thread_id`，旧快照另有 `context_fill`。标准化输入不能指定任意原文跳转目标。任意 `metadata`、原始上下文、额度快照和额外字段均不复制进该正文。

## 分享导出

`public_usage` 导出 `summary`、`monthly`、`models`、数值型 `coverage` 和固定口径说明，并保留格式版本、数据模式、经验证的时区和起止月份 `period`，方便正确解读月份。每一层均使用字段白名单，排除原文、来源路径、行号、线程/响应 ID、项目名称、筛选中的项目标识和旧快照详情。模型与提供方只允许简短 slug；路径、说明性文本和常见密钥前缀替换为 `unknown`。

分享前仍应检查聚合数值和自定义模型名称是否适合公开。

## 核验来源

Codex rollout 是内部、随版本变化的格式。本次于 2026-09-17 核验官方 `openai/codex` 提交 `da18000cae9884ab45f83b2d07fbd5a220a1de39`：

- [TokenUsage / TokenUsageRecord / TokenUsageInfo 定义与累计、上下文填充逻辑](https://github.com/openai/codex/blob/da18000cae9884ab45f83b2d07fbd5a220a1de39/codex-rs/protocol/src/protocol.rs#L2232)
- [rollout 的 token_usage_record 序列化及 compacted 检查点](https://github.com/openai/codex/blob/da18000cae9884ab45f83b2d07fbd5a220a1de39/codex-rs/history/src/rollout_payload.rs)
- [官方逐响应累计、恢复与缺失 usage 的测试](https://github.com/openai/codex/blob/da18000cae9884ab45f83b2d07fbd5a220a1de39/codex-rs/core/tests/suite/token_usage_rollout.rs)
- [旧 token_count 生命周期回放与避免重复持久化](https://github.com/openai/codex/blob/da18000cae9884ab45f83b2d07fbd5a220a1de39/codex-rs/app-server/src/request_processors/token_usage_replay.rs)
- [TurnContextItem 的轮次与模型字段](https://github.com/openai/codex/blob/da18000cae9884ab45f83b2d07fbd5a220a1de39/codex-rs/protocol/src/protocol.rs#L3280)
- [按实际响应模型统计的独立遥测](https://github.com/openai/codex/blob/da18000cae9884ab45f83b2d07fbd5a220a1de39/codex-rs/core/src/state/turn_token_usage.rs)
- [OpenAI Responses API：输入、缓存输入、输出与推理输出字段](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)
