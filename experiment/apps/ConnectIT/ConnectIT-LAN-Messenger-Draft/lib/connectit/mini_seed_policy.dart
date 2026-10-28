/// Draft opt-in only. Actual platform services/background constraints are not implemented.
class MiniSeedPolicy {
 final bool enabled, wifiOnly, allowCellular, batterySaverRestriction;
 final bool allowBackground;
 final int maxKilobytesPerSecond, maxCacheMiB;
 const MiniSeedPolicy({this.enabled = false, this.wifiOnly = true,
   this.allowCellular = false, this.batterySaverRestriction = true,
   this.allowBackground = false, this.maxKilobytesPerSecond = 64,
   this.maxCacheMiB = 16});
 bool mayForward({required bool wifiConnected, required bool meteredCellular,
   required bool batterySaver, required bool inForeground}) =>
   enabled && (!wifiOnly || wifiConnected) &&
   (!meteredCellular || allowCellular) &&
   (!batterySaverRestriction || !batterySaver) &&
   (inForeground || allowBackground) && maxKilobytesPerSecond > 0 &&
   maxCacheMiB > 0;
}
