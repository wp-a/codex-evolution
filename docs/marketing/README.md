# Codex Evolution media kit

Eight ready-to-use PNG images, built from the actual application interface. All pictured messages, project instructions and statistics are synthetic examples. Screenshots are cropped for composition; their numbers and product controls are not redrawn or invented.

| File | Dimensions | Suggested use |
|---|---|---|
| [cover-zh.png](cover-zh.png) | 1600 × 1000 | Chinese README, article cover, community post |
| [cover-en.png](cover-en.png) | 1600 × 1000 | English README and launch post |
| [feature-overview.png](feature-overview.png) | 1600 × 1000 | Monthly prompting patterns |
| [feature-evidence.png](feature-evidence.png) | 1600 × 1000 | Original-message evidence |
| [feature-rules.png](feature-rules.png) | 1600 × 1000 | Project instruction review |
| [feature-workflows.png](feature-workflows.png) | 1600 × 1000 | Prompt templates and Skill drafts |
| [poster-zh.png](poster-zh.png) | 1080 × 1440 | Portrait social post |
| [social-preview.png](social-preview.png) | 1280 × 640 | Link sharing / GitHub social-preview asset |

[Browse the image gallery](index.html) locally in a browser. [Launch copy](../launch/LAUNCH_COPY.md) includes Chinese article, Xiaohongshu, WeChat Moments and English X drafts. Repository HTML files are source files on GitHub; download the media kit to open the gallery locally.

## Visual direction

The macOS-inspired layout uses generous space, system typography, neutral light surfaces, restrained blue accents and the existing purple project mark. The dark rule-review image matches the actual dark interface. Keep the synthetic-data labels and independent-project attribution when reusing the images.

The original logo and code are covered by the repository's MIT license. These project-created compositions and synthetic screenshots use the same license. Codex Evolution is an independent community project and is not affiliated with or endorsed by OpenAI.

## Edit and render

Edit [source.html](source.html) to change the composition or copy. Its inputs are the cropped PNG screenshots in `screens/` and the repository logo. Fonts use the host's system font stack; a macOS host best matches the supplied output. No external assets or network font requests are used.

The renderer is optional development tooling, separate from the zero-dependency application:

```bash
python -m pip install playwright
python -m playwright install chromium
python docs/marketing/render.py
# Or use an installed Chrome/Chromium binary:
python docs/marketing/render.py --browser /path/to/chrome
```

## Source record

- `screens/overview-dark.png` and `screens/prompt-templates.png`: crops of user-supplied screenshots of the synthetic demo.
- `screens/overview-light.png` and `screens/audit-findings.png`: crops of the repository's verified synthetic-demo screenshots.
- `screens/evidence.png`: a fresh screenshot of the actual heatmap evidence dialog using the synthetic demo.

The capture and composition process strips capture metadata. No personal history, credentials, or private instruction files are included.
