import 'dart:ffi';
import 'dart:io';

/// Minimal Windows-only, owner-approved remote mouse action.
/// Never invokes a shell, runs a command, or injects keyboard passwords.
class WindowsRemoteInput {
  static void clickNormalized(double x, double y) {
    if (!Platform.isWindows || !x.isFinite || !y.isFinite ||
        x < 0 || x > 1 || y < 0 || y > 1) return;
    final user32 = DynamicLibrary.open('user32.dll');
    final metric = user32.lookupFunction<Int32 Function(Int32),
        int Function(int)>('GetSystemMetrics');
    final setPos = user32.lookupFunction<Int32 Function(Int32, Int32),
        int Function(int, int)>('SetCursorPos');
    final mouse = user32.lookupFunction<
        Void Function(Uint32, Uint32, Uint32, Uint32, IntPtr),
        void Function(int, int, int, int, int)>('mouse_event');
    // One-monitor prototype: avoid incorrect clicks when multiple desktop
    // monitors or arbitrary captured windows have a different origin.
    if (metric(80) > 1) return; // SM_CMONITORS
    final width = metric(0);
    final height = metric(1);
    if (width < 2 || height < 2) return;
    if (setPos((x * (width - 1)).round(), (y * (height - 1)).round()) == 0) return;
    mouse(0x0002, 0, 0, 0, 0); // Left button down.
    mouse(0x0004, 0, 0, 0, 0); // Left button up.
  }
}
