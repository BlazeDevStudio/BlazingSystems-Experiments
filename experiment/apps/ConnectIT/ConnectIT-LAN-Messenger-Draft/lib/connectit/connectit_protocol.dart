/// ConnectIT v1 draft types. No automatic integration with existing LAN Messenger.
/// Server currently uses blaze-seed-v1 signed envelope compatibility.
const connectITProtocolMajor = 1;
const maxSignalCiphertextBytes = 8192;
const discoveryMaxSeedHops = 5;

enum ConnectITReachability { directLan, seed, offline, unknown }
enum ConnectITMessageKind { message, signal }

class ConnectITIdentity {
  final String id; // numeric string; never cast to int (leading zeros).
  final String nickname;
  const ConnectITIdentity(this.id, this.nickname)
      : assert(id.length == 10);
  bool get valid => RegExp(r'^\d{10}$').hasMatch(id);
}

class DiscoveredContact {
  final String connectITId;
  final String displayName;
  final ConnectITReachability reachability;
  final int? seedHops;
  final DateTime? lastSeen;
  final bool canConnect;
  const DiscoveredContact({required this.connectITId, required this.displayName,
    required this.reachability, this.seedHops, this.lastSeen,
    required this.canConnect});
  bool get valid => RegExp(r'^\d{10}$').hasMatch(connectITId) &&
      (seedHops == null || (seedHops! >= 0 && seedHops! <= 5));
}

class EncryptedTextEnvelope {
  final String id;
  final String fromId;
  final String recipientId;
  final String ciphertextBase64; // Already E2E encrypted by the client.
  final DateTime createdUtc;
  final ConnectITMessageKind kind;
  const EncryptedTextEnvelope({required this.id, required this.fromId,
      required this.recipientId, required this.ciphertextBase64,
      required this.createdUtc, this.kind = ConnectITMessageKind.message});
  bool get valid => RegExp(r'^\d{10}$').hasMatch(fromId) &&
    RegExp(r'^\d{10}$').hasMatch(recipientId) &&
    (id.length >= 16 && id.length <= 96) && ciphertextBase64.isNotEmpty;
}

class DeviceBindRequest {
  final String requestId, targetPublicKey, challenge;
  final DateTime startedUtc, expiresUtc;
  final int approvedIntervals;
  const DeviceBindRequest({required this.requestId, required this.targetPublicKey,
    required this.challenge, required this.startedUtc, required this.expiresUtc,
    required this.approvedIntervals});
  DateTime get earliestCompletionUtc =>
      startedUtc.add(Duration(minutes: (240 - 30 * approvedIntervals).clamp(0, 240).toInt()));
  int approvalInterval(DateTime serverNow) =>
      serverNow.difference(startedUtc).inSeconds ~/ 1200;
}
