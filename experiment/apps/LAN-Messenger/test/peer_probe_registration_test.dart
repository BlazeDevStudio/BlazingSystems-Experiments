import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('app must register authenticated call-probe handler on its LAN node', () {
    // Cross-file reconciliation can accidentally replace main.dart with an
    // older version while retaining node/intercom watchdog source. Without
    // this registration EVERY active call responds false to a probe and is
    // automatically terminated within two watchdog polls.
    final main = File('lib/main.dart').readAsStringSync();
    expect(main, contains('n.onCallProbe = (peer, sessionId)'));
    expect(main, contains('inter.callId == sessionId'));
    expect(main, contains('inter.talkingTo?.id == peer.id'));
    expect(main, contains('!inter.closing'));
    final binding = main.substring(main.indexOf('n.onCallProbe ='),
        main.indexOf('final groupMessages =', main.indexOf('n.onCallProbe =')));
    // Session admission is valid even before ICE negotiation clears the
    // connecting flag, preventing false-negative probes at call startup.
    expect(binding, isNot(contains('!inter.connecting')));
  });
}
