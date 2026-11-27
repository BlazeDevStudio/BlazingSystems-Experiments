# STORCHK-0674: inspect kernel mountinfo; NEVER mount, write or certify power-cut.
# Use: awk -v want=/tmp/blaze-v2-native-ID \
#   -v scratch=/mnt/blaze-v2-lab-media-ID -v source=/dev/sdXN \
#   -f tools/v060_lab_mountinfo_guard.awk /proc/self/mountinfo
# /proc/*/mountinfo spec: ID PARENT MAJ:MIN ROOT MOUNT OPTS ... - FSTYPE SOURCE OPTIONS
function rw(opts) { return index("," opts ",", ",rw,") > 0 }
BEGIN {
  if (want !~ /^\/tmp\/blaze-v2-native-[A-Za-z0-9_-]+$/ ||
      scratch !~ /^\/mnt\/blaze-v2-lab-media-[A-Za-z0-9_-]+$/ ||
      source !~ /^\/dev\/[A-Za-z0-9_.\/-]+$/ ||
      source ~ /\.\./ || source ~ /^\/dev\/(root|ram|loop|zram|mtd|ubi|nbd)/) {
    invalid_input=1
  }
}
{
  separator=0
  for (i=7; i<=NF; i++) if ($i=="-") { separator=i; break }
  if (!separator || separator+3>NF) next
  if ($5==want) {
    target_count++
    target_device=$3; target_root=$4; target_opts=$6
    target_fs=$(separator+1); target_source=$(separator+2)
  }
  if ($5==scratch) {
    scratch_count++
    scratch_device=$3; scratch_root=$4; scratch_opts=$6
    scratch_fs=$(separator+1); scratch_source=$(separator+2)
  }
}
END {
  if (invalid_input || target_count!=1 || scratch_count!=1 ||
      target_device!=scratch_device ||
      target_root=="/" || target_root !~ /^\// ||
      index(target_root, "\\") || index(scratch_root, "\\") ||
      scratch_root!="/" || target_source!=source || scratch_source!=source ||
      target_fs!=scratch_fs || !rw(target_opts) || !rw(scratch_opts) ||
      !(target_fs=="ext4" || target_fs=="f2fs" ||
        target_fs=="xfs" || target_fs=="btrfs")) {
    print "STORCHK-0674 BLOCKED: missing/unsafe persistent scratch bind mount; no power-cut authorization" > "/dev/stderr"
    exit 9
  }
  print "STORCHK-0674 PASS: explicitly matched nonvolatile scratch bind mount (NOT power-cut verified)"
  print "source=" source
  print "filesystem=" target_fs
  print "scratch_mount=" scratch
  print "actual_fixture_mount=" want
  print "physical_powercut_verified=0"
  print "customer_install_authorized=0"
}
