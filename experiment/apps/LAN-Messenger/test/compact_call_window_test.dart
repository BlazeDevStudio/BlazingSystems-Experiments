import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/compact_call_window.dart';

void main() {
  test('incoming popup docks next to bottom-right taskbar work area', () {
    final area = const Rect.fromLTWH(0, 0, 1920, 1040);
    final popup = CompactCallWindow.dockedRect(area, const Size(344, 166));
    expect(popup, const Rect.fromLTWH(1564, 862, 344, 166));
    expect(popup.bottom, lessThan(area.bottom));
  });

  test('docking respects monitors with nonzero or negative origins', () {
    const area = Rect.fromLTWH(-1280, -120, 1280, 980);
    final popup = CompactCallWindow.dockedRect(area, const Size(344, 296));
    expect(popup, const Rect.fromLTWH(-356, 552, 344, 296));
  });

  test('call popups never exceed a narrow work area', () {
    const area = Rect.fromLTWH(10, 20, 300, 180);
    final popup = CompactCallWindow.dockedRect(area, const Size(344, 296));
    expect(area.contains(popup.topLeft), isTrue);
    expect(popup.right, lessThanOrEqualTo(area.right));
    expect(popup.bottom, lessThanOrEqualTo(area.bottom));
  });

  test('desktop compact call state has explicit incoming and two active views', () {
    expect(CompactCallMode.values, containsAll([
      CompactCallMode.normal,
      CompactCallMode.incoming,
      CompactCallMode.activeAudio,
      CompactCallMode.activeVideo,
    ]));
  });
}
