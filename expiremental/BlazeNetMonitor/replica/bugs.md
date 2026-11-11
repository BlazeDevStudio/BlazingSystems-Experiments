# Known risks / open bugs

- S2: Legacy-style embedding within Explorer taskbar is intentionally not implemented; optional overlay may obscure tray icons. Default is above taskbar.
- S2: Multiple monitors and vertical taskbar layout not covered by integration testing.
- S3: Some ICMP-disabled sites appear red while HTTPS services are reachable; choose HTTPS checks.
- S3: Some Internet services do not accept HEAD; HTTP error classification currently treats 4xx as reachable.
- S3: Windows GDI/UI smoke tests, battery/resource profiling, x86 execution test not run.
- S4: No signed MSI/installer or brand assets in development preview.
