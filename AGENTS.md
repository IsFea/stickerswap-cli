# AGENTS.md

## Project Agent Rules

These rules apply to future agent work in this repository.

### 1. Maintain project memory

- Record important architectural decisions, product-direction changes, and implementation constraints in repository docs instead of leaving them only in chat history.
- Prefer updating existing context documents over creating scattered one-off notes.
- After meaningful project changes, review whether `ENGINEERING_CONTEXT.md`, `ROADMAP.md`, or the active sprint plan should be updated.

### 2. Keep docs current with the code

- If behavior, workflow, or project direction changes, update the relevant documentation in the same work stream.
- Treat documentation updates as part of the implementation, not optional cleanup.
- Keep public docs GitHub-safe: do not include secrets, local-only paths, tokens, personal IDs, or private operator notes.

### 3. Important files to maintain

- `ENGINEERING_CONTEXT.md`
  - keep this as the compact, always-current project memory for future implementation sessions
- `ROADMAP.md`
  - keep this aligned with actual product direction and phase ordering
- `SPRINT_1_PLAN.md` or the current sprint plan
  - update when implementation priorities change or when a sprint is completed/replaced
- `README.md`
  - keep user-facing usage and setup instructions aligned with the real product behavior

### 3.1. Source of truth for priorities

- Treat `ROADMAP.md` as the source of truth for product direction and phase order.
- Treat GitHub epics and their child issues as the source of truth for actionable implementation backlog.
- Before starting substantial new work, check the current roadmap phase, the relevant epic, and the active sprint plan.
- If priorities change, update the roadmap, the sprint/context docs, and the relevant GitHub epic/issues together.
- Avoid starting lower-priority work when a higher-priority epic is still the agreed focus, unless the user explicitly reprioritizes it.
- Actively maintain GitHub backlog state during delivery: close completed tasks, update epic checklists, close finished epics, and create new issues when the plan changes or new work appears.

### 4. When to update context docs

Update the project docs when any of the following happens:

- a new subsystem or workflow is introduced
- product direction or implementation order changes
- a previously planned approach is abandoned or replaced
- setup, runtime, or model-management behavior changes materially
- a sprint is completed and the next implementation focus changes
- GitHub epics, issue hierarchy, or implementation priorities are reorganized

### 5. Documentation style

- Prefer concise, operational documentation over narrative history.
- Write docs so a future agent can resume work without needing prior chat context.
- Favor stable facts, current constraints, next steps, and explicit priorities.
- Avoid duplicating the same content across many files unless the duplication serves a different audience.

### 6. Implementation hygiene

- Preserve the working Telegram pipeline while refactoring toward reusable backend layers.
- Prefer incremental refactors that keep the current system usable.
- Before closing substantial work, check whether code changes should also update tests and docs.
- Before considering a work stream done, check whether the corresponding sprint doc, GitHub tasks, and epic status should be updated.
