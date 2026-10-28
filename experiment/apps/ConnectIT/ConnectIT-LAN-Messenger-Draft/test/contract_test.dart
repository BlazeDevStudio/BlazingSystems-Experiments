// Run with dart test/contract_test.dart after installing Dart SDK.
import '../lib/connectit/connectit_protocol.dart';
import '../lib/connectit/mini_seed_policy.dart';
import '../lib/connectit/connectit_service.dart';

void main() {
  assert(ConnectITIdentity('0088821855','Alice').valid);
  assert(!ConnectITIdentity('123456789a','Bad').valid);
  assert(!const MiniSeedPolicy().mayForward(wifiConnected: true,
    meteredCellular: false, batterySaver: false, inForeground: true));
  assert(!const DirectOnlyPolicy().mayRelayPayload('file-bytes'));
  final req = DeviceBindRequest(requestId: 'r', targetPublicKey: 'p',challenge: 'c',
    startedUtc: DateTime.utc(2026), expiresUtc: DateTime.utc(2026,1,2), approvedIntervals: 1);
  assert(req.earliestCompletionUtc == DateTime.utc(2026,1,1,3,30));
  print('Draft Dart contract assertions completed.');
}
