# Setup Assistant — offline reference preview

Open `index.html` in any modern browser. Keep the `assets/` directory adjacent.
This manual-target UI does **not** read your device hardware automatically, create EFI,
download macOS, install anything, write USB storage or promise macOS booting.
Its working controls are: import local read-only scanner JSON (v1/v2, 1 MB maximum), CPU/GPU/firmware fields, Evaluate reference, Export JSON report. Scanner data never leaves the browser; this does not validate imported values.
Only specifically mapped example CPU SKUs are classified by architecture; all others report Unknown.
The original CSS background and button design use no externally hosted stock graphics.
See `assets/README.md` and `../LICENSES/LUCIDE-ISC.txt` for bundled third-party icons.
