# Multi-project workspace collections (v0.4.6 development)

A **project** remains exactly one independently buildable target, with its own FQBN, source, libraries, pins, and sketch export. A **workspace** is a persisted membership collection of up to 100 existing project IDs. Projects may belong to multiple collections; no firmware images are merged or cross-compiled.

Use the left **Workspace collection** selector. Create a workspace, open/create projects, then **Add current** or **Unlink current**. The sidebar filters membership; **All projects** never hides an otherwise valid project. Multiple project tabs stay open in the current application session, but only the active tab is edited or compiled; switching saves outstanding changes. Closing a tab never deletes its source. Deleting a workspace destroys only the collection, not its projects.

Catalog is stored separately as `_workspaces.json` alongside local project folders with atomic replacement. Membership IDs are validated and must exist when linked. Trashed projects remain referenced and appear in `missingIds`, so recovery restores membership without silently dropping relationships. Corrupt catalogs fail closed; the independent project store remains available.

Not implemented here: graphical communication relationships, multi-project simultaneous compilation, project ZIP bundles, shared asset indexes, persistent tab layout across restarts, physical device integration. The current workspace editor does not merge projects into one `.ino` or sign/upload firmware.
