# Tabler core UI asset

BlazePwifi Standard/Full builds use only the minified core CSS from `@tabler/core@1.6.1`.

- License: MIT.
- JavaScript is not required by BlazePwifi administration.
- Optional chart, calendar, editor and other plugin bundles are deliberately excluded.
- The CSS is staged only into Standard/Full build overlays. Lite router rootfs stays dependency-free.

The native BlazePwifi admin CSS remains a functional fallback when the optional stylesheet is absent.
