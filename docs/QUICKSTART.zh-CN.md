# Codex Evolution：中文快速上手

## 启动演示

解压源码包，终端进入包含 `pyproject.toml` 的 `codex-evolution` 文件夹。

```bash
python3 --version
python3 -m codex_evolution demo --open
```

需要 Python 3.10+。启动后访问 `http://127.0.0.1:8765`。浏览器没有自动打开就手动输入地址；端口冲突可加 `--port 9000`。终端需保持运行；按 `Ctrl+C` 停止。

不需要执行 npm install，不需要安装 Python 第三方运行时依赖。这个版本没有公开 PyPI 发布，因此不要依赖 `pip install codex-evolution` 从网上安装。可选的 `python3 -m pip install .` 是安装当前本地源码。

默认打开“开始使用”页（`#start`），用三种用途介绍功能：回看使用习惯、检查项目规则、复用工作方法。点击“先看示例”会切换到明确标注的合成数据并打开“使用概览”；点击“导入我的记录”进入导入页。默认浅色主题，右上角可切换明暗，选择会保存在当前浏览器。

在“使用概览”中点击热力图的数字可以回到对话原文。随后可查看“复盘报告”，或直接使用“规则检查”“提示词模板”；后两者无需先导入历史。

“复盘报告”展示七项提示习惯变化、六行任务信号矩阵和标为 `heuristic` 的观察锚点，再给出谨慎读数与可选的长任务进度模板。顶部筛选器同时控制这些内容；少于三个活跃月份时显示数据不足的原因。词面命中率比较前后两期合并值，长度与短提示占比比较首末活跃月。展开“导出与分享”可下载报告，展开“下一次可以尝试什么”可准备模型复盘材料；统计说明与完整文字报告也按需展开。

## 导入自己的记录

```bash
python3 -m codex_evolution import "${CODEX_HOME:-$HOME/.codex}"
python3 -m codex_evolution serve --open
```

导入的是当前机器的可读取历史，不是云端账号全量。支持 `history.jsonl`、选定版本形态的 rollout JSONL，以及标准化 JSON/JSONL。页面“数据与隐私”也有显式路径输入与文件拖入。

界面上方切换“我的本机数据”。如果是空白，检查是否选错数据库或文件、是否有时间/项目筛选；导入诊断中查看坏行、未知事件和排除计数。重新导入刷新数据，不会自动监听新增历史。

原始 Codex 日志不变。应用副本保存在 `~/.codex-evolution/evolution.sqlite`。修改位置：

```bash
python3 -m codex_evolution --db ./local-workspace.sqlite import /你的历史目录
python3 -m codex_evolution --db ./local-workspace.sqlite serve --open
```

以上两个命令必须使用相同数据库。`--db` 要写在 `import` 或 `serve` 前面。

## 审查自己的指令

在“规则检查”里选择 `AGENTS.md / Skill 审计`。输入项目目录并点击读取，或者选择 Markdown 文件。通过选择文件输入时，请检查编辑器上方的相对路径，以便正确判断子目录作用域。

运行本地预审后查看：原句、位置、影响、建议、相关指令、权限扩大标记、必须保留的保护、建议 diff。没有“自动应用”按钮。导出的 `.patch` 只是文本建议，需要你另行审阅。

反冗余标签用于粘贴项目计划，不会自动扫描全部项目代码。它找出需要核实的问题，不把所有 Gate、SHA 或兜底一概删除。

## 深度复盘

成长报告或审计页可准备模型材料。先检查预览：可删除不想分享的原文，再“复制给 Codex”或导出任务包。这条路径不要求应用持有 API Key。

也能配置 API 后逐次同意发送。只有这一步联网；模型只分析选择的材料，没有执行工具。本机统计与模型材料覆盖范围不同：统计读取全部已导入支持记录，模型复盘最多看到 36 条节选和汇总。

## 导出

```bash
python3 -m codex_evolution report --format html --out my-report.html
python3 -m codex_evolution report --format md --out my-report.md
python3 -m codex_evolution report --format json --out statistics.json
python3 -m codex_evolution skills --out ./skill-review-drafts
```

统计报告与分享卡不包含原始消息或项目路径，但聚合信息本身也可能敏感。审计 JSON、diff 与模型任务包包含选定的指令原文，不能当作匿名文件直接公开。

## 本地开发与测试

```bash
python3 -m unittest discover -s tests -v
```

单元测试只需标准库。浏览器测试需额外安装 Playwright 与 Chromium，属于可选开发依赖，详见 `docs/QA.md`。系统没有 IANA 时区数据时选 UTC；非 UTC 时区依赖操作系统时区库。

这是单用户本机应用，不要把服务转发或部署到公网，也不要把个人日志加入 Git 仓库。
