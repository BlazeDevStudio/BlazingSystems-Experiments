import 'package:flutter_webrtc/flutter_webrtc.dart';

/// The presence of an SDP answer does not prove that media can flow.
/// A call is established only after the underlying WebRTC peer transport
/// explicitly reports Connected (ICE/DTLS), not merely after signaling.
class CallTransportGate {
  static bool mediaReady(RTCPeerConnectionState state) =>
      state == RTCPeerConnectionState.RTCPeerConnectionStateConnected;
}
