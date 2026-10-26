# R281 clean firmware baseline

`base/root.tar.gz` and `base/kernel.bin` are the clean OpenWrt 24.10.8 Notion R281 filesystem and kernel used for public EasyMode candidates. They were extracted from a community R281 sysupgrade image already held in the project workspace. The original builder and complete build recipe for that community image have not been identified; this is a pinned binary baseline, not a claim of a fully source-reproducible OpenWrt build.

- Community sysupgrade SHA-256: `dc39c985658dc959238c02cf09dba947b4c32e205165a0e4a4a138b4f9d66790`
- Uncompressed clean root tar SHA-256: `2f772c623ff3b056e09eb228a455afbdda4e5446102949c30b18dda0c108b143`
- Kernel SHA-256: `24c963f1af83756de4943a195ac95c4a4b7285c0097fbc985e8e00347f2e1973`

The clean root has a blank default OpenWrt root password, no Wi-Fi profile, no SSH host identity and no TLS private key. The public EasyMode builder rejects a changed root baseline or kernel, checks for device credentials, and checks every packed SquashFS file, mode and link after building. The public candidate still requires hardware boot and recovery testing; the local R281 test only verified that `sysupgrade -T` accepts the image. The device-specific firmware with current network settings and identities is kept in the owner's approved Drive folder, never in this repository.

Source for the common OpenWrt components is available from the [OpenWrt 24.10.8 release](https://downloads.openwrt.org/releases/24.10.8/). The R281 board profile is not present in the official 24.10.8 ramips/mt7621 image list; determine the community baseline's full source provenance before describing this as a fully reproducible product release.
