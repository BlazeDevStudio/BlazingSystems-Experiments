# BlazePwifi v0.5.3-dev.4 — Member Metadata Migration Green Candidate

Date: 2026-10-07

## Purpose

This development slice closes the explicit Pisonet Members export/import follow-up while preserving BlazePwifi as the central member/banked-time authority.

Full BlazePwifi is the active target. `profiles/standalone-rental` remains reference-only and is unchanged.

## Development identity

- VERSION: `0.5.3-dev.4`
- BlazeRental versionName: `0.5.3-dev.4`
- BlazeRental development versionCode: `50293`
- Frozen v0.5.2 rollback rescue remains `50299`
- Final v0.5.3 production versionCode remains reserved at `50300`

No production v0.5.3 tag, release, or signing action was performed.

## Export safety

Member export uses the strict portable format:

`BLAZE_MEMBER_METADATA_V1`

The exported member row contains only:

- normalized username;
- requested enabled state;
- banked seconds;
- updated timestamp;
- Base64-wrapped label metadata;
- Base64-wrapped source metadata.

The export deliberately excludes:

- plaintext password;
- password verifier/hash;
- password salt;
- KDF scheme;
- KDF rounds.

The retained Playwright export artifact was inspected and contains none of those secret/verifier fields.

## Reviewed import contract

Import is two-stage:

1. **Preview**
   - Admin role;
   - CSRF required;
   - strict format/field/size/member-count validation;
   - duplicate username rejection;
   - classifies each record as `create` or `collision`;
   - produces a short-lived preview token.

2. **Apply**
   - Admin role;
   - CSRF required;
   - fresh current-password re-authentication;
   - exact preview token required;
   - explicit collision policy required.

Preview tokens are:

- short-lived;
- single-use after successful apply;
- bound to current authenticated admin session;
- bound to source IP;
- pinned to the current central member global revision.

If central member state changes after Preview, Apply fails and the operator must preview again.

## Collision behavior

Supported collision policies:

- `abort` — any username collision rejects the entire import before mutation;
- `skip` — existing central users are untouched; only new users are created;
- `update` — existing member label/enabled/banked metadata may be updated, but the existing central password verifier material is preserved.

There is no silent overwrite mode.

## New imported accounts

New member rows cannot safely carry password verifier material because the migration export deliberately excludes it.

Therefore new central records are created:

- disabled;
- authentication scheme `reset_required`;
- with non-secret structural sentinels in verifier columns;
- with imported banked time preserved.

An administrator must use the normal password-reset action and then enable the member before authentication can succeed.

## Transactional apply

Before mutation, Apply snapshots:

- member records;
- member-event history;
- global member revision.

The test suite injects a deliberate failure after an earlier import mutation. The implementation restores all three snapshots byte-for-byte and leaves the later member absent.

This prevents partially applied multi-member migrations.

## Member-store integrity fix discovered during dev.4

The member store permits optional empty labels.

Several existing shell paths used tab as POSIX shell IFS, which collapses empty whitespace fields and could shift enabled/verifier/balance columns when a label was empty.

dev.4 replaced those unsafe parsing sites with explicit field extraction across:

- authentication;
- create/set-password verifier parsing;
- member patch;
- password reset;
- banked-time changes;
- transfers;
- public member listing;
- SoftTimer member snapshots;
- migration export/update.

Regression coverage now creates an unlabeled member and proves password authentication, password reset, banked-time mutation and later label update remain structurally correct.

## Browser flow evidence

The exact Playwright flow performs:

1. open Pisonet Members;
2. download a real metadata export;
3. inspect the export for verifier/password absence;
4. select a real `.blazemembers` import file containing one collision and one new member;
5. preview the import;
6. verify collision/create classification;
7. choose the `skip` collision policy;
8. enter admin password;
9. confirm and apply;
10. verify the imported member appears disabled;
11. verify preview/apply mutations used dual CSRF body + header.

Retained browser audit flags include:

- `member_metadata_export=true`
- `member_import_preview=true`
- `member_import_apply=true`
- `dual_csrf_transport=true`
- `console_errors=false`

## Exact green application candidate

Candidate SHA:

`723c9c2191542e6f6867ee5fbbc31083590b49f2`

Workflow:

`37527877646` — **PASS**

The exact run passed:

- static/security/config/integration validation;
- dev.3 WireGuard network-survival regression;
- centralized SoftTimer member regression;
- dev.4 member migration transaction regression;
- accounting integration and replay/persistence stress;
- Playwright browser runtime audit;
- Android current/rescue build;
- Android Device Owner emulator;
- ESP8266 and ESP32 builds/simulations;
- Ruijie build/simulation;
- required Orange Pi builds/simulations;
- x86_64 build and QEMU simulation;
- transactional update bundle;
- final candidate gate.

## Integration guard

At application-candidate completion, dev.4 was 27 commits ahead / 0 behind current `main`, with:

- zero `profiles/standalone-rental` changes;
- zero frozen v0.5.2 signing/release workflow changes.

The documentation commits after the application candidate must receive their own workflow pass before integration.

If `main` advances before integration, do not force it. Reconcile through a normal integration branch/PR and validate the synthetic merge tree before merging.
