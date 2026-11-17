# PHX-MASTER — COE appliance IPv6 ULA prefix contract audit

**Checkpoint:** 2026-11-17 UTC11  
**Disposition:** P0 integration blocker / destination remains draft / PRODUCTION NO-GO  
**Scope:** coordination/phoenix only; no subsystem source changes

## Exact refs

- Experiments main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Experiments blazepwifi-v0.5.3-development: aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master #288 before this commit: f63357a12ffdd5894f8697cfc6bd4b502108064e.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE #26: b382d233ff06c8791b1028bed3c617cc7b670d12, open/draft.
- COE #31: 43e70422990857168c61c77b47fdd742f34d7846, open/draft, based on #26.

The private canonical Drive registry v11 and newer corrections were not retrievable through the exposed connector surface. No older Library snapshot was substituted.

## Source finding

COE #26 tools/package_appliance_firmware.py blob c6ad3807d7fedb00ab7560813b82810cb8cce751 emits the hard-coded line:

    option ula_prefix 'fd00:db8:blaze::/48'

Current COE #31 packager blob 5e42d81e0e56e5cc420f017a5da2e9423122608f adds interface-token and VLAN validation but still emits the same literal. The EW1200G Pro profile blob 6e797cf9c9922209efe4c0da49c49fa1da16c11a has no networking.ula_prefix property.

COE #31 test file blob 109d1ee2370f79211f205bd9478091d2d1dbe837 tests generated UCI for six profiles but has no ULA/IPv6 assertions. COE #26 base test blob 8f6b2f849152902c341428067e52fe95f6763b93 has the same coverage gap.

## Bounded test actually executed

Python standard-library ipaddress.IPv6Network(..., strict=True):

- fd00:db8:blaze::/48: REJECTED because blaze contains non-hexadecimal characters.
- fd12:3456:789a::/48: ACCEPTED, valid /48 within fd00::/8 and fc00::/7.
- 2001:db8::/48: syntactically valid IPv6 but outside ULA space.
- fd12:3456:789a::/64: valid ULA space but wrong /48 profile length.

This is a parser check of the exact emitted literal, not OpenWrt uci/netifd execution, repository unit tests, ImageBuilder validation or a router test.

## Required contract and owner actions

1. Emit only a strictly parsed RFC 4193 ULA in fd00::/8 with /48 prefix length. Reject malformed, non-ULA, host-bit-set, wrong-length and missing values before staging any UCI.
2. Do not replace the invalid literal with one globally hard-coded example. Define a reviewed profile prefix or deployment-time generation/persistence policy giving each independent LAN/site a unique prefix; devices on the same LAN share that site's prefix.
3. PHX-RELEASE owns packager/profile/test correction on its existing branch or a clearly stacked draft. Master does not edit tools/package_appliance_firmware.py or its tests.
4. PHX-CORE and the COE integration owner define the intended deployment-scoped prefix policy. PHX-QA independently tests valid/invalid values at exact head. PHX-HARDWARE validates target-specific OpenWrt behavior only after correction and owner authorization.

## Exact CI context

- COE #31 head 43e70422990857168c61c77b47fdd742f34d7846: case-collision 44074188531 SUCCESS and Hardware & Shared Contracts 44074188480 SUCCESS. These scoped checks do not prove ULA validity.
- COE #26 head b382d233ff06c8791b1028bed3c617cc7b670d12: five workflows QUEUED — 43096752609, 43096752632, 43096752800, 43096752563, 43096752557.
- HARDWARE #317 head 3827fb3b2bd58e8f84c6d61020bfd5b863bdf14a: focused 44072521452 and 44072521239 SUCCESS; Full 44072521235 FAILURE in QA legacy poll-signature fixture. Preserve default-deny.
- CORE #252 c82705f2de865c89ab733b10efa84f26f56a5cc4: 42698139210 SUCCESS, scoped.
- RENTAL #289 68928774d0d7cf65adb26bc6b54199a3159d066c: 43653329235 and 43653329229 SUCCESS, scoped.
- PISONET #255 d01fd1642c105b3b0f6cd3343d1c9b67291f6e09: 42462978704 SUCCESS, scoped.
- QA #290 5c29d15994cee1279058f1eca12f2a3180704292: 43633486963 SUCCESS, scoped; QA #292 has no PR-triggered run returned.
- RELEASE #291 2c4edff231d9b2819415086825530d80b8801307: 43744993487 SUCCESS, scoped.

These are role-specific workflow observations, not combined integration or production acceptance.

## Disposition

Keep COE #26 and #31 draft. OWNERSHIP_ROUTES.json remains unchanged at DRAFT_REVIEW_ONLY. No copy, overwrite, relocation, merge, release, flash or financial migration is authorized. Protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration, independent QA, native acceptance, 150 real power cuts and 30-device/24-hour soak remain unverified.