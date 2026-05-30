
## Communication
Be extremely concise. Sacrifice grammar for brevity. Use imperative tense in all commit messages and issue titles.

---

## Workflow: Plan → Approve → Branch → Build → Test → PR

### Step 1 — Plan First, Always
Before any implementation, produce a written plan. For any non-trivial feature, prefer a multi-phase plan. A plan must include:
- What will be built
- What files will be created or modified
- What tests will be written

Do not write a single line of implementation code until the plan is explicitly approved.

### Step 2 — GitHub Issues
After plan approval, create one GitHub issue per discrete feature. Issue title format: `[Phase N] Short imperative description`. Do not proceed to implementation until signaled.

### Step 3 — Branch Per Issue
Create a new git branch for each issue. Branch naming: `feature/phase-N-short-description`. Never commit directly to `main`.

### Step 4 — Tests First
Write unit tests before implementation for all engine logic (combat, deployment, VP, state machine transitions). For UI features, write component tests before or alongside implementation. No feature is complete without passing tests.

### Step 5 — PR & Merge
Ensure all tests pass, all conflicts are resolved, and the implementation matches the approved plan before opening a PR. PRs require explicit merge approval.

---
