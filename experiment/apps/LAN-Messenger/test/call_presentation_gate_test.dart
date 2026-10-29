import 'dart:async';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/call_presentation_gate.dart';

void main() {
  test('foreground offer uses the inline Answer/Decline row', () {
    expect(CallPresentationGate.externalIncoming(
        appForeground: true, awaitingDecision: true), isFalse);
  });
  test('external incoming HUD exists only in background while ringing', () {
    expect(CallPresentationGate.externalIncoming(
        appForeground: false, awaitingDecision: true), isTrue);
    expect(CallPresentationGate.externalIncoming(
        appForeground: false, awaitingDecision: false), isFalse);
  });
  test('never opens floating video during an unanswered offer', () {
    expect(CallPresentationGate.ready(awaitingDecision: true,
      connecting: true, validSession: true,
      alreadyPresented: false, pendingPresentation: false), isFalse);
  });
  test('answer cannot create viewer before media connection', () {
    expect(CallPresentationGate.ready(awaitingDecision: false,
      connecting: true, validSession: true,
      alreadyPresented: false, pendingPresentation: false), isFalse);
  });
  test('finished negotiation presents exactly once', () {
    expect(CallPresentationGate.ready(awaitingDecision: false,
      connecting: false, validSession: true,
      alreadyPresented: false, pendingPresentation: false), isTrue);
    expect(CallPresentationGate.ready(awaitingDecision: false,
      connecting: false, validSession: true,
      alreadyPresented: true, pendingPresentation: false), isFalse);
    expect(CallPresentationGate.ready(awaitingDecision: false,
      connecting: false, validSession: true,
      alreadyPresented: false, pendingPresentation: true), isFalse);
  });
  test('ended call never revives controls', () {
    expect(CallPresentationGate.ready(awaitingDecision: false,
      connecting: false, validSession: false,
      alreadyPresented: false, pendingPresentation: false), isFalse);
  });
  test('newer restore response supersedes older delayed minimize popup', () async {
    final epochs = CallSurfaceEpoch();
    final slowWindowQuery = Completer<bool>();
    final displayed = <bool>[];

    Future<void> reconcile(Future<bool> backgroundQuery) async {
      final token = epochs.begin();
      final background = await backgroundQuery;
      if (!epochs.isCurrent(token)) return;
      displayed.add(background); // true: native popup; false: dismiss
    }

    final oldMinimize = reconcile(slowWindowQuery.future);
    await reconcile(Future<bool>.value(false)); // Later window restore
    slowWindowQuery.complete(true); // Stale minimize finally returns.
    await oldMinimize;
    expect(displayed, [false]);
  });

  test('call end invalidates an in-flight native popup reconciliation', () async {
    final epochs = CallSurfaceEpoch();
    final nativeReply = Completer<void>();
    var revived = false;
    final token = epochs.begin();
    final oldPopup = () async {
      await nativeReply.future;
      if (epochs.isCurrent(token)) revived = true;
    }();
    epochs.invalidate(); // Hangup or compact-window transition.
    nativeReply.complete();
    await oldPopup;
    expect(revived, isFalse);
    expect(epochs.isCurrent(epochs.begin()), isTrue);
  });

  test('Windows popup state is epoch-gated across native awaits', () {
    final app = File('lib/main.dart').readAsStringSync();
    final start = app.indexOf('Future<void> _syncDesktopCallSurface() async');
    final end = app.indexOf('void onWindowMinimize()', start);
    expect(start, greaterThanOrEqualTo(0));
    expect(end, greaterThan(start));
    final block = app.substring(start, end);
    expect(block, contains('final epoch = _desktopCallSurfaceEpoch.begin();'));
    expect(block, contains('await _isDesktopBackground()'));
    expect(block, contains('!_desktopCallSurfaceEpoch.isCurrent(epoch)'));
    expect(block, contains('final available = await _showDesktopIncoming('));
    expect(block, contains('desktopEpoch: epoch'));
    expect(app, contains('_desktopCallSurfaceEpoch.invalidate();'));
    expect(app, contains('_windowsVideoTransition'));
  });

}
