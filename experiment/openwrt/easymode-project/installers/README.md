# Current installer entry points

Use exactly one generated Traffic Intelligence 7.0.2 edition archive from the [public candidate release](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/easymode-r281-v10.2.0-5b1e4ab15bf2). It contains the common IPK, edition IPK, checksum-verifying `install.sh`, and Windows `Update-EasyMode.bat` / PowerShell launcher. No passwords are embedded and no firmware is flashed automatically.

The historical HTML utility is informational only. The old v5 copying/launcher implementation is retired; current wrappers direct administrators to the actual v7 packages. These packages add the shared Traffic dashboard on six capability profiles. They do not install the board-specific R281 EasyMode 10.2 management app; use the [R281 app installer](../releases/v10.2.0-r281-candidate/) for that exact board and release. See [Traffic installation instructions](../traffic/README.md) for prerequisites and rollback.
