import 'connectit_protocol.dart';
import 'connectit_service.dart';

/// Example composition point; does NOT replace original LAN node.dart or intercom.dart.
/// The caller MUST encrypt text end-to-end and sign the relay envelope before calling.
class HybridConnectITAdapter {
  final ExistingLanMessengerPort lan;
  final SatelliteSeedPort seed;
  final DirectPeerTransportPort direct;
  HybridConnectITAdapter({required this.lan, required this.seed, required this.direct});

  Future<void> sendEncryptedText({required String? existingLanPeerId,
      required EncryptedTextEnvelope envelope,
      required String? separateLocalPlaintext}) async {
    // Preserve legacy LAN-only communication without requiring a ConnectIT account.
    if (existingLanPeerId != null && separateLocalPlaintext != null &&
        await lan.isPeerReachable(existingLanPeerId)) {
      await lan.sendLocalText(existingLanPeerId, separateLocalPlaintext);
      return;
    }
    if (!envelope.valid) throw ArgumentError('Invalid ConnectIT envelope');
    await seed.submitEncrypted(envelope); // Small encrypted message only.
  }

  Future<void> sendFile({required String connectITId, required String path,
    String? existingLanPeerId, Duration grace = const Duration(seconds: 45)}) async {
    if (existingLanPeerId != null && await lan.isPeerReachable(existingLanPeerId)) {
      return lan.sendLocalFile(existingLanPeerId, path);
    }
    // Connectivity negotiation may use an encrypted small Seed signal, but NOT file bytes.
    return direct.sendFileDirect(accountId: connectITId, path: path,
        reconnectGrace: grace);
  }

  Future<void> call({required String connectITId, String? existingLanPeerId,
    bool video = false, Duration grace = const Duration(seconds: 30)}) async {
    if (existingLanPeerId != null && await lan.isPeerReachable(existingLanPeerId)) {
      return lan.startLocalCall(existingLanPeerId, video: video);
    }
    return direct.callDirect(accountId: connectITId, video: video,
        reconnectGrace: grace);
  }
}
