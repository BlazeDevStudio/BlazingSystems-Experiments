import 'package:flutter/material.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';

/// Messenger-style call surfaces shared by desktop toast and Android overlay.
/// Rendering never grants a call; accept/decline are explicit callbacks.
class CompactCallCard extends StatelessWidget {
  const CompactCallCard({
    super.key,
    required this.peerName,
    required this.video,
    required this.incoming,
    required this.connecting,
    required this.muted,
    this.renderer,
    required this.onAnswer,
    required this.onDecline,
    required this.onMute,
    required this.onEnd,
    required this.onOpenThread,
    this.onExpand,
    this.onDragStart,
    this.onDragUpdate,
  });
  final String peerName;
  final bool video, incoming, connecting, muted;
  final RTCVideoRenderer? renderer;
  final VoidCallback onAnswer, onDecline, onMute, onEnd, onOpenThread;
  final VoidCallback? onExpand;
  final GestureDragStartCallback? onDragStart;
  final GestureDragUpdateCallback? onDragUpdate;

  @override
  Widget build(BuildContext context) {
    const white = Colors.white;
    return Material(
      color: const Color(0xff10233e),
      elevation: 12,
      clipBehavior: Clip.antiAlias,
      borderRadius: BorderRadius.circular(18),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        GestureDetector(
          behavior: HitTestBehavior.opaque,
          onPanStart: onDragStart,
          onPanUpdate: onDragUpdate,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(12, 10, 8, 8),
            child: Row(children: [
              CircleAvatar(
                radius: 18,
                backgroundColor: const Color(0xff2777c7),
                child: Icon(video ? Icons.videocam_rounded : Icons.call_rounded,
                    color: white, size: 19),
              ),
              const SizedBox(width: 10),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(peerName, style: const TextStyle(color: white, fontSize: 15,
                      fontWeight: FontWeight.bold), maxLines: 1,
                      overflow: TextOverflow.ellipsis),
                  Text(incoming
                      ? (video ? 'Incoming video call' : 'Incoming voice call')
                      : connecting ? 'Connecting call…'
                      : (video ? 'Video call in progress' : 'Voice call in progress'),
                    style: const TextStyle(color: Colors.white70, fontSize: 11)),
                ])),
              const Icon(Icons.drag_indicator_rounded, color: Colors.white54),
            ]),
          ),
        ),
        if (!incoming && video)
          Container(
            color: const Color(0xff071321),
            constraints: const BoxConstraints(maxHeight: 175, minHeight: 135),
            child: AspectRatio(
              aspectRatio: 16 / 9,
              child: renderer != null
                  ? RTCVideoView(renderer!,
                      objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitContain)
                  : const Center(child: Icon(Icons.videocam_off,
                      color: Colors.white54, size: 48)),
            ),
          ),
        const SizedBox(height: 8),
        if (incoming)
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 1, 12, 13),
            child: Row(children: [
              Expanded(child: OutlinedButton.icon(
                key: const Key('decline-call'),
                onPressed: onDecline,
                icon: const Icon(Icons.call_end, color: Colors.white),
                label: const Text('Decline', style: TextStyle(color: white)),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: Color(0xffe86c70)),
                  backgroundColor: const Color(0xffa72b34),
                  padding: const EdgeInsets.symmetric(vertical: 12)),
              )),
              const SizedBox(width: 9),
              Expanded(child: FilledButton.icon(
                key: const Key('answer-call'),
                onPressed: onAnswer,
                icon: const Icon(Icons.call),
                label: const Text('Answer'),
                style: FilledButton.styleFrom(
                  backgroundColor: const Color(0xff1b995b),
                  padding: const EdgeInsets.symmetric(vertical: 12)),
              )),
            ]),
          )
        else
          Padding(
            padding: const EdgeInsets.fromLTRB(8, 0, 8, 12),
            child: Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _action(
                  key: const Key('mute-call'),
                  icon: muted ? Icons.mic_off : Icons.mic,
                  title: muted ? 'Unmute' : 'Mute',
                  onPressed: onMute),
                _action(
                  key: const Key('end-call'),
                  icon: Icons.call_end, title: 'End',
                  color: const Color(0xffb83841), onPressed: onEnd),
                _action(
                  key: const Key('open-thread'),
                  icon: Icons.chat_bubble_outline_rounded,
                  title: 'Thread', onPressed: onOpenThread),
                if (onExpand != null)
                  _action(
                    key: const Key('expand-call'),
                    icon: Icons.open_in_full_rounded,
                    title: 'Expand', onPressed: onExpand!),
              ]),
          ),
      ]),
    );
  }

  Widget _action({required Key key, required IconData icon, required String title,
      required VoidCallback onPressed, Color color = const Color(0xff234d76)}) =>
    Column(mainAxisSize: MainAxisSize.min, children: [
      IconButton.filled(
        key: key,
        onPressed: onPressed,
        tooltip: title,
        style: IconButton.styleFrom(backgroundColor: color,
          foregroundColor: Colors.white),
        icon: Icon(icon, size: 22)),
      Text(title, style: const TextStyle(fontSize: 11, color: Colors.white70)),
    ]);
}
