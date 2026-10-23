import 'dart:math' as math;
import 'package:flutter/material.dart';

/// Input policies matching the four Chrome Remote Desktop Windows modes.
/// Direct touch falls back to mouse injection on current Windows hosts.
enum ControlInputMode { trackpad, directTouch, twoFingerPanZoom, threeFingerPanZoom }

extension ControlInputModeDescription on ControlInputMode {
  String get title => switch (this) {
    ControlInputMode.trackpad => 'Trackpad',
    ControlInputMode.directTouch => 'Direct touch',
    ControlInputMode.twoFingerPanZoom => '2-finger pan & zoom',
    ControlInputMode.threeFingerPanZoom => '3-finger pan & zoom',
  };
  String get hint => switch (this) {
    ControlInputMode.trackpad => 'Swipe to move pointer; tap to click; pinch to zoom or two-finger scroll/right-click',
    ControlInputMode.directTouch => 'Tap or drag at the corresponding desktop position',
    ControlInputMode.twoFingerPanZoom => 'One finger controls the PC; two fingers pan and zoom locally',
    ControlInputMode.threeFingerPanZoom => 'One finger controls the PC; two fingers scroll/right-click; three fingers pan and zoom',
  };
}

typedef RemoteInputSender = void Function(String action, double x, double y, int wheel);

/// The surface receives raw touch events so a second/third finger can
/// switch from remote interaction to local pan/zoom without accidental taps.
class RemoteControlSurface extends StatefulWidget {
  const RemoteControlSurface({
    super.key, required this.child, required this.mode,
    required this.enabled, required this.sourceRatio, required this.onInput,
  });
  final Widget child;
  final ControlInputMode mode;
  final bool enabled;
  final double sourceRatio;
  final RemoteInputSender onInput;

  /// Returns null for video letterbox margins; does not click hidden areas.
  static Offset? normalizedPoint(Offset local, Size view, double ratio,
      {double scale = 1, Offset pan = Offset.zero}) {
    if (view.width <= 0 || view.height <= 0 || ratio <= 0 || scale <= 0) return null;
    final width = math.min(view.width, view.height * ratio);
    final height = width / ratio;
    final center = Offset(view.width / 2, view.height / 2) + pan;
    final left = center.dx - width * scale / 2;
    final top = center.dy - height * scale / 2;
    final x = (local.dx - left) / (width * scale);
    final y = (local.dy - top) / (height * scale);
    if (x < 0 || x > 1 || y < 0 || y > 1) return null;
    return Offset(x, y);
  }

  @override
  State<RemoteControlSurface> createState() => _RemoteControlSurfaceState();
}

class _RemoteControlSurfaceState extends State<RemoteControlSurface> {
  final Map<int, Offset> _points = {};
  Offset _cursor = const Offset(0.5, 0.5);
  Offset _pan = Offset.zero;
  double _zoom = 1;
  bool _dragging = false;
  bool _moved = false;
  bool _localGesture = false;
  bool _pinching = false;
  double? _pinchStartSpread;
  Offset? _firstDown;
  DateTime? _firstDownAt;
  Offset? _previousCenter;
  double? _previousSpread;
  DateTime? _lastMove;
  Size _viewport = Size.zero;

  int get _localFingers => switch (widget.mode) {
    ControlInputMode.twoFingerPanZoom => 2,
    ControlInputMode.threeFingerPanZoom => 3,
    _ => 99,
  };
  bool get _trackpad => widget.mode == ControlInputMode.trackpad;

  void _send(String action, [int wheel = 0]) {
    if (!widget.enabled) return;
    widget.onInput(action, _cursor.dx, _cursor.dy, wheel);
  }
  Offset _center() => Offset(
    _points.values.map((p) => p.dx).reduce((a, b) => a + b) / _points.length,
    _points.values.map((p) => p.dy).reduce((a, b) => a + b) / _points.length,
  );
  double _spread(Offset center) {
    if (_points.length < 2) return 0;
    return _points.values
        .map((p) => (p - center).distance).reduce((a, b) => a + b) / _points.length;
  }
  void _releaseDrag() {
    if (_dragging) {
      _send('up');
      _dragging = false;
    }
  }
  void _onDown(PointerDownEvent e) {
    if (!widget.enabled) return;
    _points[e.pointer] = e.localPosition;
    if (_points.length == 1) {
      _firstDown = e.localPosition;
      _firstDownAt = DateTime.now();
      _moved = false;
      _localGesture = false;
      _pinching = false;
      _pinchStartSpread = null;
      if (!_trackpad) {
        final p = RemoteControlSurface.normalizedPoint(
            e.localPosition, _viewport, widget.sourceRatio,
            scale: _zoom, pan: _pan);
        if (p != null) _cursor = p;
      }
    } else {
      // Entering multitouch cancels a mouse drag, never leaves the button down.
      _releaseDrag();
      if (_points.length >= _localFingers) _localGesture = true;
    }
    final c = _center();
    _previousCenter = c;
    _previousSpread = _spread(c);
    if (_points.length == 2) _pinchStartSpread = _previousSpread;
    setState(() {});
  }
  void _onMove(PointerMoveEvent e) {
    if (!widget.enabled || !_points.containsKey(e.pointer)) return;
    final previous = _points[e.pointer]!;
    _points[e.pointer] = e.localPosition;
    if (_points.length >= _localFingers) {
      _localGesture = true;
      _releaseDrag();
      final center = _center();
      final spread = _spread(center);
      setState(() {
        if (_previousCenter != null) _pan += center - _previousCenter!;
        if (_previousSpread != null && _previousSpread! > 3 && spread > 3) {
          _zoom = (_zoom * spread / _previousSpread!).clamp(1.0, 4.0).toDouble();
        }
        _pan = Offset(
          _pan.dx.clamp(-_viewport.width * 1.5, _viewport.width * 1.5).toDouble(),
          _pan.dy.clamp(-_viewport.height * 1.5, _viewport.height * 1.5).toDouble(),
        );
      });
      _previousCenter = center;
      _previousSpread = spread;
      return;
    }
    if (_points.length == 2) {
      // In trackpad mode, a divergent two-finger gesture scales the local
      // desktop preview, while parallel movement scrolls on the host.
      // The initial threshold prevents small touch jitter from zooming.
      final center = _center();
      final spread = _spread(center);
      if (_trackpad && _pinchStartSpread != null &&
          _pinchStartSpread! > 3 && spread > 3) {
        if ((spread - _pinchStartSpread!).abs() > 8) _pinching = true;
        if (_pinching && _previousSpread != null &&
            _previousSpread! > 3) {
          setState(() {
            _zoom = (_zoom * spread / _previousSpread!)
                .clamp(1.0, 4.0).toDouble();
          });
        }
      }
      if (!_pinching) {
        final dy = e.localPosition.dy - previous.dy;
        if (dy.abs() >= 1) {
          _send('scroll', (-dy * 12).round().clamp(-120, 120).toInt());
        }
      }
      _previousCenter = center;
      _previousSpread = spread;
      _moved = true;
      return;
    }
    if (_points.length != 1 || _localGesture) return;
    final initial = _firstDown ?? e.localPosition;
    if ((e.localPosition - initial).distance > 9) _moved = true;
    if (_trackpad) {
      final next = Offset(
        (_cursor.dx + (e.localPosition.dx - previous.dx) / math.max(1, _viewport.width)).clamp(0.0, 1.0).toDouble(),
        (_cursor.dy + (e.localPosition.dy - previous.dy) / math.max(1, _viewport.height)).clamp(0.0, 1.0).toDouble());
      _cursor = next;
      final holding = _firstDownAt != null &&
          DateTime.now().difference(_firstDownAt!) > const Duration(milliseconds: 450);
      if (holding && _moved && !_dragging) {
        _send('down');
        _dragging = true;
      }
    } else {
      final mapped = RemoteControlSurface.normalizedPoint(
          e.localPosition, _viewport, widget.sourceRatio,
          scale: _zoom, pan: _pan);
      if (mapped == null) return;
      _cursor = mapped;
      if (_moved && !_dragging) {
        _send('down');
        _dragging = true;
      }
    }
    final now = DateTime.now();
    if (_lastMove == null || now.difference(_lastMove!) >= const Duration(milliseconds: 35)) {
      _send('move');
      _lastMove = now;
    }
    setState(() {});
  }
  void _onUp(PointerEvent e) {
    if (!_points.containsKey(e.pointer)) return;
    final count = _points.length;
    final tap = _firstDownAt != null &&
        DateTime.now().difference(_firstDownAt!) < const Duration(milliseconds: 380);
    if (count == 1) {
      if (_dragging) _releaseDrag();
      else if (!_moved && !_localGesture && tap) {
        if (!_trackpad) {
          final mapped = RemoteControlSurface.normalizedPoint(
              e.localPosition, _viewport, widget.sourceRatio,
              scale: _zoom, pan: _pan);
          if (mapped != null) _cursor = mapped;
          else { _points.clear(); setState(() {}); return; }
        }
        _send('click');
      }
    } else if (!_localGesture && !_moved && tap) {
      if (count == 2) _send('right');
      if (count >= 3) _send('middle');
      _moved = true;
    }
    _points.remove(e.pointer);
    if (_points.isEmpty) {
      _releaseDrag();
      _firstDown = null;
      _firstDownAt = null;
      _previousCenter = null;
      _previousSpread = null;
      _localGesture = false;
      _pinching = false;
      _pinchStartSpread = null;
    } else {
      final c = _center();
      _previousCenter = c;
      _previousSpread = _spread(c);
      // Remaining fingers after a multitouch gesture never start a new click.
      _localGesture = true;
    }
    setState(() {});
  }
  @override
  void didUpdateWidget(covariant RemoteControlSurface oldWidget) {
    super.didUpdateWidget(oldWidget);
    if ((oldWidget.enabled && !widget.enabled) || oldWidget.mode != widget.mode) {
      _releaseDrag();
      _points.clear();
      _localGesture = false;
      _pinching = false;
      _pinchStartSpread = null;
      _pan = Offset.zero;
      _zoom = 1;
    }
  }
  @override
  void dispose() {
    _releaseDrag();
    super.dispose();
  }
  @override
  Widget build(BuildContext context) => LayoutBuilder(builder: (context, box) {
    _viewport = Size(box.maxWidth, box.maxHeight);
    return ClipRect(child: Listener(
      behavior: HitTestBehavior.opaque,
      onPointerDown: widget.enabled ? _onDown : null,
      onPointerMove: widget.enabled ? _onMove : null,
      onPointerUp: widget.enabled ? _onUp : null,
      onPointerCancel: widget.enabled ? (event) {
        _moved = true;
        _localGesture = true;
        _onUp(event);
      } : null,
      child: Stack(children: [
        Positioned.fill(child: Transform.translate(
          offset: _pan,
          child: Transform.scale(scale: _zoom, child: widget.child))),
        if (widget.enabled && _trackpad)
          Positioned(
            left: (_cursor.dx * box.maxWidth - 9).clamp(0.0, math.max(0.0, box.maxWidth - 18)).toDouble(),
            top: (_cursor.dy * box.maxHeight - 9).clamp(0.0, math.max(0.0, box.maxHeight - 18)).toDouble(),
            child: IgnorePointer(child: Container(
              width: 18, height: 18,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.white, width: 2),
                color: Colors.blueAccent.withValues(alpha: 0.65),
                shape: BoxShape.circle))),
          ),
      ]),
    ));
  });
}
