import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:lan_messenger/src/call_transport_gate.dart';

void main() {
  test('SDP/ICE negotiation cannot display Connected before transport', () {
    expect(
      CallTransportGate.mediaReady(
          RTCPeerConnectionState.RTCPeerConnectionStateNew),
      isFalse,
    );
    expect(
      CallTransportGate.mediaReady(
          RTCPeerConnectionState.RTCPeerConnectionStateConnecting),
      isFalse,
    );
  });

  test('only established WebRTC peer transport is media-ready', () {
    expect(
      CallTransportGate.mediaReady(
          RTCPeerConnectionState.RTCPeerConnectionStateConnected),
      isTrue,
    );
    for (final state in [
      RTCPeerConnectionState.RTCPeerConnectionStateDisconnected,
      RTCPeerConnectionState.RTCPeerConnectionStateFailed,
      RTCPeerConnectionState.RTCPeerConnectionStateClosed,
    ]) {
      expect(CallTransportGate.mediaReady(state), isFalse,
          reason: 'Transport in $state must not be announced as connected');
    }
  });
}
