/// External call presentation is not allowed while the incoming offer is
/// still awaiting its answer or the WebRTC peer is negotiating audio/video.
class CallPresentationGate {
  /// Native Answer/Decline controls belong outside the app only while ringing
  /// and the primary Messenger window is not in the foreground.
  static bool externalIncoming({
    required bool appForeground,
    required bool awaitingDecision,
  }) => !appForeground && awaitingDecision;

  static bool ready({
    required bool awaitingDecision,
    required bool connecting,
    required bool validSession,
    required bool alreadyPresented,
    required bool pendingPresentation,
  }) => !awaitingDecision && !connecting && validSession &&
      !alreadyPresented && !pendingPresentation;
}


/// Ignores stale Windows popup reconciliations when native window events
/// complete out of order (minimize, restore, focus, call end).
///
/// A captured epoch is valid only until a newer visibility event or the
/// session's cleanup invalidates it. This does not identify or authenticate
/// callers; session ownership is checked separately by the call controller.
class CallSurfaceEpoch {
  int _current = 0;

  int begin() => ++_current;

  bool isCurrent(int token) => token == _current;

  void invalidate() {
    _current++;
  }
}
