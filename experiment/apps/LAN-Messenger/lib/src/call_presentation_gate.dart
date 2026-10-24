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
