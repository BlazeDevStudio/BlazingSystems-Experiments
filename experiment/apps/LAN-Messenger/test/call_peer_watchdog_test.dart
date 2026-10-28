import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/call_peer_watchdog.dart';

void main() {
  test('one temporary lost ping does not declare an abandoned call', () {
    var now = DateTime.utc(2026, 10, 28);
    final check = CallPeerWatchdog(now: () => now);
    expect(check.report(CallProbeResult.unreachable), CallWatchdogChange.none);
    expect(check.suspect, false);
    now = now.add(const Duration(seconds: 5));
    expect(check.report(CallProbeResult.active), CallWatchdogChange.recovered);
    expect(check.firstUnavailableAt, isNull);
  });
  test('repeated failure anchors deadline to first missing reply', () {
    var now = DateTime.utc(2026, 10, 28);
    final check = CallPeerWatchdog(now: () => now);
    check.report(CallProbeResult.unreachable);
    final first = check.firstUnavailableAt;
    now = now.add(const Duration(seconds: 5));
    expect(check.report(CallProbeResult.unreachable), CallWatchdogChange.suspect);
    now = now.add(const Duration(seconds: 70));
    expect(check.report(CallProbeResult.unreachable), CallWatchdogChange.none);
    expect(check.firstUnavailableAt, first);
    expect(check.suspect, true);
  });
  test('two authenticated ended replies terminate but one does not', () {
    final check = CallPeerWatchdog();
    expect(check.report(CallProbeResult.ended), CallWatchdogChange.none);
    expect(check.report(CallProbeResult.active), CallWatchdogChange.recovered);
    expect(check.report(CallProbeResult.ended), CallWatchdogChange.none);
    expect(check.report(CallProbeResult.ended), CallWatchdogChange.ended);
  });
  test('recovered liveness resets loss and late ended counts', () {
    final check = CallPeerWatchdog();
    check.report(CallProbeResult.unreachable);
    check.report(CallProbeResult.unreachable);
    expect(check.report(CallProbeResult.active), CallWatchdogChange.recovered);
    expect(check.suspect, false);
    expect(check.report(CallProbeResult.ended), CallWatchdogChange.none);
    expect(check.report(CallProbeResult.unreachable), CallWatchdogChange.none);
    expect(check.report(CallProbeResult.ended), CallWatchdogChange.none);
  });
}
