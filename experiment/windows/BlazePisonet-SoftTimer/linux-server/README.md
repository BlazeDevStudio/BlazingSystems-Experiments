# Linux LIO disk preparation (lab preview)

This server component has its own `v0.1.0-preview.2` source bundle. On a
trusted build checkout, `sh build-preview.sh /absolute/output/directory`
produces a deterministic `BlazePisonet-LIO-v0.1.0-preview.2-linux.tar.gz`
and a SHA256SUMS file. Verify the published digest against the reviewed CI
artifact before extracting it. On an **approved noncustomer Linux lab host**,
unpack the archive and run `sudo sh install-preview.sh --prefix
/opt/blaze-lio-preview --confirm-lab-install` from inside the unpacked folder.
The installer checks the complete file manifest, stages root-owned code and
refuses an existing target or a non-root/writable path ancestor. To remove an
unmodified code install, run `sudo sh uninstall-preview.sh --prefix
/opt/blaze-lio-preview --confirm-lab-uninstall` from the reviewed bundle.
Uninstall refuses changed or extra files and never removes LIO, SSH, images,
state or network configuration. Inspect a refused install manually instead
of deleting the path blindly. Neither command installs Python, `rtslib-fb`, SSH keys,
sshd configuration, LIO targets, images, DHCP/PXE or a boot service. The
manifest detects accidental file changes within the bundle; it is not a
signature or independent origin proof. Keep the pinned CI artifact digest
with the lab acceptance record. Physical uninstall/recovery still needs
approved hardware testing.

`blaze_lio_prepare.py` prepares one **disabled** Linux LIO iSCSI target for one
pre-existing Windows disk image and one initiator. It writes actual configfs
objects through `rtslib-fb`; it is not a simulator. It does not create or alter
the image, configure DHCP/PXE, or claim that Windows booted.

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
Preparation rechecks the complete live and saved target before recording
`prepared_disabled`; a mismatch leaves the intent uncertain and refuses retry.
The command does not install a boot-time restore service. Verify that the
actual target remains disabled across reboot before any live acceptance.
On the same dedicated host, `python3 blaze_lio_status.py /private/spec.json
--secret-file /private/chap.txt --state-dir /var/lib/blaze-lio` performs a
read-only check of the private intent, image identity, saved configuration and
live disabled LIO target. It prints only `PREPARED_DISABLED` after all checks
pass. Missing, corrupt, active or incomplete intent and policy drift produce
no success output. This local command does not open a network management port
or expose the CHAP secret. Remote SoftTimer management still needs an
authenticated, provisioned channel and approved noncustomer acceptance.
For a dedicated approved **lab** server, `blaze_lio_ssh_status.py` is an
optional forced SSH command for the same local disabled-target check. It reads
only `/etc/blaze-lio/ssh-status.json`, a root-owned `0600` regular file inside
a root-owned `0700` directory, with exact absolute `spec`, `secret_file`, and
`state_dir` paths. It accepts only the SSH original command
`blaze-lio-status`, runs the existing local inspection as root, prints only
`PREPARED_DISABLED` on exact success, and never enables a target. Provision a
dedicated SSH identity with a server-side forced command and `restrict` key
option, no shell, forwarding or PTY access, under an approved privilege
policy. The preview does not generate keys, change sshd, grant root access,
install a listener, or establish the host's identity. The operator must pin
the host key in a separate known-hosts file and supply its path and the SSH
identity path to SoftTimer for that session. SoftTimer uses Windows OpenSSH
with `-F none`, strict host-key checking, public-key-only batch mode, no
forwarding and a fixed remote command. If OpenSSH Client is absent, the check
refuses until it is installed. A successful response is a **read-only claim
from that authenticated server**, not proof of CHAP refusal, persistence or
Windows boot. See the [OpenSSH client manual](https://man.openbsd.org/ssh.1),
[server forced-key restrictions](https://man.openbsd.org/sshd.8), and
[Microsoft's Windows OpenSSH guidance](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_overview).
For a dedicated **noncustomer lab only**, `blaze_lio_activate.py` with the same
spec, secret and state directory plus `--confirm-lab-activation` inspects the
live LIO target, backing image, ACL/CHAP, LUN mapping, portal and disabled
saved configuration before enabling the target. It writes an `activating`
intent before the enable call. A partial write, crash or lost result refuses
retry; the command attempts to disable the target on ordinary errors and
refuses quarantine completion unless the private saved restore configuration
matches the complete disabled live target. A crash can still leave it live.
An operator must inspect the target and intent before
any recovery. `ACTIVE_LAB_TARGET` means only that the target enable and saved
configuration calls completed; it is not a boot, isolation or hardware pass.
CHAP, initiator ACL and target exclusivity require independent tests from
the intended Windows client and a second unauthorized initiator. FOG imaging,
DHCP/PXE, per-client writable isolation, restore behavior, Windows boot,
reboot and power-loss tests remain separate release gates. This lab preview
does not change BlazePwifi paid v2 admission or authorize a release.

SoftTimer's generated iPXE script is for a supervised lab boot. It prompts
before `sanboot`; enter the client's initiator IQN as the CHAP username and
the corresponding secret provisioned on this dedicated target. Cancelling
the prompt exits the script. The saved client profile, DHCP root path and
iPXE script contain no secret. This prompt is not unattended credential
provisioning or proof that Windows can boot from the target.
