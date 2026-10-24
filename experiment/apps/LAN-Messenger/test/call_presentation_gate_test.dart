import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/call_presentation_gate.dart';

void main() {
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
}
