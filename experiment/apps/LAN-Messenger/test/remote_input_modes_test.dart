import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/remote_input_modes.dart';

void main() {
  test('four distinct local input modes have readable labels', () {
    expect(RemoteInputMode.values.length, 4);
    expect(RemoteInputMode.values.map((m) => m.label).toSet().length, 4);
  });

  test('letterbox margins are ignored for pointer mapping', () {
    // 16:9 content inside a tall phone screen: large top/bottom margins.
    const view = Size(400, 800);
    expect(normalizedVideoPoint(const Offset(200, 400), view,
        16 / 9, 1, Offset.zero), const Offset(0.5, 0.5));
    expect(normalizedVideoPoint(const Offset(200, 40), view,
        16 / 9, 1, Offset.zero), isNull);
  });

  test('2x pan and zoom mapping accounts for transformed frame', () {
    const view = Size(400, 300);
    final center = normalizedVideoPoint(const Offset(200, 150),
        view, 4 / 3, 2.0, const Offset(80, 0));
    expect(center, isNotNull);
    expect(center!.dx, closeTo(0.4, 0.0001));
    expect(center.dy, closeTo(0.5, 0.0001));
  });

  test('invalid video dimensions do not generate remote clicks', () {
    expect(normalizedVideoPoint(Offset.zero, Size.zero,
        16 / 9, 1, Offset.zero), isNull);
    expect(normalizedVideoPoint(Offset.zero, const Size(10, 10),
        0, 1, Offset.zero), isNull);
  });
}
