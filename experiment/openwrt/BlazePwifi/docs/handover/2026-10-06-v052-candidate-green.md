# Handover Log — 2026-10-06 — v0.5.2 Exact Candidate Green

## Exact candidate

Branch:
`blazepwifi-v0.5.2-implementation`

Candidate SHA:
`bf2992977fe8504d21b107df02826032c31d3a62`

Build run:
`37443570618`

Result:
**PASS**

## Production changes

- LCM production artwork from the user-supplied source is now the BlazeRental application icon/branding.
- The previously corrupted PNG was replaced with a verified PNG derived directly from the uploaded LCM source.
- CI now parses PNG chunks and validates CRCs before Android compilation.
- BlazeRental version is 0.5.2 / versionCode 50200.
- Near End alarm defaults to 10 minutes / 5 seconds.
- Urgent Add Credit alarm defaults to 3 minutes / 10 seconds.
- Time's Up alarm triggers at 00:00 / 15 seconds.
- Alarm duration, threshold, minimum volume, and sound source are configurable in the native admin.
- Device alarm picker disallows Silent.
- Custom audio documents and built-in tones are supported.
- Active alarms use STREAM_ALARM and a periodic volume guard to prevent reduction below the configured non-zero minimum.
- DND policy access is available for Android Total Silence override where the OS permits it.
- Alarm/ringer/DND state is restored after playback.
- Warnings are one-shot per lease and re-arm when credit extends the lease.
- Time's Up re-applies the rental gate in managed mode.

## Candidate evidence

The exact run passed:
- validate;
- Android normal + v0.5.1 rollback rescue build;
- no-reflash update bundle;
- browser simulation;
- ESP8266/ESP32;
- Ruijie;
- x86 QEMU;
- required Orange Pi simulations;
- Android Device Owner emulator;
- final candidate gate.

Android artifact:
`BlazePwifi-android-BlazeRental-v0.5.2`

Candidate gate artifact:
`BlazePwifi-v0.5.2-candidate-gate`

## Release rule

Publish v0.5.2 from this exact candidate **before production signing**.

Initial release must use `signing_run_id=0`, remain prerelease, and clearly label Android TEST/unsigned assets.

Do not sign 0.5.1 or older APKs as part of the v0.5.2 production lineage.

## Audit & Reconcile prompt

```text
@GitHub Reconcile BlazePwifi v0.5.2 from the exact green candidate.

1. Read PROJECT_HANDOVER.md and this v0.5.2 candidate log.
2. Verify build run 37443570618 passed for exact SHA bf2992977fe8504d21b107df02826032c31d3a62.
3. Verify Android normal/rescue builds, Device Owner emulator, no-reflash update bundle, browser, ESP, Ruijie, x86 and Orange Pi simulations, and candidate gate all passed.
4. Verify the packaged BlazeRental APK uses the supplied LCM branding and the LCM PNG integrity contract passes.
5. Preserve the three alarm defaults: Near End 10m/5s, Urgent 3m/10s, Time's Up 00:00/15s.
6. Preserve STREAM_ALARM forced minimum-volume enforcement, DND override support, device/custom/built-in alarm sources, one-shot-per-lease behavior and re-arm on credit extension.
7. Publish v0.5.2 from the exact candidate with signing_run_id 0 before creating any new production signing lineage.
8. Do not newly sign older 0.5.1 or older APKs.
9. After release verification, update PROJECT_HANDOVER.md and add a release handover log.
10. Only then design/perform the new permanent production signing lineage with external recovery storage.
```
