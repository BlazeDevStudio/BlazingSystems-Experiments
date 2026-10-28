// Opt-in ConnectIT compile-time test bridge against LAN Messenger 0.3.2+15.
// Baseline exact SHA 7d8a08afb39bab8d001fce3d3ba33706e034fcb1.
// This file is NOT imported by main.dart and changes no existing runtime flow.
import 'dart:io';
import '../src/node.dart';
import '../src/intercom.dart';
import '../src/protocol.dart';

class ConnectITLanV032Bridge {
  static const bool enabledByDefault = false;
  final LanNode node;
  final Intercom intercom;
  final bool enabled;
  ConnectITLanV032Bridge({required this.node, required this.intercom,
    this.enabled = enabledByDefault});

  static void requireOptIn(bool enabled) {
    if (!enabled) throw StateError('ConnectIT test integration is disabled');
  }

  Peer _requireKnownOnlinePeer(String peerId) {
    requireOptIn(enabled);
    final peer = node.peers[peerId];
    if (peer == null || !node.isOnline(peer)) {
      throw StateError('LAN peer is unavailable; no implicit internet fallback');
    }
    return peer;
  }

  Future<bool> isPeerReachable(String peerId) async {
    if (!enabled) return false;
    final peer = node.peers[peerId];
    return peer != null && node.isOnline(peer);
  }

  Future<void> sendLocalText(String peerId, String text) =>
      node.sendMessage(_requireKnownOnlinePeer(peerId), text);

  Future<void> sendLocalFile(String peerId, String path) =>
      node.sendFile(_requireKnownOnlinePeer(peerId), File(path));

  Future<void> startLocalCall(String peerId, {required bool video}) =>
      intercom.call(_requireKnownOnlinePeer(peerId), withVideo: video);
}

/// Seed transport policy only; legacy LAN file sending remains local.
class ConnectITSeedPayloadGate {
  static const maxEncryptedBytes = 8192;
  static bool permits(String kind, int decodedCiphertextSize) =>
      (kind == 'message' || kind == 'signal') &&
      decodedCiphertextSize > 0 && decodedCiphertextSize <= maxEncryptedBytes;
}
