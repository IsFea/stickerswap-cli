# Engineering Context

This file is a compact project memory for future implementation sessions. It is meant to restore working context quickly without relying on prior chat history.

## Project Snapshot

`stickerswap-cli` is a Python CLI tool that currently supports a full Telegram video sticker workflow:

`fetch -> swap -> encode -> validate -> publish`

The project already has:

- guided CLI flow via `stickerswap run`
- advanced stage commands for each pipeline step
- local-only config support through `.env.local`
- runtime detection for Apple Silicon and CPU-only systems
- model bootstrap with fallback download behavior
- local `check` command for safety and hygiene
- gated `test-live` command for a real Telegram integration check

## Current Product Direction

The long-term product is not just a Telegram sticker utility.

The intended shape is:

- reusable backend face-swap engine
- CLI as automation/debug client
- cross-platform UI as the primary user-facing experience
- Telegram as the first connector, not the only one
- local video import/export as a first-class non-Telegram workflow

Roadmap reference:

- [ROADMAP.md](ROADMAP.md)
- GitHub backlog source: roadmap epics and child issues in [IsFea/stickerswap-cli issues](https://github.com/IsFea/stickerswap-cli/issues)

## Current Repo Shape

Core areas already present:

- CLI entrypoint and command parsing
- pipeline orchestration
- runtime/bootstrap/config layers
- Telegram integration
- media handling and encoding
- face-swap backend integration
- local checks and tests

The repo is already public and should remain safe for open-source use.

Repository-level agent workflow guidance lives in [AGENTS.md](AGENTS.md).

## Important Working Constraints

- Do not commit secrets, local photos, workspaces, models, or other runtime artifacts.
- Keep `.env.local` local-only.
- Keep GitHub-safe docs free of private paths, tokens, and local operator details.
- Prefer evolving the current architecture rather than replacing it wholesale.
- Preserve the working Telegram pipeline while extracting reusable backend layers.

## Technical Direction

The next architectural move is to separate:

- input collection and UX
- job orchestration
- stage execution
- persisted job/manifest state
- platform-specific runtime/model setup
- connector-specific source/publish logic

This separation is the prerequisite for:

- UI orchestration
- local video mode
- multi-face/manual workflows
- future connector abstraction

## Near-Term Priority Order

Top implementation order:

1. backend service extraction
2. persistent job model and progress state
3. structured progress and inspection surfaces
4. stronger tests for resume and recovery
5. backend job API for UI clients

Sprint reference:

- [SPRINT_1_PLAN.md](SPRINT_1_PLAN.md)

GitHub issue reference:

- [#1](https://github.com/IsFea/stickerswap-cli/issues/1) Foundation epic
- [#2](https://github.com/IsFea/stickerswap-cli/issues/2) Phase 1 epic
- [#3](https://github.com/IsFea/stickerswap-cli/issues/3) Phase 2 epic

## Priority Rule

For future implementation sessions, use this priority stack unless the user explicitly changes it:

1. `ROADMAP.md` phase order
2. active sprint plan
3. GitHub epic and child-issue ordering

Current execution priority is:

1. Foundation epic `#1`
2. Phase 1 epic `#2`
3. Phase 2 epic `#3`
4. Phase 3 epic `#4`
5. Phase 4 epic `#5`
6. Phase 5 epic `#6`

Current recommended starting sequence is:

1. [#7](https://github.com/IsFea/stickerswap-cli/issues/7)
2. [#8](https://github.com/IsFea/stickerswap-cli/issues/8)
3. [#10](https://github.com/IsFea/stickerswap-cli/issues/10)
4. [#9](https://github.com/IsFea/stickerswap-cli/issues/9)
5. [#12](https://github.com/IsFea/stickerswap-cli/issues/12)

## Backlog Management Rule

GitHub issues and epics are not static planning artifacts; they should be maintained as work progresses.

Expected behavior for future sessions:

- when a task is finished and you are satisfied, update or close the corresponding GitHub issue
- keep epic child checklists aligned with actual completion state
- close an epic when its planned scope is done or intentionally retired
- revise sprint docs when implementation reality changes
- create new issues or replace outdated ones when new requirements appear

## Design Principles to Preserve

- Keep the pipeline resume-friendly.
- Keep runtime setup automatic where practical, explicit where necessary.
- Prefer structured state over parsing human-readable logs.
- Treat UI as a client over reusable backend services, not as a new processing engine.
- Treat Telegram as a connector layered on top of core media processing.
- Keep project memory and docs updated when architecture, workflow, or priorities change.

## When Returning Later

If starting a new implementation session, re-read these in order:

1. [ENGINEERING_CONTEXT.md](ENGINEERING_CONTEXT.md)
2. [ROADMAP.md](ROADMAP.md)
3. [SPRINT_1_PLAN.md](SPRINT_1_PLAN.md)
4. the relevant GitHub epic and child issues

That should be enough to resume work without reconstructing the whole project history.
