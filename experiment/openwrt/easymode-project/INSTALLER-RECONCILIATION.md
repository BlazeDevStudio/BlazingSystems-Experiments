# EasyMode installer and source reconciliation

Audited 2026-10-08 against repository main `7f53c977e5b036b5e959935c7f8ba54175f88fe5`, then compared published R281 application source with the running router.

**The installed R281 application is the functional reference.** Numeric versions do not establish feature quality or superiority. The separate `5.0.0-alpha.1` toolkit does not replace the feature-complete installed UI merely because its number is larger. This audit preserves the installed feature set and the owner's changes.

| Artifact | Actual contents / behavior | Relationship to the installed R281 |
|---|---|---|
| Preserved 4.1.4 | Historical baseline | Keep for history; not the current target |
| 4.2.1 / 4.2.2 / 4.2.3 R281 source | Successive hardware-specific application snapshots | Historical source lineage |
| 4.2.4 access update | Eight-file incremental update adding system-wide client access controls | Required overlay on 4.2.3 source |
| 4.2.5 visual refresh | Four-file incremental update, including original plain CSS | Current installed visual refresh; retains existing features |
| 4.2.3 encrypted personal installer | Earlier private recovery/firmware package | Predates access and theme changes; not a current system backup |
| 5.0.0-alpha.1 editions | Cellular, AP, router, switch, PC, generic manifests | Toolkit structure; edition names alone do not demonstrate working feature implementations |
| Offline HTML | Tests login and system board through `/ubus`; bootstrap button logs an unimplemented message | Does not install the R281 portal; backup and edition controls are not an installation implementation |
| Windows PowerShell | Requires a separate `easymode-upload.tar.gz`, transfers it using SSH/SCP and invokes the shell installer | Launcher for the alpha bundle, not an installer for the running R281 application |
| OpenWrt install.sh | Copies core/modules/editions to `/usr/lib/easymode`, writes profile, verifies detector | Does not install the live web root, RPC backend or hardware helper set |
| build-release.sh | Packages the alpha toolkit folders and installer sources | Does not build a matching R281 portal or firmware |

## Evidence and resolved catalog issues

All six edition manifests, root VERSION, MANIFEST and shell installer identify the alpha toolkit consistently. The problem is payload coverage, not version ordering. The prior README called two historical R281 snapshots “current deployed,” while latest.json pointed to a `releases/v5.0.0-alpha.1/` directory absent from the audited Git tree. The catalog now names the installed reference explicitly and distinguishes source updates from runnable installers. This finding concerns the repository tree, not an exhaustive claim about every GitHub release asset.

The live source audit compares 46 application files in the combined published 4.2.3 + 4.2.4 source against the router. Forty-three match exactly. Three differ only because this turn updated the version marker, index and app version/LED help text. The additional refined.css is supplied in 4.2.5. Existing app functionality was retained, rather than replaced with the alpha toolkit.

## Remaining installer gaps

1. The universal toolkit needs the installed application's actual UI, RPC, helper and dependency integration before it can claim equivalent features. Hardware-specific operations must remain capability-gated. This theme task does not establish compatibility with other boards.
2. The Windows launcher requires its matching bundle, which is not beside the script in the audited source tree.
3. The offline HTML bootstrap is a placeholder. It should not be presented as a working full installer.
4. The alpha shell installer stores its backup in `/tmp`, so it is lost on reboot. Its rollback helper accepts an existing directory without validating that it is a complete matching backup before removing the installation prefix. Do not use it as verified recovery for the current router.
5. Static checks validate syntax and JSON; they do not prove the installer's payload reproduces the portal. The shell test's `find -exec sh -n` also does not reliably propagate child syntax failures through find's exit status.
6. Archived firmware has not been regenerated or flashed with the current access/theme changes. Reset persistence cannot be inferred from a successful web-file update.

No universal installer or firmware executable was run against the live router during this audit. Older releases remain immutable for traceability. Current installer parity remains unfinished; the catalog and source lineage are now reconciled with the installed build.
