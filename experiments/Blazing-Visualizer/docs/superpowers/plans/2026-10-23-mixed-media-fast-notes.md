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


## Verification ledger

- Baseline regression source: `c249f1f330524f277f7a937fdddf27f9430bffcc`. Actions run `39919163110`: all three metadata/view contract tests failed with assertions; independent first-note test failed with the intended timeout on API26 and API36. No production changes were included in this checkpoint.
- Integrated implementation restores the complete host/lint/assemble and two-device workflow. Additional tests cover bounded source-time decode/seek, stale quick-frame rejection, video pixel layering, metadata, rotated frames, video→audio transition and MP4 source-time compositing.
- Target release is separately tagged Preview 4 (versionCode4); retain Preview2/3 public debug signer. Do not describe this preview as production-ready.
- Real instrument/source separation remains research only. See `docs/acceptance/2026-10-23-stem-separation-research.md` for the staged offline pilot and primary sources. No model weights or runtime added, and no media uploaded.

## Continuation: 23 October evening

- Observed native RED at `d855944`, run39936432159: API36 reproduces collapsed audio timestamps, truncated video duration, stale analysis cache reuse and EGL target ownership failures. API26's generated timing input failed fixture verification; the older muxer changed the first timestamp. Those setup failures are not claimed as timing regressions.
- Ruling: preserve one source timeline in original PCM and analysis mono, pad/trim in bounded cancellable blocks and version both caches. Content hashes remain unchanged, preserving project identity. Cost if wrong: an affected track needs reanalysis; native PCM assertions pin the intended timing.
- Ruling: use the existing Media3 1.8 extractor for decode as well as playback, and one fixed synthetic MP4 on both device versions. No new runtime dependency or copied parser. Cost if wrong: an unsupported container may report a visible decode failure; the media, queue and source remain available.
- The earlier host stall was not reproduced in independent diagnostic39959477936: unchanged source passed118 tests/20 suites. The cause remains unconfirmed. Complete host/lint/APK and API26/API36 validation are restored for the fix candidate; diagnostic checkpoints cannot publish a preview.
- Pending: GREEN verification, native artifact inspection, retained-signer/direct-APK verification, Preview4 publication and final handoff.
