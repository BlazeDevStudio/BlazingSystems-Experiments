/// Pure, cross-platform guard for call-window activation.
///
/// UI callbacks may fire before microphone/camera creation and WebRTC SDP.
/// The native compact video window must never be shown during that interval.
class CallPresentationPolicy {
  static bool ready({
    required bool incomingPending,
    required bool connecting,
    required bool peerPresent,
    required bool alreadyShown,
    required bool scheduled,
  }) => !incomingPending && !connecting && peerPresent &&
      !alreadyShown && !scheduled;

  static bool externalIncoming({
    required bool foreground,
    required bool minimizedOrHidden,
    required bool android,
  }) => android ? !foreground : minimizedOrHidden;
}
