import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/remote_control_surface.dart';

void main() {
  test('four independent input modes have discoverable labels', () {
    expect(ControlInputMode.values.length, 4);
    expect(ControlInputMode.trackpad.title, 'Trackpad');
    expect(ControlInputMode.directTouch.title, 'Direct touch');
    expect(ControlInputMode.twoFingerPanZoom.title, '2-finger pan & zoom');
    expect(ControlInputMode.threeFingerPanZoom.title, '3-finger pan & zoom');
  });

  test('maps letterboxed desktop without clicking the margins', () {
    const view = Size(400, 400);
    const ratio = 16 / 9;
    expect(RemoteControlSurface.normalizedPoint(
        const Offset(200, 200), view, ratio), const Offset(0.5, 0.5));
    expect(RemoteControlSurface.normalizedPoint(
        const Offset(200, 0), view, ratio), isNull);
    expect(RemoteControlSurface.normalizedPoint(
        const Offset(0, 200), view, ratio), const Offset(0, 0.5));
  });

  testWidgets('direct-touch tap maps correctly to shared desktop', (tester) async {
    final calls = <String>[];
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: Center(
      child: SizedBox(width: 200, height: 200,
        child: RemoteControlSurface(
          mode: ControlInputMode.directTouch,
          enabled: true,
          sourceRatio: 1,
          onInput: (action, x, y, wheel) {
            calls.add('$action:${x.toStringAsFixed(2)}:${y.toStringAsFixed(2)}');
          },
          child: const ColoredBox(color: Colors.black),
        )),
    ))));
    await tester.tapAt(tester.getCenter(find.byType(RemoteControlSurface)));
    await tester.pump();
    expect(calls, contains('click:0.50:0.50'));
  });

  testWidgets('disabled remote-control surface never sends clicks', (tester) async {
    final calls = <String>[];
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: Center(
      child: SizedBox(width: 200, height: 200,
        child: RemoteControlSurface(
          mode: ControlInputMode.trackpad,
          enabled: false,
          sourceRatio: 1,
          onInput: (action, x, y, wheel) => calls.add(action),
          child: const ColoredBox(color: Colors.black),
        )),
    ))));
    await tester.tapAt(tester.getCenter(find.byType(RemoteControlSurface)));
    await tester.pump();
    expect(calls, isEmpty);
  });

  test('translated and zoomed view maps input back to desktop positions', () {
    const pan = Offset(20, -10);
    expect(RemoteControlSurface.normalizedPoint(
        const Offset(220, 190), const Size(400, 400), 16 / 9,
        scale: 2, pan: pan), const Offset(0.5, 0.5));
    expect(RemoteControlSurface.normalizedPoint(
        const Offset(-300, -300), const Size(400, 400), 16 / 9,
        scale: 2, pan: pan), isNull);
  });
}
