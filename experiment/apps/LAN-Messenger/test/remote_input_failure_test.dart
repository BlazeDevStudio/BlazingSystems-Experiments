import 'dart:io';

import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/identity.dart';
import 'package:lan_messenger/src/intercom.dart';
import 'package:lan_messenger/src/node.dart';
import 'package:lan_messenger/src/protocol.dart';

class _FailingSignalNode extends LanNode {
  _FailingSignalNode(super.identity);

  int attempts = 0;

  @override
  Future<void> signal(Peer peer, Map<String, dynamic> payload) async {
    attempts++;
    throw const SocketException('Simulated disconnect during remote gesture');
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('network loss during remote control never propagates an unhandled error',
      () async {
    final pair = await (await X25519().newKeyPair()).extract();
    final local = Identity(pair, 'Host');
    final node = _FailingSignalNode(local);
    final other = Peer(
        id: 'remote', key: 'remote-key', host: '127.0.0.1', port: 1234,
        name: 'Other device', seen: DateTime.now());
    final call = Intercom(node);
    call.callId = randomId();
    call.talkingTo = other;
    call.peerSharingScreen = true;
    call.remoteControlActive = true;

    await call.sendRemoteInput('click', 0.5, 0.5);
    await call.sendRemoteInput('up', 0.5, 0.5);
    await call.sendRemoteClick(0.5, 0.5);
    expect(node.attempts, 3);
  });

  test('invalid gestures are refused before touching the network', () async {
    final pair = await (await X25519().newKeyPair()).extract();
    final node = _FailingSignalNode(Identity(pair, 'Host'));
    final call = Intercom(node)
      ..callId = randomId()
      ..talkingTo = Peer(id: 'other', key: 'key', host: '127.0.0.1',
          port: 1, name: 'Other', seen: DateTime.now())
      ..peerSharingScreen = true
      ..remoteControlActive = true;
    await call.sendRemoteInput('quit', 0.5, 0.5);
    await call.sendRemoteInput('click', double.nan, 0.5);
    await call.sendRemoteInput('click', 2.0, 0.5);
    expect(node.attempts, 0);
  });
}
