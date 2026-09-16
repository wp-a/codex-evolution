# Clear introduction and macOS-inspired interface

## Purpose and audience

The user finds the current application confusing and requests a feature introduction plus a polished Apple-style interface. The audience is an individual Codex user who wants to understand past conversations and improve future prompts, project instructions and reusable workflows.

The main purpose is: 回看与 Codex 的历史对话，检查提示词和项目规则，把可复用的方法留给下一次。

## Design

Add a default `#start` page with a plain-language purpose, three jobs (review habits, check rules, reuse methods), a short first-use sequence and two actions: import local history or try the clearly labelled synthetic example. A small preview uses the actual current analysis; it never invents personal results. Rules and prompt templates remain directly usable without importing history.

Group existing navigation under 开始、回顾历史、改进协作. Keep existing route identifiers and actions; use shorter Chinese labels. Keep reports central, and disclose full report text, methodology and secondary exports with native details instead of stacking everything open.

Use a macOS-inspired light interface: system typography, warm white/gray surfaces, blue actions, generous spacing, subtle borders and restrained translucency on navigation. Maintain an equally readable dark theme and saved theme preference. Preserve the original logo and all evidence, model-consent and data-isolation behavior.

## Implementation and verification

1. Extend browser smoke with new-entry, navigation, actual-demo and theme-preference checks; observe the missing start page fail before implementing it.
2. Update `web/app.js` and `web/index.html` with the start view, clear labels and native report disclosures. Refine `web/styles.css` in parallel under the shared class contract.
3. Verify existing 80 core tests, JavaScript syntax, all browser workflows and keyboard behavior. Inspect new entry/report views in both themes at 320/360/736/1024/1512px; wide data tables may scroll inside their containers.
4. Update quickstart and QA records with actual results, refresh intentional screenshots, and open the local preview. Keep this as a local UI iteration; no backend schema or external publication is needed.

## Completed

The user explicitly selected the macOS daily-tool direction. Implemented the introduction, grouped navigation, clear page copy, light/dark styling and report disclosures. Verified 80 core tests, full direct-localhost Chrome flows and targeted keyboard/layout checks in both themes at five viewport widths. Corrected mobile dataset truncation and disclosure focus/body inset after visual and independent review. See `docs/QA.md` for the exact checks and remaining limits.
