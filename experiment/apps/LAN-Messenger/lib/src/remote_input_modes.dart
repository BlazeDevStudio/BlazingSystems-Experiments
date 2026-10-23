import 'dart:math' as math;
import 'package:flutter/material.dart';

/// The four control presentations documented by Chrome Remote Desktop:
/// virtual trackpad, direct touch, and two-/three-finger local pan/zoom.
/// Remote mouse injection is a separate, explicitly approved capability.
enum RemoteInputMode { trackpad, direct, panTwo, panThree }

extension RemoteInputModeLabel on RemoteInputMode {
  String get label => switch (this) {
    RemoteInputMode.trackpad => 'Trackpad',
    RemoteInputMode.direct => 'Direct touch',
    RemoteInputMode.panTwo => '2-finger pan',
    RemoteInputMode.panThree => '3-finger pan',
  };
}

enum RemoteMouseButton { left, right, middle }

/// Takes touch/mouse input on top of a letterboxed video and maps taps to
/// the *actual frame* after local pan and zoom. Padding is not interactive.
@visibleForTesting
Offset? normalizedVideoPoint(Offset location, Size viewport,
    double sourceRatio, double zoom, Offset pan) {
  if (viewport.width <= 0 || viewport.height <= 0 ||
      !sourceRatio.isFinite || sourceRatio <= 0 || zoom <= 0) return null;
  final boxRatio = viewport.width / viewport.height;
  final videoWidth = boxRatio > sourceRatio
      ? viewport.height * sourceRatio : viewport.width;
  final videoHeight = boxRatio > sourceRatio
      ? viewport.height : viewport.width / sourceRatio;
  final relative = (location - Offset(viewport.width / 2, viewport.height / 2)
      - pan) / zoom;
  final x = (relative.dx + videoWidth / 2) / videoWidth;
  final y = (relative.dy + videoHeight / 2) / videoHeight;
  if (x < 0 || y < 0 || x > 1 || y > 1) return null;
  return Offset(x, y);
}

class RemoteInputOverlay extends StatefulWidget {
  const RemoteInputOverlay({
    super.key,
    required this.video,
    required this.sourceRatio,
    required this.mode,
    required this.onClick,
    required this.onMove,
    required this.onScroll,
  });
  final Widget video;
  final double sourceRatio;
  final RemoteInputMode mode;
  final void Function(Offset normalized, RemoteMouseButton button) onClick;
  final void Function(Offset relative) onMove;
  final void Function(double wheelSteps) onScroll;

  @override
  State<RemoteInputOverlay> createState() => _RemoteInputOverlayState();
}

class _RemoteInputOverlayState extends State<RemoteInputOverlay> {
  final Map<int, Offset> _points = {};
  Offset _pan = Offset.zero;
  double _zoom = 1;
  int _contacts = 0;
  bool _gesture = false;
  Offset _down = Offset.zero;
  DateTime? _pressedAt;
  DateTime _lastMove = DateTime.fromMillisecondsSinceEpoch(0);
  double _oldRadius = 0;
  Offset _oldCentroid = Offset.zero;
  Size _size = Size.zero;

  int get _requiredPanFingers => widget.mode == RemoteInputMode.panThree ? 3 : 2;

  Offset get _centroid => _points.values.fold(Offset.zero,
      (Offset total, Offset point) => total + point) / math.max(1, _points.length).toDouble();

  double get _radius {
    final center = _centroid;
    return _points.values.fold<double>(0,
        (total, p) => total + (p - center).distance) /
        math.max(1, _points.length);
  }

  void _downPointer(PointerDownEvent event) {
    _points[event.pointer] = event.localPosition;
    _contacts = math.max(_contacts, _points.length);
    if (_points.length == 1) {
      _down = event.localPosition;
      _pressedAt = DateTime.now();
      _gesture = false;
    }
    _oldCentroid = _centroid;
    _oldRadius = _radius;
  }

  void _movePointer(PointerMoveEvent event) {
    if (!_points.containsKey(event.pointer)) return;
    final old = _points[event.pointer]!;
    _points[event.pointer] = event.localPosition;
    final count = _points.length;
    final delta = event.localPosition - old;
    final now = DateTime.now();

    if (widget.mode == RemoteInputMode.trackpad) {
      if (count == 1 && now.difference(_lastMove).inMilliseconds >= 30) {
        widget.onMove(Offset(delta.dx / _size.width,
            delta.dy / _size.height));
        _lastMove = now;
      } else if (count == 2 &&
          now.difference(_lastMove).inMilliseconds >= 55) {
        widget.onScroll(-delta.dy / 28);
        _lastMove = now;
      }
    } else if ((widget.mode == RemoteInputMode.panTwo ||
        widget.mode == RemoteInputMode.panThree) &&
        count >= _requiredPanFingers) {
      final center = _centroid;
      final radius = _radius;
      setState(() {
        _pan += center - _oldCentroid;
        if (_oldRadius > 4 && radius > 4) {
          _zoom = (_zoom * radius / _oldRadius).clamp(1.0, 4.0);
        }
        final limitX = (_size.width * (_zoom - 1) / 2);
        final limitY = (_size.height * (_zoom - 1) / 2);
        _pan = Offset(_pan.dx.clamp(-limitX, limitX),
            _pan.dy.clamp(-limitY, limitY));
      });
      _gesture = true;
    }
    if (delta.distance > 12 || (count == 1 &&
        (event.localPosition - _down).distance > 12)) {
      _gesture = true;
    }
    if (widget.mode == RemoteInputMode.trackpad &&
        count == 2 && delta.distance > 4) _gesture = true;
    _oldCentroid = _centroid;
    _oldRadius = _radius;
  }

  void _upPointer(PointerEvent event) {
    if (!_points.containsKey(event.pointer)) return;
    final up = _points[event.pointer]!;
    _points.remove(event.pointer);
    if (_points.isNotEmpty) return;
    final duration = DateTime.now().difference(
        _pressedAt ?? DateTime.now()).inMilliseconds;
    if (!_gesture && duration < 350 &&
        (_contacts > 1 || (up - _down).distance < 14)) {
      final point = widget.mode == RemoteInputMode.trackpad
          ? const Offset(0.5, 0.5)
          : normalizedVideoPoint(up, _size, widget.sourceRatio, _zoom, _pan);
      if (point != null) {
        final button = _contacts >= 3 ? RemoteMouseButton.middle :
            _contacts == 2 ? RemoteMouseButton.right :
            RemoteMouseButton.left;
        widget.onClick(point, button);
      }
    }
    _contacts = 0;
    _gesture = false;
    _oldRadius = 0;
  }

  @override
  Widget build(BuildContext context) => LayoutBuilder(builder: (context, box) {
    _size = Size(box.maxWidth, box.maxHeight);
    return Listener(
      behavior: HitTestBehavior.opaque,
      onPointerDown: _downPointer,
      onPointerMove: _movePointer,
      onPointerUp: _upPointer,
      onPointerCancel: (event) {
        _gesture = true;
        _upPointer(event);
      },
      child: ClipRect(child: Transform.translate(
        offset: _pan,
        child: Transform.scale(scale: _zoom,
          child: widget.video),
      )),
    );
  });
}
