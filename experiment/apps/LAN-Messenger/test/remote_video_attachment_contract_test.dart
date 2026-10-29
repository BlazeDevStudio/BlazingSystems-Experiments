import 'dart:async';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/serial_async_gate.dart';

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
  test('streamless track attachments serialize with native call teardown', () {
    final source = File('lib/src/intercom.dart').readAsStringSync();
    final trackStart = source.indexOf('pc.onTrack = (event) {');
    final trackEnd = source.indexOf('pc.onConnectionState =', trackStart);
    final block = source.substring(trackStart, trackEnd);
    expect(block, matches(RegExp(r'unawaited\(\s*_remoteVideoTrackGate\.run<void>\(\(\) async \{')));
    expect(block, contains('track.id == event.track.id'));
    // The fallback must be freed after a failed initial native addTrack,
    // but never while bound to the live renderer.
    expect(block, contains('MediaStream? createdFallback;'));
    expect(block, contains('if (!rendererAttached && abandoned != null &&'));
    expect(block, contains('await abandoned.dispose();'));
    expect(block, contains('if (callId != id || _closing || _remoteHasNativeStream) return;'));

    final shutdownStart = source.indexOf('Future<void> _hangUpOnce(');
    final shutdown = source.substring(shutdownStart);
    final drain = shutdown.indexOf('await _remoteVideoTrackGate.run<void>(() async {});');
    final peerClose = shutdown.indexOf('await pc.close()');
    final fallback = shutdown.indexOf('final fallback = _remoteFallbackStream;');
    expect(drain, greaterThanOrEqualTo(0));
    expect(peerClose, greaterThan(drain));
    expect(fallback, greaterThan(drain));
  });

  test('queued track events cannot run while earlier native attach is pending', () async {
    final gate = SerialAsyncGate();
    final firstNativeAttach = Completer<void>();
    final sequence = <String>[];
    final first = gate.run<void>(() async {
      sequence.add('attach-start');
      await firstNativeAttach.future;
      sequence.add('attach-end');
    });
    final second = gate.run<void>(() async {
      sequence.add('teardown');
    });
    await Future<void>.delayed(Duration.zero);
    expect(sequence, ['attach-start']);
    firstNativeAttach.complete();
    await Future.wait<void>([first, second]);
    expect(sequence, ['attach-start', 'attach-end', 'teardown']);
  });

}
