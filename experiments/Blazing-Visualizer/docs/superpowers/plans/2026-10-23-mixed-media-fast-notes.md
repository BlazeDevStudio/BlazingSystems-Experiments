# Mixed Media and Fast Notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Play mixed audio/video queues with video behind the visualizer and quick source-time note estimates while detailed analysis runs.

**Architecture:** Preserve Media3 as the single audible session. Add source metadata, video surface attachment and transparent compositing; export video frames at source time. A bounded quick decoder/cache feeds preview estimates without waiting for whole-file hash/Basic Pitch.

**Tech Stack:** Kotlin, Media3 1.8.0, Android Canvas/GL, MediaMetadataRetriever, LiteRT, existing Actions matrix.

**Spec:** ../specs/2026-10-23-mixed-media-fast-notes-design.md

## Global Constraints

- Android26+, SDK36; retain current Media3 1.8.0 and existing presets/Practice/queue/export.
- No unapproved external audio uploads, fabricated stem separation or production-ready claims.
- Keep main and existing releases intact; new tested preview is versionCode4 / Preview4.
- SourceRef additions default to mimeType=null, hasVideo=false, hasAudio=true.
- Equations remain off by default; video-to-graph tracing remains last.

## Review Focus

- Silent videos must play/export with no phantom note estimates.
- New selections/seeks must never display stale notes/video from a prior source.
- Video is the deepest layer and shares the actual player clock, including Practice speed.
- Cached and refined notes must remain correct and edits/export must not consume temporary estimates.
- Whole-file preparation must not block initial visual feedback; cache requests must be bounded.

## Tasks

- [ ] 1. Root: add SourceRef media metadata, multi-media import/intent handling and silent-video decoder behavior, with metadata/backward compatibility tests.
- [ ] 2. Video renderer owner: transparent TextureView visualizer, optional deepest background bitmap in painter/GL, source-time video export reader, pixel/native export tests. Root owns Media3 surface attachment and UI wiring.
- [ ] 3. Root: bounded quick decoder/cache and StudioModel progressive preview; regressions for early estimates, seeks, cancellation and refined-note precedence. Publish regressions before the fixes where a current observable behavior is pinned.
- [ ] 4. Research owner: primary-source instrument-separation assessment and concrete measurable next-stage workflow; no unsupported model claims or downloads into the app.
- [ ] 5. Integrated review, clean host/lint/APK and API26/API36, resolve failures, verify separately versioned Preview4 release and rewrite handoff.

## Execution ledger

Base302bbe0. Existing source/release reconciled; no AGENTS.md observed in the scoped project. Standing approval resolves routine choices without another design gate. Owner priorities supersede the old roadmap order: mixed media and startup responsiveness first, then preset/production hardening; tracing remains deferred.
