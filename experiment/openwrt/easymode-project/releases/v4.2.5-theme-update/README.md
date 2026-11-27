# R281 EasyMode — visual refresh 4.2.5

The installed R281 build is the functional reference. Version numbers are identifiers, not rankings. This release preserves its features and settings and adds an original lightweight visual theme inspired by CoreUI and Metis.

The update adds `root/www/easy/refined.css` (about 6 KB). It retains the existing CSS, JavaScript application, header navigation, SMS conversations, device access, network tools, repeater controls, and light/dark preference. There is no React, Bootstrap, external font, downloaded asset, new JavaScript dependency, polling loop, or router service.

Four deployed files changed: the new stylesheet, the index page that loads it, the application version plus an outdated LED help paragraph, and the version marker. No feature logic changed. Private settings are not included.

## Source reconciliation

Read [LIVE-SOURCE-AUDIT.json](LIVE-SOURCE-AUDIT.json). All 46 files represented by the published 4.2.3 R281 source plus the 4.2.4 access update were compared against the actual installed router. Of these, 43 match byte-for-byte; the remaining three are the version marker, app.js and index.html supplied here. The fourth file here is the new stylesheet. This establishes the exact source relationship instead of treating the separate 5.0 alpha toolkit as an upgrade.

The complete published application reference is the 4.2.3 R281 source, overlaid with 4.2.4 access files, then these 4.2.5 files. This is source composition, not a generic installation procedure. Router services, packages and private configuration prerequisites still matter. Do not install the alpha toolkit over a working R281 expecting feature parity.

## Verification on the existing router

- All four deployed files read back and matched the local files; no restart was needed.
- JavaScript syntax check passed. The app diff contains only the version and LED help text.
- Login and overview rendered with live data; the existing SMS inbox and conversations loaded.
- Device-access settings remained available; no access-policy changes were made.
- Appearance saved in both light and dark modes. The original light preference and blue accent were restored.
- Desktop and 390-pixel phone layout inspected; navigation remains horizontally scrollable on small screens.

These are theme regression checks, not a new certification of every modem operation. This update was not flashed into a firmware image and does not establish factory-reset persistence. Existing archived firmware/installers are unchanged.

## Recovery

The private before-change archive is retained locally, outside the public repository. To remove only the visual overlay, remove its stylesheet link from `/www/index.html`; the original `style.css` remains present. A complete rollback should restore the three replaced files from that archive as a matched set. Avoid copying older full releases over newer user changes.

See [THEME-NOTICES.md](THEME-NOTICES.md) for visual-reference attribution. No private screenshots, router credentials, SMS contents, or device configuration are published.
