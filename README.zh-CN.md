<div align="center">
  <img src="codex_evolution/web/logo.svg" width="64" alt="Codex Evolution">
  <h1>Codex Evolution</h1>
  <p><strong>回看与 Codex 的协作，整理下一次可用的方法。</strong></p>
  <p>本地优先 · 零运行时依赖 · 证据可追溯 · MIT 开源</p>
  <p><a href="README.md">English</a> · <a href="#快速开始">快速开始</a> · <a href="docs/QUICKSTART.zh-CN.md">使用指南</a> · <a href="https://github.com/wp-a/codex-evolution/releases/latest">下载</a> · <a href="docs/marketing/README.md">宣传素材</a></p>
</div>

![Codex Evolution：看懂使用习惯，整理可复用方法](docs/marketing/cover-zh.png)

**Codex Evolution 是一个在本机运行的 Codex 协作复盘工具。** 把历史对话整理成可追溯的观察，帮助你检查项目规则、准备下一次任务。

| 用途 | 你可以做什么 |
|---|---|
| 回看使用习惯 | 按月份、项目查看常用表达与任务信号，导出复盘报告。 |
| 找到原文依据 | 点击统计，查看命中消息、来源文件、行号和线程上下文。 |
| 检查项目规则 | 审阅 `AGENTS.md`、Skill 与项目计划中的重复要求和潜在冲突。 |
| 留下可复用方法 | 编辑 5 类提示词模板，将有证据支持的重复流程整理为 `SKILL.md` 草稿。 |

> **作者的 AI 服务 · 推广｜WPIRONMAN AI 中转**<br>
> 为支持自定义 API 地址的客户端提供 OpenAI 兼容模型接入。[访问控制台，查看接入说明 →](https://api.wpironman.top)<br>
> 此服务由项目作者运营。Codex Evolution 的本地功能无需开通中转；当前内置模型请求使用 OpenAI 官方接口。

## 快速开始

需要 **Python 3.10+**，从源码运行无需额外安装运行时依赖：

```bash
git clone https://github.com/wp-a/codex-evolution.git
cd codex-evolution
python3 -m codex_evolution demo --open
```

浏览器打开 `http://127.0.0.1:8765`。先点「先看示例」即可体验；演示使用合成数据，不会扫描个人历史。保持终端运行，按 `Ctrl+C` 停止。

导入自己的记录：

```bash
python3 -m codex_evolution import "${CODEX_HOME:-$HOME/.codex}"
python3 -m codex_evolution serve --open
```

也可在「导入与隐私」页选择目录或拖入 JSON/JSONL。原始日志保持只读，应用副本保存在 `~/.codex-evolution/evolution.sqlite`。规则检查与提示词模板可以直接使用，无需先导入历史。

端口、数据库、导出及模型材料的用法，见[中文快速上手](docs/QUICKSTART.zh-CN.md)；完整命令与模型配置见[详细使用说明](docs/USAGE.md)。也可从 [Releases](https://github.com/wp-a/codex-evolution/releases/latest) 下载源码和安装包。

## 界面预览

macOS 风格，支持明暗主题与移动端布局。当前界面为中文，文档提供中英文版本。

<details>
<summary>展开 4 张功能配图（均为合成演示数据）</summary>

| 回看使用习惯 | 查看原文证据 |
|---|---|
| ![按月查看提示习惯](docs/marketing/feature-overview.png) | ![回到带来源的原文](docs/marketing/feature-evidence.png) |
| 检查项目规则 | 整理可复用方法 |
| ![带原文引用的规则检查](docs/marketing/feature-rules.png) | ![提示词模板与 Skill 草稿](docs/marketing/feature-workflows.png) |

</details>

## 数据与使用边界

- **本地处理：**默认不发送模型请求。统计报告与分享卡只导出汇总；原文证据、审计文件和模型材料可能包含选定文本，分享前请检查。
- **观察有范围：**仅覆盖已导入且支持的本机记录，非云端账号全量。“验证”相关表达增加不证明执行了更多测试，报告不做能力评分。
- **修改由你决定：**规则检查提供引用与建议 diff，Skill 输出为待审阅草稿；应用不会自动修改规则、安装 Skill 或扩大 Codex 权限。
- **模型分析可选：**可以先预览材料，再复制给现有 Codex；内置 API 通道需单独配置并逐次同意。模型复盘最多接收 36 条节选和统计汇总。

更多说明：[安全与隐私](SECURITY.md) · [数据格式](docs/DATA_FORMAT.md) · [统计口径](docs/METHODOLOGY.md)。

## 文档与参与

| 你需要 | 文档 |
|---|---|
| 启动、导入、导出和常见操作 | [中文快速上手](docs/QUICKSTART.zh-CN.md) · [完整命令与配置](docs/USAGE.md) |
| 理解实现或贡献代码 | [架构](docs/ARCHITECTURE.md) · [测试记录](docs/QA.md) · [贡献指南](CONTRIBUTING.md) · [路线图](docs/ROADMAP.md) |
| 复用审核方法或介绍项目 | [配套 Skill](skills/README.md) · [宣传图片](docs/marketing/README.md) · [发布文案](docs/launch/LAUNCH_COPY.md) |

欢迎通过 Issue 或 PR 反馈导入兼容性、可访问性和实际使用问题；复现材料请使用合成数据。

当前版本 **0.1.1** · [MIT 许可](LICENSE) · 独立社区项目，与 OpenAI 无隶属或背书关系。
