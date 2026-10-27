import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/lan_reconnect_policy.dart';

void main() {
  test('bounded grace is saved only for supported values', () {
    expect(LanReconnectPolicy.choicesSeconds, [15, 30, 60, 120, 300]);
    expect(LanReconnectPolicy.clampSeconds(120), 120);
    expect(LanReconnectPolicy.clampSeconds(null), 60);
    expect(LanReconnectPolicy.clampSeconds(0), 60);
    expect(LanReconnectPolicy.clampSeconds(999999), 60);
    expect(LanReconnectPolicy.clampSeconds('300'), 60);
  });

  test('routed discovery accepts only private unicast IPv4', () {
    for (final addr in ['192.168.1.100', '10.0.0.20', '172.16.1.4',
                        '172.31.255.1']) {
      expect(LanReconnectPolicy.privateIpv4Seed(addr), addr);
    }
    for (final addr in ['1.1.1.1', '8.8.8.8', '127.0.0.1',
                        '169.254.1.2', '224.0.0.1', '255.255.255.255',
                        '192.168.1.255', '10.0.0.0', 'localhost',
                        'https://192.168.1.1', '192.168.1.1:39823',
                        '::1', '']) {
      expect(LanReconnectPolicy.privateIpv4Seed(addr), isNull,
          reason: 'Never allow unsolicited scans or public discovery');
    }
  });

  test('one disconnect starts exactly one bounded timer', () async {
    var expired = 0;
    final grace = LanDisconnectGrace(() => expired++);
    grace.disconnected(const Duration(milliseconds: 40));
    grace.disconnected(const Duration(seconds: 5));
    expect(grace.waiting, isTrue);
    await Future<void>.delayed(const Duration(milliseconds: 100));
    expect(expired, 1);
    expect(grace.waiting, isFalse);
    grace.dispose();
  });

  test('recovered connection and ended call cancel the timeout', () async {
    var expired = 0;
    final grace = LanDisconnectGrace(() => expired++);
    grace.disconnected(const Duration(milliseconds: 30));
    grace.connected();
    await Future<void>.delayed(const Duration(milliseconds: 70));
    expect(expired, 0);
    grace.disconnected(const Duration(milliseconds: 30));
    grace.dispose();
    await Future<void>.delayed(const Duration(milliseconds: 70));
    expect(expired, 0);
  });
}
