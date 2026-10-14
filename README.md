# AI for Founders Mastery

The draft curriculum for Mindvalley's AI for Founders Mastery, as a self-contained static site.

| File | What it is |
|---|---|
| `index.html` | The front door: calendar, the Founder Operating System diagram, the eight modules, who it is for, the promise |
| `curriculum.html` | The curriculum: seventeen lessons and a graduation, every Tuesday lesson and Thursday lab, with the AI team each lesson installs |
| `pack.html` | The co-creation pack for marketing: the outline, the survey and the community email copy |
| `data/ai-founders-curriculum.json` | The curriculum data every page renders |

Open any page from disk or any static host; nothing needs a build or a server. Links to the proposal, the positioning
page and Expert & Authority go to the live Mindvalley site, which needs Google sign-in.

**Source of truth.** These files are exported from `garethwinter-cpu/expert-authority-mastery`, where the curriculum is
built and served live. To refresh this repo from there:

```
python3 scripts/aif/build_aif.py
python3 scripts/aif/export_static.py /path/to/ai-founder-mastery
```

Draft for alignment, 14 October 2026. Not yet aligned with Vishen; teachers are mapped once the curriculum is settled.
