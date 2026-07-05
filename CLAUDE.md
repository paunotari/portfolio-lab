# Project instructions (auto-loaded every session)

This file is read automatically by Claude Code at the start of every session in this repo.
It exists to make the workflow below happen **without the user having to ask each time.**

For what the code does and how it's structured, read **[info/CLAUDE.md](info/CLAUDE.md)** first
(architecture, module map, data flow, caveats). Also see **[info/vision.md](info/vision.md)**
(product roadmap) and **[info/TODO.md](info/TODO.md)** (task backlog).

## Standing workflow — do this on every change, without being asked

1. **Keep `info/CLAUDE.md` current.** If a change adds/renames/moves a module, changes the data
   flow, adds a config constant, or introduces a new caveat/gotcha — update the relevant section
   of `info/CLAUDE.md` in the same turn you make the change, not as an afterthought later.

2. **Keep `info/TODO.md` current.**
   - If you notice a needed follow-up while working (a gap, a rough edge, a deferred piece),
     add it as a checklist item in the right section — don't just mention it in chat and drop it.
   - When a TODO item is completed, mark it `[x]` or remove it (whichever keeps the file
     readable) in the same turn you finish the work.

3. **Commit and push automatically once a change is implemented and verified working** — i.e.
   after the relevant tests pass (`python tests/test_pipeline.py`) and, if applicable, the
   pipeline runs clean (`python scripts/run_pipeline.py`). Do not ask for permission to commit/push
   for routine work in this repo — that confirmation is pre-authorized here. Write a descriptive
   commit message (what changed and why, not just "update"). Push to `main` (this repo's
   established workflow — solo owner, no branch/PR process yet).
   - Exception: still ask first for anything destructive or irreversible beyond a normal commit
     (force-push, history rewrite, deleting data, etc.) — this pre-authorization covers ordinary
     commit + push only.

## Quick reference
```bash
python scripts/run_pipeline.py      # rebuild processed data, analytics, dashboard
python tests/test_pipeline.py       # data-integrity checks — must pass before committing
```
