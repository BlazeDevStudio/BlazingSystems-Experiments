
## 2026-10-27 SOFTTIMER-NSIS-UNICODE actual RED, minimal input parser correction
- Exact TEST ONLY PR #223 SHA ee1b8f5ebef5760433df2b3682e3bfed7e52aa08: Windows #40451527593 HANDOVER PASS, native Windows builds/NSIS3.13 Setup compile PASS, compiled PE LegalCopyright check meaningful FAIL U+00C2 U+00A9 instead of U+00A9. Job #122015266282 log; installer execution, packaging and publication correctly skipped. No customer run.
- Before source, CURRENT_STATE recorded red/expected parser fix at b254eb2884bb6973571a457ad6df2d23b902cf40.
- Minimal code 7791025c18996dea5fa625128ebe3fcb660e35c7 modifies Windows workflow existing NSIS command to use documented /INPUTCHARSET UTF8 (BOM-less NSI), preserves all original installer source code and v0.4.0 release/version. Regression script e4a02293 and build gate 532ef7f2 unchanged.
- Status SOURCE_FIX_COMMITTED_FRESH_WINDOWS_CI_PENDING; no green claim from earlier RED. Require literal-head Windows job success including real native resource, Setup install/uninstall and mandatory handover; independent reviewer and unchanged active development HEAD before merge.
- No production tags/assets, keys, signing secrets, customer monetary data, device flashing or hardware. Separate publisher signing PR #217/#218 not merged. BlazePwifi production v0.6 #31/#32/#43/#34 still NO-GO.
