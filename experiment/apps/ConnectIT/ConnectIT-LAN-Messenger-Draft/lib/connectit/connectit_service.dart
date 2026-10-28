import 'dart:typed_data';
import 'connectit_protocol.dart';

/// Keeps LAN Messenger's existing trusted local behavior fully separate.
abstract interface class ExistingLanMessengerPort {
  Future<bool> isPeerReachable(String existingLanPeerId);
  Future<void> sendLocalText(String existingLanPeerId, String plaintext);
  Future<void> sendLocalFile(String existingLanPeerId, String absoluteFilePath);
  Future<void> startLocalCall(String existingLanPeerId, {required bool video});
}

/// Master-only operations. Secure keystore-backed signing belongs in platform implementation.
abstract interface class MasterAuthorityPort {
  Future<ConnectITIdentity> signInAndEnroll({required String accountId,
    required String password, required Uint8List publicKey});
  Future<List<DeviceBindRequest>> pendingBindings();
  Future<void> approveBinding(String requestId, {required String confirmedLocalPin});
  Future<void> revokeBinding(String requestId, {required bool suspectedAttack});
}

/// A Seed accepts small, already-encrypted text or signaling only.
abstract interface class SatelliteSeedPort {
  Future<void> submitEncrypted(EncryptedTextEnvelope envelope);
  Future<List<EncryptedTextEnvelope>> inbox({required String perSeedCursor});
  Future<List<DiscoveredContact>> discover({required int maxSeedHops});
}

/// File bytes, camera frames and microphone packets MUST use this DIRECT channel.
abstract interface class DirectPeerTransportPort {
  Future<void> sendFileDirect({required String accountId,
    required String path, required Duration reconnectGrace});
  Future<void> callDirect({required String accountId, required bool video,
    required Duration reconnectGrace});
  Future<void> closeSession(String sessionId);
}

/// Implementations must NEVER automatically substitute Seed traffic for direct media.
class DirectOnlyPolicy {
  const DirectOnlyPolicy();
  Never noDirectPath() => throw StateError(
    'Direct connection unavailable: no file, audio or video relay is allowed.');
  bool mayRelayPayload(String kind) => kind == 'encrypted-text' ||
      kind == 'encrypted-small-signal';
}
