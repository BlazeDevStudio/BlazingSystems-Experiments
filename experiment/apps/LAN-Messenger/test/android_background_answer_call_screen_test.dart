import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Android native Answer restores full call after ringing minimization', () {
    final source = File('lib/main.dart').readAsStringSync();
    final begin = source.indexOf('inter.onIncoming = (peer, incomingVideo) async {');
    final end = source.indexOf('await n.start();', begin);
    expect(begin, greaterThanOrEqualTo(0));
    expect(end, greaterThan(begin));
    final incoming = source.substring(begin, end);
    // Background ring stays unobtrusive; consent must still be explicit.
    expect(incoming, contains('_callMinimized = _incomingUsesExternalSurface;'));
    expect(incoming, contains('accepted = await answer.future.timeout('));
    // Resume can run while _incomingDialogOpen is still true. Therefore
    // acceptance itself must restore the expanded call and never change
    // the UI for rejected, stale, or different sessions.
    final finalized = incoming.substring(incoming.indexOf('} finally {'));
    expect(finalized, contains('_incomingDialogOpen = false;'));
    // dart format may wrap this boolean guard across any number of lines.
    // Check the entire token sequence, including explicit session and OS
    // conditions, instead of assuming a particular whitespace layout.
    expect(
      RegExp(
        r'if\s*\(\s*accepted\s*&&\s*id\s*==\s*inter\.callId\s*&&'
        r'\s*inter\.talkingTo\?\.id\s*==\s*peer\.id\s*&&'
        r'\s*Platform\.isAndroid\s*\)',
      ).hasMatch(finalized),
      isTrue,
    );
    expect(finalized, contains('_callMinimized = false;'));
    expect(finalized, contains('selected = peer;'));
  });
}
