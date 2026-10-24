import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/call_surface_policy.dart';

void main() {
  test('foreground incoming call never shows a floating native toast', () {
    for (final android in [false, true]) {
      expect(CallSurfacePolicy.incoming(background: false, android: android),
          IncomingSurface.foregroundCall);
    }
  });

  test('minimized PC receives Win32 toast; background Android CallStyle', () {
    expect(CallSurfacePolicy.incoming(background: true, android: false),
        IncomingSurface.windowsToast);
    expect(CallSurfacePolicy.incoming(background: true, android: true),
        IncomingSurface.androidCallStyle);
  });

  test('answered call cannot present external video before negotiation', () {
    expect(CallSurfacePolicy.mayPresentOngoing(
        incomingPending: true, connecting: true, hasPeer: true,
        alreadyPresent: false, presenting: false), isFalse);
    expect(CallSurfacePolicy.mayPresentOngoing(
        incomingPending: false, connecting: true, hasPeer: true,
        alreadyPresent: false, presenting: false), isFalse);
    expect(CallSurfacePolicy.mayPresentOngoing(
        incomingPending: false, connecting: false, hasPeer: true,
        alreadyPresent: false, presenting: false), isTrue);
    expect(CallSurfacePolicy.mayPresentOngoing(
        incomingPending: false, connecting: false, hasPeer: true,
        alreadyPresent: true, presenting: false), isFalse);
  });
}
