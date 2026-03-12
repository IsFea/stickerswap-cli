# Sprint 1 Plan

This document turns the first roadmap slice into a concrete implementation sprint.

It is intentionally narrow: the goal is not to start UI work yet, but to build the backend foundation that will make UI, local video workflows, and connector expansion safe to implement.

## Sprint Goal

Make the current CLI-backed pipeline behave like a reusable backend service with explicit job state, stable progress reporting, and stronger automated coverage.

This sprint covers:

- [#7](https://github.com/IsFea/stickerswap-cli/issues/7) Extract reusable backend service layer from CLI orchestration
- [#8](https://github.com/IsFea/stickerswap-cli/issues/8) Add persistent job model and progress state
- [#10](https://github.com/IsFea/stickerswap-cli/issues/10) Add structured progress schema and workspace inspection commands
- [#9](https://github.com/IsFea/stickerswap-cli/issues/9) Expand tests for resumable and failure-recovery job flows

## Why This Sprint First

The project already works end to end for Telegram sticker packs, but the current shape is still CLI-first. Future work depends on making the pipeline callable and inspectable as a stable backend:

- UI needs a durable job and progress model
- generic local video mode needs pipeline reuse without Telegram assumptions
- multi-face tooling needs richer persistent state
- connector abstraction is easier once orchestration and state are normalized

## Desired Outcomes

By the end of Sprint 1:

- pipeline execution is available through reusable backend-facing services
- progress/state is represented in a stable structured format
- users can inspect workspace/job state through dedicated commands
- resume and recovery behavior have stronger automated test coverage

## Scope

### 1. Extract backend service layer

Refactor the current orchestration so interactive prompting and user-facing console flow no longer own the execution model.

Target outcomes:

- shared orchestration entrypoints that can be invoked by CLI and future UI
- clear separation between input collection, runtime setup, and stage execution
- reduced duplication between `run`, advanced commands, and future automation paths

Likely implementation themes:

- move stage sequencing into reusable service objects or backend-oriented functions
- keep CLI responsible for argument parsing, prompts, and final console formatting
- stop leaking CLI-only assumptions into orchestration code

### 2. Introduce persistent job model

Extend the workspace state beyond the current manifest-only view.

Target outcomes:

- job-level metadata separate from sticker records
- stage status, timestamps, counters, and last-known progress stored persistently
- recoverable state after interruption

Likely implementation themes:

- add a job metadata file in the workspace
- record per-stage status such as `pending`, `running`, `completed`, `failed`
- include lightweight failure context suitable for inspection and retries

### 3. Add structured progress and inspection commands

The current console progress is useful, but not stable enough for future UI or deeper local debugging.

Target outcomes:

- a structured event/progress representation
- CLI commands to inspect job and workspace state
- readable visibility into `skip`, `review`, failures, and partial completion

Likely implementation themes:

- define a normalized event schema shared across stages
- emit consistent progress payloads from stage execution
- add command(s) such as manifest/job inspection rather than forcing manual JSON reads

### 4. Expand tests around resume and failure recovery

The project now needs tests for long-lived product behavior, not only happy-path smoke coverage.

Target outcomes:

- tests for interrupted runs and partial outputs
- tests for reusing existing workspace state safely
- tests for progress/job state persistence
- tests for publish and stage resume semantics

Likely implementation themes:

- add fixture-style temporary workspaces
- simulate missing or partially produced artifacts
- verify inspection output against expected state transitions

## Suggested Execution Order

1. Extract orchestration boundaries for stage execution.
2. Introduce a job metadata format and write/read helpers.
3. Wire progress emission through the new backend layer.
4. Add inspection commands on top of job and manifest state.
5. Backfill tests for recovery, resume, and inspection behavior.

## Concrete Deliverables

- reusable backend orchestration module or service layer
- persistent job metadata file format and loader/saver
- stable structured progress representation
- one or more inspection commands exposed through CLI
- expanded unit/integration-style tests for resume and recovery

## Non-Goals

This sprint should not include:

- shipping the cross-platform UI
- local video import/export
- multi-face tracking and mapping
- connector abstraction beyond preparatory refactors
- major model/backend experiments

## Acceptance Criteria

- current Telegram CLI workflow still works after refactor
- advanced stage commands continue to work
- progress/state can be consumed without parsing ad hoc console strings
- there is a documented and test-covered resume/recovery story
- Sprint 2 can start UI/backend API work without needing to redesign core job state

## Notes for the Next Sprint

If Sprint 1 lands cleanly, the next implementation target should be:

- [#12](https://github.com/IsFea/stickerswap-cli/issues/12) Define backend job API for UI clients

That is the right bridge from backend refactor into real UI work.
