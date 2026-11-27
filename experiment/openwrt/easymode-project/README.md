# EasyMode for OpenWrt

**Functional reference: the installed R281 EasyMode**, now at 4.2.6 with client presence and session history. Version numbers identify separate work; they do not rank feature completeness.

The current router retains its existing SMS, cellular, repeater, Wi-Fi, LED, device-access and other controls. The visual refresh combines CoreUI/Metis design cues using about 6 KB of original CSS, with no React or Bootstrap runtime.

## Current source and audit

- [Consolidated current application source — 4.2.6](releases/v4.2.6-r281-consolidated/)
- [Handoff for 6.0 development](releases/v4.2.6-r281-consolidated/HANDOFF-6.0.md)

- [4.2.5 live theme and source comparison](releases/v4.2.5-theme-update/)
- [Installer reconciliation audit](INSTALLER-RECONCILIATION.md)
- [4.2.4 system-wide device-access update](releases/v4.2.4-access-update/)
- [4.2.3 R281 source snapshot](releases/v4.2.3-r281-experiment/)

The 4.2.6 folder consolidates the current application source and includes client tracking, so development no longer needs the earlier overlays. Its 50 application files were compared with the installed R281. External package prerequisites are documented; this is a development snapshot, not standalone universal installation or flashable firmware.

## Separate universal toolkit

The root VERSION and six edition manifests still identify `5.0.0-alpha.1`: an unfinished toolkit for cellular, AP, router, switch, PC and generic editions. This is not a feature upgrade for the current R281.

The offline HTML tests connectivity but does not install. The Windows launcher requires a matching external bundle. The shell installer copies toolkit folders but does not deploy the running R281 web application and backend. See the audit before using these artifacts.

## History and recovery

4.1.4 is preserved history. The 4.2.1, 4.2.2 and 4.2.3 R281 releases are historical snapshots. The encrypted personal 4.2.3 installer predates the current access controls and theme; it is not a current system backup. Existing firmware packages were not rebuilt or flashed in this visual update. Factory-reset persistence remains separate work.

Private credentials, settings, SMS and device backups are not included in the public source updates.
