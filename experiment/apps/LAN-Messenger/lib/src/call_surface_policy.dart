/// Deterministic call presentation policy; background notifications are
/// deliberately separate from the full-screen foreground incoming call view.
enum IncomingSurface { foregroundCall, windowsToast, androidCallStyle }

class CallSurfacePolicy {
  static IncomingSurface incoming({required bool background,
      required bool android}) {
    if (!background) return IncomingSurface.foregroundCall;
    return android ? IncomingSurface.androidCallStyle :
        IncomingSurface.windowsToast;
  }

  /// Never open an ongoing call window while the caller is still negotiating
  /// media. It used to run in a finally block before getUserMedia(), which
  /// caused a race between the Win32 window and WebRTC video initialization.
  static bool mayPresentOngoing({
    required bool incomingPending,
    required bool connecting,
    required bool hasPeer,
    required bool alreadyPresent,
    required bool presenting,
  }) => !incomingPending && !connecting && hasPeer &&
      !alreadyPresent && !presenting;
}
