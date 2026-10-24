/// External call presentation is not allowed while the incoming offer is
/// still awaiting its answer or the WebRTC peer is negotiating audio/video.
class CallPresentationGate {
  static bool ready({
    required bool awaitingDecision,
    required bool connecting,
    required bool validSession,
    required bool alreadyPresented,
    required bool pendingPresentation,
  }) => !awaitingDecision && !connecting && validSession &&
      !alreadyPresented && !pendingPresentation;
}
