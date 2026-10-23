import 'dart:convert';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:pdfrx/pdfrx.dart';
import 'package:video_player/video_player.dart';

/// Never read a document merely because its chat bubble is scrolling onscreen.
/// The preview only loads after the user expands a specific attachment.
class InlineAttachment extends StatefulWidget {
  final String? path;
  final String name;
  final int? size;
  final VoidCallback openExternally;
  const InlineAttachment({super.key, required this.path, required this.name,
    this.size, required this.openExternally});

  @override
  State<InlineAttachment> createState() => _InlineAttachmentState();
}

class _InlineAttachmentState extends State<InlineAttachment> {
  bool expanded = false;
  String get ext => widget.name.toLowerCase().split('.').last;
  IconData get icon => switch (ext) {
    'mp4' || 'mov' || 'webm' || 'mkv' => Icons.movie_outlined,
    'mp3' || 'm4a' || 'wav' || 'ogg' || 'aac' => Icons.audio_file_outlined,
    'pdf' => Icons.picture_as_pdf_outlined,
    'docx' || 'doc' || 'txt' || 'md' || 'log' => Icons.description_outlined,
    'xlsx' || 'xls' || 'csv' => Icons.table_chart_outlined,
    _ => Icons.attach_file,
  };
  bool get supported => supportsInlinePreview(ext);

  @override
  Widget build(BuildContext context) {
    final path = widget.path;
    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 420),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        InkWell(onTap: () => setState(() => expanded = !expanded), child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 5),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Icon(icon, size: 23),
            const SizedBox(width: 9),
            Flexible(child: Text(widget.name, maxLines: 2,
                overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w600))),
            const SizedBox(width: 10),
            Icon(expanded ? Icons.expand_less : Icons.expand_more),
          ]))),
        if (!expanded && path != null && File(path).existsSync() &&
            const {'jpg','jpeg','png','gif','webp','bmp'}.contains(ext))
          ClipRRect(borderRadius: BorderRadius.circular(8),
            child: Image.file(File(path), width: 250, height: 170, fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => const Text('Image preview unavailable'))),
        if (expanded) ...[
          const SizedBox(height: 6),
          if (path == null || !File(path).existsSync())
            const Text('Attachment is no longer available on this device.')
          else if (supported)
            _PreviewBody(key: ValueKey(path), file: File(path), extension: ext)
          else
            const Text('No safe inline preview is available for this file type.'),
          Align(alignment: Alignment.centerRight,
            child: TextButton.icon(onPressed: widget.openExternally,
              icon: const Icon(Icons.open_in_new, size: 16),
              label: const Text('Open externally'))),
        ],
      ]),
    );
  }
}

class _PreviewBody extends StatefulWidget {
  final File file;
  final String extension;
  const _PreviewBody({super.key, required this.file, required this.extension});
  @override
  State<_PreviewBody> createState() => _PreviewBodyState();
}

class _PreviewBodyState extends State<_PreviewBody> {
  VideoPlayerController? video;
  AudioPlayer? audio;
  Future<String>? document;
  String? mediaError;
  bool playing = false;

  @override
  void initState() {
    super.initState();
    final ext = widget.extension;
    if (const {'mp4','mov','webm','mkv'}.contains(ext)) {
      video = VideoPlayerController.file(widget.file)
        ..initialize().then((_) { if (mounted) setState(() {}); })
          .catchError((Object e) { if (mounted) setState(() => mediaError = '$e'); });
    } else if (const {'txt','md','log','csv','json','xml'}.contains(ext)) {
      document = previewDocument(widget.file, ext);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ext = widget.extension;
    if (const {'jpg','jpeg','png','gif','webp','bmp'}.contains(ext)) {
      return ClipRRect(borderRadius: BorderRadius.circular(8), child: Image.file(widget.file,
        fit: BoxFit.contain, height: 230, errorBuilder: (_,__,___) => const Text('Image unavailable')));
    }
    if (const {'mp4','mov','webm','mkv'}.contains(ext)) {
      final v = video;
      if (mediaError != null) return Text('Could not play video: $mediaError');
      if (v == null || !v.value.isInitialized) return const SizedBox(height: 70, child: Center(child: CircularProgressIndicator()));
      return Column(children: [
        SizedBox(height: 220, child: Center(child: AspectRatio(aspectRatio: v.value.aspectRatio <= 0 ? 16 / 9 : v.value.aspectRatio,
          child: VideoPlayer(v)))),
        Row(children: [IconButton(icon: Icon(v.value.isPlaying ? Icons.pause : Icons.play_arrow),
            onPressed: () async { if (v.value.isPlaying) { await v.pause(); } else { await v.play(); } if (mounted) setState(() {}); }),
          Expanded(child: VideoProgressIndicator(v, allowScrubbing: true)),
        ]),
      ]);
    }
    if (const {'mp3','m4a','wav','ogg','aac'}.contains(ext)) {
      return Row(children: [
        IconButton(icon: Icon(playing ? Icons.pause_circle_filled : Icons.play_circle_filled),
          onPressed: () async {
            try {
              final player = audio ??= AudioPlayer();
              if (playing) { await player.pause(); } else {
                if (player.state == PlayerState.paused) { await player.resume(); }
                else { await player.play(DeviceFileSource(widget.file.path)); }
              }
              if (mounted) setState(() => playing = !playing);
            } catch (e) { if (mounted) setState(() => mediaError = '$e'); }
          }),
        Expanded(child: Text(mediaError ?? 'Audio • Tap to ${playing ? 'pause' : 'play'}')),
      ]);
    }
    if (ext == 'pdf') {
      return SizedBox(height: 350, child: PdfViewer.file(widget.file.path));
    }
    return FutureBuilder<String>(future: document,
      builder: (context,snapshot) {
        if (snapshot.hasError) return Text('Preview unavailable: ${snapshot.error}');
        if (!snapshot.hasData) return const Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator());
        return Container(constraints: const BoxConstraints(maxHeight: 260),
          decoration: BoxDecoration(border: Border.all(color: Theme.of(context).dividerColor), borderRadius: BorderRadius.circular(8)),
          child: SingleChildScrollView(padding: const EdgeInsets.all(12), child: SelectableText(snapshot.data!,
            style: const TextStyle(fontFamily: 'monospace', fontSize: 13))));
      });
  }

  @override
  void dispose() {
    video?.dispose();
    audio?.dispose();
    super.dispose();
  }
}

/// Inline previews are deliberately conservative. A flattened worksheet or
/// DOCX XML dump is misleading, so Office attachments remain file cards.
bool supportsInlinePreview(String ext) => const <String>{
  'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp',
  'mp4', 'mov', 'webm', 'mkv', 'mp3', 'm4a', 'wav', 'ogg', 'aac',
  'pdf', 'txt', 'md', 'log', 'csv', 'json', 'xml',
}.contains(ext.toLowerCase());

Future<String> previewDocument(File file, String ext) async {
  if (!const <String>{'txt', 'md', 'log', 'csv', 'json', 'xml'}.contains(ext)) {
    return 'No faithful inline preview is available. Open in another application.';
  }
  final length = await file.length();
  if (length > 8 * 1024 * 1024) {
    return 'File exceeds the 8 MB text preview limit. Open externally.';
  }
  final raw = await file.readAsString().catchError(
      (_) => 'This document is not UTF-8 encoded.');
  return raw.length > 24000
      ? '${raw.substring(0,24000)}\\n… Preview truncated'
      : raw;
}
