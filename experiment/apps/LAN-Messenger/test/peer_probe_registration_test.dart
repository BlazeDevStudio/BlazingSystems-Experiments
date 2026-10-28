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
        main.indexOf('groupMessages.onChanged =', main.indexOf('n.onCallProbe =')));
    expect(binding, contains('mesh.hasLiveLinkSession(peer, sessionId)'));
    // Session admission is valid even before ICE negotiation clears the
    // connecting flag, preventing false-negative probes at call startup.
    expect(binding, isNot(contains('!inter.connecting')));
  });
  test('group call probes check the per-peer live link, not the room ID', () {
    final source = File('lib/src/group_call.dart').readAsStringSync();
    final begin = source.indexOf('bool hasLiveLinkSession(');
    final end = source.indexOf('static bool canCall', begin);
    expect(begin, greaterThan(0));
    expect(end, greaterThan(begin));
    final method = source.substring(begin, end);
    expect(method, contains('final link = links[peer.id]'));
    expect(method, contains('link.callId == callSessionId'));
    expect(method, contains('link.talkingTo?.id == peer.id'));
    expect(method, contains('!link.closing'));
    expect(method, contains('!active'));
    expect(method, isNot(contains('sessionId == callSessionId')));
    // The room and per-peer call IDs have different scopes.
  });

}
