import 'dart:convert';
import 'dart:io';

import 'package:archive/archive.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:pdfrx/pdfrx.dart';
import 'package:video_player/video_player.dart';
import 'package:xml/xml.dart';

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
  bool get supported => const {
    'jpg','jpeg','png','gif','webp','bmp',
    'mp4','mov','webm','mkv','mp3','m4a','wav','ogg','aac',
    'pdf','docx','txt','md','log','csv','json','xml','xlsx',
  }.contains(ext);

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
    } else if (const {'txt','md','log','csv','json','xml','docx','xlsx'}.contains(ext)) {
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

/// Safe, bounded, read-only previews. ZIP macros/scripts are never executed.
/// Legacy binary .doc/.xls intentionally need an external editor.
Future<String> previewDocument(File file, String ext) async {
  final length = await file.length();
  if (length > 8 * 1024 * 1024) return 'This document is larger than the 8 MB inline preview limit. Open externally.';
  if (const {'txt','md','log','csv','json','xml'}.contains(ext)) {
    final raw = await file.readAsString().catchError((_) => 'This document is not UTF-8 encoded.');
    return raw.length > 24000 ? '${raw.substring(0,24000)}\n… Preview truncated' : raw;
  }
  if (ext != 'docx' && ext != 'xlsx') return 'Preview not available.';
  final zip = ZipDecoder().decodeBytes(await file.readAsBytes());
  String? readEntry(String name) {
    for (final entry in zip) {
      if (entry.name != name || !entry.isFile) continue;
      if (entry.size > 5 * 1024 * 1024) throw const FormatException('Document contains an oversized XML part');
      return utf8.decode(entry.readBytes(), allowMalformed: true);
    }
    return null;
  }
  if (ext == 'docx') {
    final xml = readEntry('word/document.xml');
    if (xml == null) return 'DOCX document content is unavailable.';
    final doc = XmlDocument.parse(xml);
    final paragraphs = doc.descendants.whereType<XmlElement>()
        .where((e) => e.name.local == 'p').take(180);
    final text = paragraphs.map((e) => e.descendants.whereType<XmlElement>()
        .where((t) => t.name.local == 't').map((t) => t.innerText).join()).join('\n');
    return text.isEmpty ? 'No readable text in this DOCX (images and formatting are not rendered).' : text;
  }
  final stringsXml = readEntry('xl/sharedStrings.xml');
  final shared = <String>[];
  if (stringsXml != null) {
    final parsed = XmlDocument.parse(stringsXml);
    for (final item in parsed.descendants.whereType<XmlElement>().where((e) => e.name.local == 'si').take(1000)) {
      shared.add(item.descendants.whereType<XmlElement>().where((e) => e.name.local == 't').map((e) => e.innerText).join());
    }
  }
  final sheet = readEntry('xl/worksheets/sheet1.xml');
  if (sheet == null) return 'No first worksheet available for preview.';
  final rows = XmlDocument.parse(sheet).descendants.whereType<XmlElement>()
      .where((e) => e.name.local == 'row').take(100);
  final lines = <String>[];
  for (final row in rows) {
    final cells = <String>[];
    for (final cell in row.children.whereType<XmlElement>().where((e) => e.name.local == 'c').take(24)) {
      final name = cell.getAttribute('r') ?? '';
      final values = cell.descendants.whereType<XmlElement>().where((e) => e.name.local == 'v' || e.name.local == 't');
      final value = values.isEmpty ? '' : values.first.innerText;
      final index = int.tryParse(value);
      final display = cell.getAttribute('t') == 's' && index != null && index < shared.length && index >= 0 ? shared[index] : value;
      if (display.isNotEmpty) cells.add('$name: $display');
    }
    if (cells.isNotEmpty) lines.add(cells.join('   |   '));
  }
  return lines.isEmpty ? 'No readable cells in the first worksheet.' : lines.join('\n');
}