import 'dart:async';
import 'dart:ui';

import 'package:screen_retriever/screen_retriever.dart';
import 'package:window_manager/window_manager.dart' as wm;

/// A single-window Windows call shell. While showing an incoming call or
/// picture-in-picture, the normal Messenger window is replaced with a tiny,
/// inactive, draggable window above the work area. We never focus or raise
/// the original full-size window. All changes are reversible.
enum CompactCallMode { normal, incoming, activeAudio, activeVideo }

class CompactCallWindow {
  CompactCallMode mode = CompactCallMode.normal;
  Rect? _originalBounds;
  bool _wasVisible = false;
  bool _wasMaximized = false;
  Future<void> _serial = Future<void>.value();

  bool get isCompact => mode != CompactCallMode.normal;

  /// Anchor beside the taskbar clock, respecting logical work-area bounds.
  /// Primary-display offsets need not be (0,0), e.g. vertically stacked PCs.
  static Rect dockedRect(Rect workArea, Size preferred, {double margin = 12}) {
    if (workArea.width <= 0 || workArea.height <= 0) {
      return Rect.fromLTWH(0, 0, preferred.width, preferred.height);
    }
    final width = preferred.width.clamp(0.0, workArea.width).toDouble();
    final height = preferred.height.clamp(0.0, workArea.height).toDouble();
    final x = (workArea.right - width - margin)
        .clamp(workArea.left, workArea.right - width).toDouble();
    final y = (workArea.bottom - height - margin)
        .clamp(workArea.top, workArea.bottom - height).toDouble();
    return Rect.fromLTWH(x, y, width, height);
  }

  Future<void> _queue(Future<void> Function() action) {
    final task = _serial.then((_) => action());
    _serial = task.catchError((Object _) {});
    return task;
  }

  Future<void> incoming(void Function() changed) => _queue(() async {
    await wm.windowManager.ensureInitialized();
    if (_originalBounds == null) {
      _originalBounds = await wm.windowManager.getBounds();
      _wasVisible = await wm.windowManager.isVisible();
      _wasMaximized = await wm.windowManager.isMaximized();
    }
    mode = CompactCallMode.incoming;
    changed();
    await _present(const Size(344, 166));
  });

  Future<void> active({required bool video, required void Function() changed}) =>
      _queue(() async {
    if (_originalBounds == null) return;
    mode = video ? CompactCallMode.activeVideo : CompactCallMode.activeAudio;
    changed();
    await _present(video ? const Size(344, 296) : const Size(344, 136));
  });

  Future<void> _present(Size size) async {
    if (await wm.windowManager.isMaximized()) {
      await wm.windowManager.unmaximize();
    }
    final display = await screenRetriever.getPrimaryDisplay();
    final area = Rect.fromLTWH(
      display.visiblePosition?.dx ?? 0,
      display.visiblePosition?.dy ?? 0,
      (display.visibleSize ?? display.size).width,
      (display.visibleSize ?? display.size).height,
    );
    final target = dockedRect(area, size);
    await wm.windowManager.setMinimumSize(const Size(300, 112));
    await wm.windowManager.setResizable(false);
    await wm.windowManager.setTitleBarStyle(wm.TitleBarStyle.hidden);
    await wm.windowManager.setSkipTaskbar(true);
    await wm.windowManager.setAlwaysOnTop(true);
    await wm.windowManager.setBounds(target);
    // Inactive show prevents the compact caller banner taking keyboard focus
    // away from whatever application the user is currently working in.
    await wm.windowManager.show(inactive: true);
  }

  Future<void> restore(void Function() changed, {bool bringToFront = false}) =>
      _queue(() async {
    if (_originalBounds == null) {
      mode = CompactCallMode.normal;
      changed();
      return;
    }
    final original = _originalBounds!;
    final wasVisible = _wasVisible;
    final wasMaximized = _wasMaximized;
    _originalBounds = null;
    mode = CompactCallMode.normal;
    changed();
    // Drop always-on-top *before* changing bounds to avoid flashing a large
    // full-screen window on top of the user's unrelated foreground program.
    await wm.windowManager.setAlwaysOnTop(false);
    await wm.windowManager.setResizable(true);
    await wm.windowManager.setMinimumSize(Size.zero);
    await wm.windowManager.setSkipTaskbar(false);
    await wm.windowManager.setTitleBarStyle(wm.TitleBarStyle.normal);
    await wm.windowManager.setBounds(original);
    if (wasMaximized) await wm.windowManager.maximize();
    if (bringToFront || wasVisible) {
      await wm.windowManager.show(inactive: !bringToFront);
      if (bringToFront) await wm.windowManager.focus();
    } else {
      await wm.windowManager.hide();
    }
  });

  /// Let the user explicitly open the full chat without ending the call.
  Future<void> openThread(void Function() changed) =>
      restore(changed, bringToFront: true);
}
