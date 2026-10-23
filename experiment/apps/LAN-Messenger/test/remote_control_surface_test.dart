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
