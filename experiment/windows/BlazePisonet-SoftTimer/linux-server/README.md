# Linux LIO disk preparation (lab preview)

`blaze_lio_prepare.py` prepares one **disabled** Linux LIO iSCSI target for one
pre-existing Windows disk image and one initiator. It writes actual configfs
objects through `rtslib-fb`; it is not a simulator. It does not create or alter
the image, enable the target, configure DHCP/PXE, or claim that Windows booted.

Use only on a dedicated, approved noncustomer Linux host with `rtslib-fb`,
mounted `configfs`, and an empty LIO configuration. Run as root. Prepare a
root-owned `0700` directory for the spec/CHAP file, a separate root-owned
`0700` state directory, and a root-owned `0700` image directory containing a
pre-existing `0600`, single-link, block-aligned image of at least 16 GiB.
The spec and secret file must each be root-owned `0600` regular files. The
secret file contains exactly 16 printable ASCII bytes followed by a newline;
do not pass the secret on the command line or commit it to source control.

Example spec (replace all identities and paths with lab values):

```json
{
  "target_iqn": "iqn.2026-10.example.net:blaze-win-01",
  "initiator_iqn": "iqn.2026-10.example.net:win-01",
  "portal_ipv4": "192.168.44.2",
  "image_path": "/srv/blaze-private/win-01.img",
  "storage_name": "blaze_win_01"
}
```

Run `python3 blaze_lio_prepare.py /private/spec.json --secret-file
/private/chap.txt --state-dir /var/lib/blaze-lio` on the lab server. The
command refuses any existing LIO target, storage object, session, saved
configuration or prior/incomplete intent. A failure after intent creation is
**uncertain**: inspect the disabled target and saved config manually. Do not
delete the intent to force a retry; the first run may have committed the LIO
configuration even if its success response was lost.

The saved config can contain the CHAP secret and is restricted to `0600`.
The command does not install a boot-time restore service. Verify that the
actual target remains disabled across reboot before any live acceptance.
CHAP, initiator ACL and target exclusivity require independent tests from
the intended Windows client and a second unauthorized initiator. FOG imaging,
DHCP/PXE, per-client writable isolation, restore behavior, Windows boot,
reboot and power-loss tests remain separate release gates. This lab preview
does not change BlazePwifi paid v2 admission or authorize a release.
