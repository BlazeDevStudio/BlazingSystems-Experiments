import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/connectit/lan_v032_bridge.dart';

void main() {
  test('ConnectIT is disabled in unmodified LAN Messenger by default', () {
    expect(ConnectITLanV032Bridge.enabledByDefault, isFalse);
    expect(() => ConnectITLanV032Bridge.requireOptIn(false), throwsStateError);
    expect(() => ConnectITLanV032Bridge.requireOptIn(true), returnsNormally);
  });

  test('Seed accepts bounded text/signals, never file/media payloads', () {
    expect(ConnectITSeedPayloadGate.permits('message', 8192), isTrue);
    expect(ConnectITSeedPayloadGate.permits('signal', 1), isTrue);
    expect(ConnectITSeedPayloadGate.permits('message', 8193), isFalse);
    expect(ConnectITSeedPayloadGate.permits('message', 0), isFalse);
    for (final kind in ['file', 'file-bytes', 'audio', 'video', 'media', 'chunk']) {
      expect(ConnectITSeedPayloadGate.permits(kind, 32), isFalse);
    }
  });
}
