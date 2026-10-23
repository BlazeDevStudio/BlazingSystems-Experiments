import 'dart:ffi';
import 'dart:io';

/// Consent-gated Windows mouse driver for a single shared full desktop.
/// No shell execution, keyboard injection, passwords or unattended control.
/// Multi-monitor/multiple-display coordinate mapping remains unsupported.
class WindowsRemoteInput {
  static bool _pressed = false;
  static final DynamicLibrary _user32 =
      Platform.isWindows ? DynamicLibrary.open('user32.dll') : DynamicLibrary.process();
  static final int Function(int) _metric = _user32.lookupFunction<
      Int32 Function(Int32), int Function(int)>('GetSystemMetrics');
  static final int Function(int, int) _setPos = _user32.lookupFunction<
      Int32 Function(Int32, Int32), int Function(int, int)>('SetCursorPos');
  static final void Function(int, int, int, int, int) _mouse = _user32.lookupFunction<
      Void Function(Uint32, Uint32, Uint32, Uint32, IntPtr),
      void Function(int, int, int, int, int)>('mouse_event');

  static bool _move(double x, double y) {
    if (!Platform.isWindows || !x.isFinite || !y.isFinite ||
        x < 0 || x > 1 || y < 0 || y > 1) return false;
    if (_metric(80) != 1) return false; // only one-monitor capture, for now
    final w = _metric(0), h = _metric(1);
    if (w < 2 || h < 2) return false;
    return _setPos((x * (w - 1)).round(), (y * (h - 1)).round()) != 0;
  }

  static void releaseButtons() {
    if (!Platform.isWindows || !_pressed) return;
    _mouse(0x0004, 0, 0, 0, 0);
    _pressed = false;
  }

  static void clickNormalized(double x, double y) => perform('click', x, y);

  static void perform(String action, double x, double y, [int wheel = 0]) {
    if (!_move(x, y)) {
      if (action == 'up') releaseButtons();
      return;
    }
    switch (action) {
      case 'move':
        break;
      case 'down':
        if (!_pressed) {
          _mouse(0x0002, 0, 0, 0, 0);
          _pressed = true;
        }
        break;
      case 'up':
        releaseButtons();
        break;
      case 'click':
        releaseButtons();
        _mouse(0x0002, 0, 0, 0, 0);
        _mouse(0x0004, 0, 0, 0, 0);
        break;
      case 'right':
        releaseButtons();
        _mouse(0x0008, 0, 0, 0, 0);
        _mouse(0x0010, 0, 0, 0, 0);
        break;
      case 'middle':
        releaseButtons();
        _mouse(0x0020, 0, 0, 0, 0);
        _mouse(0x0040, 0, 0, 0, 0);
        break;
      case 'scroll':
        if (wheel != 0) _mouse(0x0800, 0, 0, wheel & 0xffffffff, 0);
        break;
    }
  }
}
