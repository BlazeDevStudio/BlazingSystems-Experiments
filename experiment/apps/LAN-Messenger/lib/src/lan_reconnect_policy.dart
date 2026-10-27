import 'dart:async';
import 'dart:io';

/// Settings bounds shared by call grace and interrupted file transfers.
class LanReconnectPolicy {
  static const choicesSeconds = [15, 30, 60, 120, 300];
  static int clampSeconds(Object? value) =>
      value is int && choicesSeconds.contains(value) ? value : 60;

  /// A routed discovery seed is not a proxy, relay or internet peer.
  /// Permit only explicit RFC1918 IPv4 destinations, not arbitrary URLs,
  /// multicast, loopback, broadcast, public IPs or hostnames.
  static String? privateIpv4Seed(String raw) {
    final input = raw.trim();
    final ip = InternetAddress.tryParse(input);
    if (ip == null || ip.type != InternetAddressType.IPv4 ||
        input != ip.address) return null;
    final parts = input.split('.').map(int.parse).toList();
    if (parts[0] == 10 ||
        (parts[0] == 172 && parts[1] >= 16 && parts[1] <= 31) ||
        (parts[0] == 192 && parts[1] == 168)) {
      // Reject gateway wildcard/broadcast addresses; no network scan.
      if (parts[3] == 0 || parts[3] == 255) return null;
      return input;
    }
    return null;
  }
}

/// The disconnected grace countdown is per call, not a new call model.
/// A restored connected state cancels it. Repeated disconnected events do
/// not extend the original deadline indefinitely.
class LanDisconnectGrace {
  LanDisconnectGrace(this.onExpired);
  final void Function() onExpired;
  Timer? _timer;
  bool get waiting => _timer?.isActive ?? false;

  void disconnected(Duration grace) {
    if (waiting) return;
    _timer = Timer(grace, () {
      _timer = null;
      onExpired();
    });
  }

  void connected() { _timer?.cancel(); _timer = null; }
  void dispose() => connected();
}
