# AI for Founders Mastery

The draft curriculum for Mindvalley's AI for Founders Mastery, as a self-contained static site.

| File | What it is |
|---|---|
| `index.html` | The front door: calendar, the Founder Operating System diagram, the eight modules, who it is for, the promise |
| `curriculum.html` | The student-facing curriculum: every session week by week, with date, teacher and description. Built from `data/curriculum-sessions.json` |
| `pack.html` | The co-creation pack for marketing: the outline, the survey and the community email copy |
| `data/curriculum-sessions.json` | Snapshot of the AIF Airtable base: Schedule (order, date, speakers, module) and Lessons (title, type, description) |
| `data/ai-founders-curriculum.json` | The working curriculum data the front door and pack render |

Open any page from disk or any static host; nothing needs a build or a server. Links to the proposal, the positioning
page and Expert & Authority go to the live Mindvalley site, which needs Google sign-in.

**Curriculum page.** Airtable is the source of truth. Refresh `data/curriculum-sessions.json` from the base, then run
`python3 scripts/build_curriculum.py`. The export below leaves `curriculum.html` alone.
Session titles come from the `mastery-lesson-titles` skill and are in Airtable as of 30 October.

**Front door and pack.** These files are exported from `garethwinter-cpu/expert-authority-mastery`, where the curriculum is
built and served live. To refresh this repo from there:

```
python3 scripts/aif/build_aif.py
python3 scripts/aif/export_static.py /path/to/ai-founder-mastery
```

The curriculum page reflects the Airtable base as of 29 October 2026 (teacher allocation D).
