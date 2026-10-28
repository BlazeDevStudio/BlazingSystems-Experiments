import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('empty native media streams fall back to the real remote video track', () {
    final source = File('lib/src/intercom.dart').readAsStringSync();
    final start = source.indexOf('pc.onTrack = (event) {');
    final end = source.indexOf('pc.onConnectionState =', start);
    expect(start, greaterThanOrEqualTo(0));
    expect(end, greaterThan(start));
    final block = source.substring(start, end);
    expect(block, contains('event.streams.first.getVideoTracks().isNotEmpty'));
    expect(block, contains('await fallback.addTrack(event.track)'));
    expect(block, contains('remoteRenderer?.srcObject = fallback'));
  });

  test('late streamless track events cannot resurrect disposed call video', () {
    final source = File('lib/src/intercom.dart').readAsStringSync();
    final start = source.indexOf('pc.onTrack = (event) {');
    final end = source.indexOf('pc.onConnectionState =', start);
    final block = source.substring(start, end);
    expect(block, contains('final existing = _remoteFallbackStream;'));
    expect(block, contains('if (callId != id || _closing || _remoteHasNativeStream)'));
    expect(block, contains('if (existing == null) await fallback.dispose();'));
    expect(block, contains('identical(_remoteFallbackStream, fallback)'));
    expect(block, contains('_remoteFallbackStream = null;'));
  });
}
