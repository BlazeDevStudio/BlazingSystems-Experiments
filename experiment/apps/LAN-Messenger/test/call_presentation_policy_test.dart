import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/call_presentation_policy.dart';

void main() {
  test('Answer must not open native video during WebRTC media setup', () {
    expect(CallPresentationPolicy.ready(
      incomingPending: true, connecting: true, peerPresent: true,
      alreadyShown: false, scheduled: false), isFalse);
    expect(CallPresentationPolicy.ready(
      incomingPending: false, connecting: true, peerPresent: true,
      alreadyShown: false, scheduled: false), isFalse);
    expect(CallPresentationPolicy.ready(
      incomingPending: false, connecting: false, peerPresent: true,
      alreadyShown: false, scheduled: false), isTrue);
    expect(CallPresentationPolicy.ready(
      incomingPending: false, connecting: false, peerPresent: true,
      alreadyShown: false, scheduled: true), isFalse);
    expect(CallPresentationPolicy.ready(
      incomingPending: false, connecting: false, peerPresent: false,
      alreadyShown: false, scheduled: false), isFalse);
  });

  test('Windows native incoming toast only while hidden or minimized', () {
    expect(CallPresentationPolicy.externalIncoming(
      foreground: true, minimizedOrHidden: false, android: false), isFalse);
    expect(CallPresentationPolicy.externalIncoming(
      foreground: false, minimizedOrHidden: true, android: false), isTrue);
  });

  test('Android floating Answer/Decline only outside foreground app', () {
    expect(CallPresentationPolicy.externalIncoming(
      foreground: true, minimizedOrHidden: false, android: true), isFalse);
    expect(CallPresentationPolicy.externalIncoming(
      foreground: false, minimizedOrHidden: false, android: true), isTrue);
  });
}
