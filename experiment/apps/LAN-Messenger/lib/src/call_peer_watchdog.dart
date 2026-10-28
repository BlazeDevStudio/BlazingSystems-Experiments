/// Session-aware authenticated liveness checks supplement WebRTC ICE.
///
/// An abrupt process crash cannot send a hangup frame, and ICE may continue
/// reporting Connected until its next consent check. Two failed probes mark a
/// link suspect; a reconnect grace deadline is then anchored to the FIRST
/// failure so later retry attempts cannot extend it indefinitely.
enum CallProbeResult { active, ended, unreachable }
enum CallWatchdogChange { none, suspect, recovered, ended }

class CallPeerWatchdog {
  CallPeerWatchdog({DateTime Function()? now}) : _now = now ?? DateTime.now;
  final DateTime Function() _now;
  int _unreachable = 0;
  int _ended = 0;
  DateTime? firstUnavailableAt;
  bool get suspect => _unreachable >= 2;

  CallWatchdogChange report(CallProbeResult outcome) {
    switch (outcome) {
      case CallProbeResult.active:
        final changed = _unreachable > 0 || _ended > 0;
        _unreachable = 0;
        _ended = 0;
        firstUnavailableAt = null;
        return changed ? CallWatchdogChange.recovered
            : CallWatchdogChange.none;
      case CallProbeResult.ended:
        _unreachable = 0;
        firstUnavailableAt = null;
        _ended++;
        // Require two authenticated negative replies so a transient
        // negotiation overlap cannot instantly terminate a valid session.
        return _ended == 2 ? CallWatchdogChange.ended
            : CallWatchdogChange.none;
      case CallProbeResult.unreachable:
        _ended = 0;
        firstUnavailableAt ??= _now();
        _unreachable++;
        return _unreachable == 2 ? CallWatchdogChange.suspect
            : CallWatchdogChange.none;
    }
  }
  void reset() {
    _unreachable = 0;
    _ended = 0;
    firstUnavailableAt = null;
  }
}
