import 'dart:ffi';
import 'dart:io';

/// Owner-approved, active-call-only Windows input. No keyboard or command
/// execution. Coordinate mapping intentionally rejects multi-monitor desktops
/// until a particular selected display can be authenticated and calibrated.
class WindowsRemoteInput {
  static final _user32 = DynamicLibrary.open('user32.dll');
  static final _metric = _user32.lookupFunction<Int32 Function(Int32),
      int Function(int)>('GetSystemMetrics');
  static final _setPos = _user32.lookupFunction<Int32 Function(Int32, Int32),
      int Function(int, int)>('SetCursorPos');
  static final _mouse = _user32.lookupFunction<
      Void Function(Uint32, Uint32, Uint32, Uint32, IntPtr),
      void Function(int, int, int, int, int)>('mouse_event');

  static bool get _singleMonitor =>
      Platform.isWindows && _metric(80) == 1 && _metric(0) > 1 && _metric(1) > 1;

  static void clickNormalized(double x, double y, {String button = 'left'}) {
    if (!_singleMonitor || !x.isFinite || !y.isFinite ||
        x < 0 || x > 1 || y < 0 || y > 1) return;
    if (_setPos((x * (_metric(0) - 1)).round(),
        (y * (_metric(1) - 1)).round()) == 0) return;
    clickPointer(button: button);
  }

  static void clickPointer({String button = 'left'}) {
    if (!_singleMonitor) return;
    final (down, up) = switch (button) {
      'right' => (0x0008, 0x0010),
      'middle' => (0x0020, 0x0040),
      _ => (0x0002, 0x0004),
    };
    _mouse(down, 0, 0, 0, 0);
    _mouse(up, 0, 0, 0, 0);
  }

  static void moveRelative(double dx, double dy) {
    if (!_singleMonitor || !dx.isFinite || !dy.isFinite ||
        dx.abs() > 0.5 || dy.abs() > 0.5) return;
    final px = (dx * _metric(0) * 1.5).round().clamp(-400, 400);
    final py = (dy * _metric(1) * 1.5).round().clamp(-400, 400);
    _mouse(0x0001, px & 0xFFFFFFFF, py & 0xFFFFFFFF, 0, 0);
  }

  static void scroll(double steps) {
    if (!_singleMonitor || !steps.isFinite || steps.abs() > 10) return;
    final ticks = (steps * 120).round().clamp(-360, 360);
    _mouse(0x0800, 0, 0, ticks & 0xFFFFFFFF, 0);
  }
}
