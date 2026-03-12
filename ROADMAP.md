# StickerSwap Roadmap

This roadmap describes how `stickerswap-cli` can evolve from a Telegram-focused CLI into a broader face-swap and video-processing product. It is intentionally implementation-oriented: each phase names the capabilities to add, the work to complete, and what "done" should look like.

Today the project already supports a complete Telegram sticker-pack flow:

`fetch -> swap -> encode -> validate -> publish`

The long-term direction is to keep Telegram as a strong connector while making the core pipeline reusable for local video workflows, future UI clients, and additional platforms.

## Roadmap Index

- [Product Direction](#product-direction)
- [Foundational Work](#foundational-work)
- [Phase 1: CLI Hardening and Project Hygiene](#phase-1-cli-hardening-and-project-hygiene)
- [Phase 2: Cross-Platform UI](#phase-2-cross-platform-ui)
- [Phase 3: Generic Video Workflow](#phase-3-generic-video-workflow)
- [Phase 4: Multi-Face Detection, Tracking, and Mapping](#phase-4-multi-face-detection-tracking-and-mapping)
- [Phase 5: Connectors Beyond Telegram](#phase-5-connectors-beyond-telegram)

## Product Direction

`stickerswap-cli` started as a practical Telegram video sticker workflow. The next step is to turn it into a reusable face-swap engine with multiple entrypoints:

- CLI for automation and repeatable batch jobs
- cross-platform UI for guided workflows and manual review
- local video import/export for non-Telegram use cases
- connector-based publishing for Telegram first, with room for more platforms later

The product direction is `UI-first`, but the UI should sit on top of a reusable backend instead of reimplementing pipeline logic.

## Foundational Work

This work supports every later phase and should be treated as shared platform investment.

### Goals

- Separate reusable pipeline services from CLI-only orchestration.
- Stabilize interfaces between runtime, jobs, pipeline stages, and connectors.
- Expand tests so future UI and connector work can move without breaking the current CLI.

### Key tasks

- Extract backend service boundaries from the current CLI-driven flow.
- Introduce a job model with persistent progress state and resumable stage metadata.
- Normalize stage outputs so CLI and future UI read the same manifest and progress data.
- Formalize runtime/model management behind a stable service layer.
- Expand automated tests around resume behavior, failures, and long-running batch execution.

### Done when

- Core pipeline can be called without going through interactive CLI code.
- Progress and stage results are readable by more than one client type.
- Tests cover the main happy path plus recovery from partial runs.

## Phase 1: CLI Hardening and Project Hygiene

The current CLI is already useful; this phase makes it more durable as the backend reference implementation.

### Why this phase matters

- The CLI remains the fastest way to test new capabilities.
- A stronger CLI makes UI and connector work lower risk.
- Public open-source usage benefits from better defaults, diagnostics, and setup behavior.

### What exists today

- Guided `stickerswap run`
- advanced stage commands
- local-only config support
- runtime detection and model bootstrap
- local checks and gated live Telegram test

### Add next

- Better structured logs and machine-readable progress summaries.
- More explicit error categories for bootstrap, Telegram, media, and model failures.
- Improved dry-run and inspection commands for debugging workspaces.
- Clearer output around skipped/reviewed items and why they need attention.
- Stronger local pre-publish checks for secrets, ignored files, and release hygiene.

### Milestones and tasks

- Add a stable progress/event schema used by both CLI and future UI.
- Add command(s) to inspect manifest state and failed items.
- Improve bootstrap diagnostics for missing `ffmpeg`, missing models, and unsupported runtimes.
- Expand tests around config precedence, workspace reuse, and publish resume flows.

### Done when

- The CLI can serve as the canonical backend client.
- Users can understand job state without opening raw workspace files manually.
- Release and local safety checks catch common mistakes before publishing or pushing to Git.

## Phase 2: Cross-Platform UI

This is the main product expansion phase and the highest-priority roadmap item.

### Why this phase matters

- The current workflow has real review and override steps that fit UI better than terminal output.
- Progress, previews, and selective publishing are much easier with a desktop-style interface.
- UI lowers the barrier for users who do not want to orchestrate pipeline stages manually.

### Target capabilities

- Create a project from source pack, local video, or existing workspace.
- Enter or reuse local config values such as token, owner id, output pack naming, and face inputs.
- Show stage progress with current file, processed count, and overall status.
- Browse raw, swapped, encoded, and validation outputs.
- Manually include, exclude, retry, or review individual stickers or clips.
- Trigger model downloads and runtime setup from the UI.

### Milestones and tasks

- Define a backend job API that the UI can call for create/start/resume/cancel/status.
- Build a project list and project detail view over workspace data.
- Add preview grids for sticker review and before/after comparisons.
- Add controls for rerun, skip, publish selection, and export selection.
- Surface runtime/model status and download actions in a dedicated settings/setup area.

### Done when

- A user can run the full Telegram workflow from UI without falling back to CLI for normal operations.
- Project progress and outputs are inspectable visually.
- Manual selection of what to publish is a first-class workflow.

## Phase 3: Generic Video Workflow

This phase grows the project beyond Telegram and makes the engine useful for local media workflows.

### Why this phase matters

- Telegram is a strong initial connector, but the core problem is broader than sticker packs.
- Local video processing opens up more use cases and makes the product less connector-dependent.
- A generic workflow is a prerequisite for future social/sticker platform integrations.

### Target capabilities

- Import local video files directly.
- Process clips without any Telegram dependency.
- Export to local formats such as `.mp4`, `.webm`, preview frames, and project metadata.
- Reuse the same runtime, face-swap, encode, and validation stack outside sticker publishing.

### Milestones and tasks

- Introduce a local-media input path alongside Telegram pack ingestion.
- Add output targets for local video export and artifact bundles.
- Separate Telegram-specific validation/publishing from generic encode/export logic.
- Add workspace metadata that can represent both sticker projects and local-video projects.

### Done when

- A user can load local videos, swap faces, and export results without Telegram credentials.
- Telegram is optional, not required, for the main processing engine.
- Project structure supports both sticker-pack and generic-video jobs cleanly.

## Phase 4: Multi-Face Detection, Tracking, and Mapping

This phase handles the cases where automatic single-face swap is not enough.

### Why this phase matters

- Real video workflows often contain multiple people, ambiguous detections, and unstable face geometry.
- Manual correction requires stable identities across frames, not just isolated bounding boxes.
- Mapping different target faces to different reference photo sets unlocks much stronger editing workflows.

### Target capabilities

- Detect multiple faces per frame.
- Track faces across frames and assign stable face ids.
- Let the user inspect, merge, split, accept, or override face tracks.
- Map each face track to one reference image or a reference photo set.
- Support "do not swap" as an explicit mapping outcome for selected faces.

### Milestones and tasks

- Add face-track data structures to manifest/job state.
- Introduce tracking or re-identification across frame sequences.
- Add track-level preview and identity review workflows.
- Add mapping rules such as `track -> reference set` and `track -> no swap`.
- Add rerender support after manual track or mapping edits.

### Done when

- The system can process clips with multiple distinct people in a controlled way.
- Users can tell the system exactly which faces to change and which to leave untouched.
- Track-level decisions persist across resume and rerender operations.

## Phase 5: Connectors Beyond Telegram

Telegram should remain a first-class connector, but not the only one.

### Why this phase matters

- Different platforms have different ingest, packaging, and publish requirements.
- A connector model keeps platform-specific logic out of the core engine.
- This makes the product extensible without forking the main workflow per platform.

### Target capabilities

- Connector abstraction for sources and outputs.
- Telegram remains the reference connector for fetch/publish.
- Future connectors can add import/export rules for other sticker platforms or social apps.
- Non-network outputs such as local folders stay valid targets alongside remote platforms.

### Milestones and tasks

- Define connector interfaces for source ingestion and publish/export targets.
- Refactor Telegram-specific code behind the connector abstraction.
- Add capability descriptors so clients know which features a connector supports.
- Add connector-specific validation rules layered on top of generic media processing.

### Done when

- The core pipeline no longer depends directly on Telegram-specific assumptions.
- New connectors can be added without reworking the full engine.
- Telegram remains stable while the project expands into other ecosystems.

## Notes on Runtime and Model Management

Runtime and model management cut across all phases and should continue evolving in parallel.

### Ongoing product goals

- Auto-detect platform-specific runtime choices.
- Support selectable detectors/backends when quality or performance tradeoffs matter.
- Manage model downloads from supported sources with clear progress and fallback behavior.
- Expose quality presets and detection modes in a way that both CLI and UI can use.

### Near-term tasks

- Make detector/backend selection an explicit config surface.
- Add model inventory/status reporting.
- Improve download progress reporting and retry/fallback logic.
- Keep Apple Silicon and CPU-only paths both supported and testable.

## Suggested implementation order

1. Finish foundational refactors and CLI hardening.
2. Extract a reusable backend job layer.
3. Build the first cross-platform UI over existing workspace and job state.
4. Add local video import/export as a first non-Telegram workflow.
5. Add multi-face tracking and manual mapping.
6. Generalize connectors beyond Telegram.

That order keeps the current working CLI useful while building toward a broader product.
