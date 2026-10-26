# EasyMode 10.2.0 R281 handoff

## Live state

The 10.2.0 application update is running on the R281. The installer created `/root/easymode-before-v10.2-20261026-165405.tar.gz`. The cellular default route stayed on `eth1`, the health and quality services remained active, and the authenticated desktop and 390 px mobile screens were checked. Signal history and the mobile section picker returned live data. No test outage, router reboot or firmware flash was performed.

Traffic Intelligence Cellular edition 7.0.2 was installed on the R281. The service remained active and the mobile view picker switched from Overview to Devices. Website and Apps views now report estimated naming coverage and show DNS-only activity without inventing traffic. The browser had retained the old `/traffic/` document; the EasyMode link now uses `/traffic/?v=7.0.2` to load the updated page. Generic, AP, Router, Switch and PC bundles were built and their package contents and checksums were verified offline, but not installed on those hardware types.

## Reset-persistent image

A private R281 sysupgrade image combines the verified OpenWrt 24.10.8 R281 kernel, independently checked SquashFS root, EasyMode 10.2.0, Traffic Intelligence 7.0.2 and captured current router defaults. It is a candidate, not a flashed release. The earlier v10 reset-persistent kit was also built and `sysupgrade -T` tested, not flashed; `/rom/etc/blaze/easymode-version` on this router is still absent.

The R281 exposes one firmware partition and one rootfs volume. There is no verified second boot slot or automatic rollback. The device is physically inaccessible on a roof. A remote flash can be attempted over the current cellular path, but a bad image or first boot could require physical recovery. The image must pass a fresh on-router `sysupgrade -T` after the final rebuild, and the user must review this specific risk before a flash.

## Remaining validation

1. Observe a real degraded period and correlate client pings, router quality samples and event history. The available pasted pings lacked per-packet timestamps, and the bounded router log did not establish that reboot caused recovery.
2. In a maintenance window, test a reversible outage fixture: confirm a healthy secondary target or backup link prevents reboot; failed reconnect escalates to radio; the reboot budget persists across device boots.
3. Verify restore from the application rollback archive on a recoverable setup.
4. Validate the other five Traffic edition packages on representative OpenWrt hardware before advertising hardware support.

The QManager feature matrix is in [FEATURE-GAP.md](FEATURE-GAP.md). This revision does not claim full parity.
