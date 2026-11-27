# Handover Log — 2026-10-06 — v0.5.2 Prerelease Published

## Result

BlazePwifi `v0.5.2` is published as the agreed pre-signing GitHub prerelease.

Release:
`https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/v0.5.2`

Release ID:
`404545281`

Exact validated candidate:
`bf2992977fe8504d21b107df02826032c31d3a62`

Build run:
`37443570618` — **PASS**

Release run:
`37445141476` — **PASS**

The release remains pinned to the exact green candidate even though release workflow/docs commits occurred later.

## Android assets

- `BlazeRental-v0.5.2-TEST.apk`
- `BlazeRental-v0.5.2-release-unsigned.apk`
- `BlazeRental-v0.5.1-rescue-for-v0.5.2-TEST.apk`
- `BlazeRental-v0.5.1-rescue-for-v0.5.2-release-unsigned.apk`

No production `BlazeRental.apk` is present yet, by design.

## Branding/alarm state

- User-supplied LCM artwork is the v0.5.2 BlazeRental production icon/branding.
- Packaged APK contains a valid LCM PNG.
- Near End: default 10m remaining / 5s audible ring.
- Urgent Add Credit: default 3m remaining / 10s audible ring.
- Time's Up: 00:00 / 15s audible ring.
- Admin can change threshold, duration, non-zero minimum alarm volume, and sound source.
- Sound sources: built-in, Android device alarm tone, custom local audio.
- Silent device-tone option is disabled.
- Active alarm volume guard prevents reduction below configured non-zero minimum.
- DND policy access supports Total Silence override where Android permits.
- Previous audio/ringer/DND state is restored after alarm playback.
- Alarm events are one-shot per lease and re-arm when credit extends the lease.

## Next action

Create the new permanent production signing lineage for v0.5.2 only.

Do not newly sign v0.5.1 or older APKs.

The new lineage must have an externally retained recovery credential and must not hide plaintext/reversible private signing material in Git.

## Audit & Reconcile prompt

```text
@GitHub Reconcile BlazePwifi from the published v0.5.2 pre-signing state.

1. Read PROJECT_HANDOVER.md and this handover log.
2. Verify release v0.5.2 exists as prerelease ID 404545281 and targets bf2992977fe8504d21b107df02826032c31d3a62.
3. Verify build run 37443570618 and release run 37445141476 passed.
4. Verify LCM branding and the 10m/5s, 3m/10s, 00:00/15s alarm defaults remain intact.
5. Verify STREAM_ALARM minimum-volume enforcement, DND override support, and device/custom/built-in sounds remain intact.
6. Verify no production-signed BlazeRental.apk is present yet.
7. Create/use a new production signing lineage for v0.5.2 only; do not newly sign 0.5.1 or older APKs.
8. Keep signing recovery outside plaintext Git and publish only public verification/encrypted recovery material.
9. After signing, verify normal and rescue APK signer fingerprints and refresh/promote the existing v0.5.2 release without moving its tag.
10. Log the signing/release promotion result with a fresh Audit & Reconcile prompt.
```
