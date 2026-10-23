import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'src/identity.dart';
import 'src/intercom.dart';
import 'src/node.dart';
import 'src/protocol.dart';
import 'package:open_filex/open_filex.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const LanMessengerApp());
}

class LanMessengerApp extends StatelessWidget {
  const LanMessengerApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'LAN Messenger', debugShowCheckedModeBanner: false,
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff1267d8)),
      useMaterial3: true, scaffoldBackgroundColor: const Color(0xfff7f9fd),
      textTheme: const TextTheme(bodyMedium: TextStyle(fontSize: 16),
          bodyLarge: TextStyle(fontSize: 18))),
    home: const HomePage(),
  );
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});
  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  LanNode? node;
  Intercom? intercom;
  Peer? selected;
  final input = TextEditingController();
  final scroll = ScrollController();
  final Map<String, List<ChatMessage>> chats = {};
  final Map<String, TransferProgress> transfers = {};
  bool busy = false;
  String? error;
  bool showReceived = false;
  bool _incomingDialogOpen = false;
  Timer? _ringTimer;
  List<File> received = [];
  Future<void> _historyQueue = Future<void>.value();

  @override
  void initState() { super.initState(); unawaited(_initialize()); }

  Future<void> _initialize() async {
    try {
      final identity = await Identity.load();
      final n = LanNode(identity);
      await _restoreChats();
      final inter = Intercom(n);
      n.onPeersChanged = () { if (mounted) setState(() {}); };
      n.onChat = (peer, message) {
        if (!mounted) return;
        setState(() => chats.putIfAbsent(peer.id, () => []).add(message));
        _persistChats();
        if (scroll.hasClients) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (scroll.hasClients) scroll.animateTo(scroll.position.maxScrollExtent,
                duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
          });
        }
      };
      n.onProgress = (progress) { if (mounted) setState(() => transfers[progress.id] = progress); };
      n.onFileOffer = (peer, name, size) async => _ask(
          title: 'Receive a file?', detail: '${peer.name} wants to send:\n$name\n${_bytes(size)}',
          allowText: 'Receive');
      n.onSignal = (peer, data) => unawaited(inter.incomingSignal(peer, data));
      inter.onChanged = () {
        if (!mounted) return;
        if (_incomingDialogOpen && inter.talkingTo == null) {
          Navigator.of(context, rootNavigator: true).pop(false);
        }
        setState(() {});
      };
      inter.onIncoming = (peer) async {
        if (!mounted) return false;
        setState(() { selected = peer; showReceived = false; });
        _incomingDialogOpen = true;
        SystemSound.play(SystemSoundType.alert);
        _ringTimer = Timer.periodic(const Duration(seconds: 3), (_) {
          if (_incomingDialogOpen) SystemSound.play(SystemSoundType.alert);
        });
        try {
          return await _ask(title: 'Incoming call',
              detail: '${peer.name} is calling.', allowText: 'Answer');
        } finally {
          _ringTimer?.cancel();
          _ringTimer = null;
          _incomingDialogOpen = false;
        }
      };
      await n.start();
      if (mounted) setState(() { node = n; intercom = inter; });
    } catch (e) {
      if (mounted) setState(() => error = 'Cannot start LAN Messenger: $e');
    }
  }

  Future<void> _restoreChats() async {
    try {
      final folder = await Identity.appDirectory();
      final file = File('${folder.path}${Platform.pathSeparator}chats.json');
      if (!await file.exists()) return;
      final data = jsonDecode(await file.readAsString()) as List<dynamic>;
      for (final item in data) {
        final message = ChatMessage.fromJson(item);
        if (message != null) chats.putIfAbsent(message.peerId, () => []).add(message);
      }
    } catch (_) { /* A corrupt cache must never prevent startup. */ }
  }

  void _persistChats() {
    _historyQueue = _historyQueue.then((_) async {
      final folder = await Identity.appDirectory();
      final file = File('${folder.path}${Platform.pathSeparator}chats.json');
      final data = chats.values.expand((items) => items.length > 300
          ? items.sublist(items.length - 300) : items).map((m) => m.toJson()).toList();
      await file.writeAsString(jsonEncode(data), flush: true);
    }).catchError((_) {});
  }

  Future<bool> _ask({required String title, required String detail,
      required String allowText}) async {
    if (!mounted) return false;
    return await showDialog<bool>(context: context, barrierDismissible: false,
      builder: (context) => AlertDialog(title: Text(title, style: const TextStyle(fontSize: 24)),
        content: Text(detail, style: const TextStyle(fontSize: 18)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Decline')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: Text(allowText)),
        ],
      )) ?? false;
  }

  void _toast(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _send() async {
    final peer = node?.peers[selected?.id];
    final text = input.text.trim();
    if (peer == null || text.isEmpty || node == null || busy) return;
    setState(() => busy = true);
    try {
      await node!.sendMessage(peer, text);
      input.clear();
    } catch (_) { _toast('Could not send. Check that the other device is open.'); }
    finally { if (mounted) setState(() => busy = false); }
  }

  Future<void> _sendFiles() async {
    final peer = node?.peers[selected?.id];
    if (node == null || peer == null || busy) return;
    final result = await FilePicker.pickFiles();
    if (result.isEmpty) return;
    setState(() => busy = true);
    try {
      for (final f in result) {
        if (f.path == null) { _toast('This file could not be accessed.'); continue; }
        await node!.sendFile(peer, File(f.path!));
      }
      _toast('File transfer complete.');
    } catch (e) { _toast('Transfer stopped: $e'); }
    finally { if (mounted) setState(() => busy = false); }
  }

  Future<void> _startCall() async {
    final peer = node?.peers[selected?.id];
    if (peer == null || intercom == null) return;
    try { await intercom!.call(peer); }
    catch (_) { _toast('Could not start the call. Check microphone permission.'); }
  }

  Future<void> _renameDevice() async {
    final n = node;
    if (n == null) return;
    final controller = TextEditingController(text: n.identity.displayName);
    final value = await showDialog<String>(context: context, builder: (dialogContext) =>
      AlertDialog(title: const Text('This device name'),
        content: TextField(controller: controller, autofocus: true, maxLength: 40,
          decoration: const InputDecoration(hintText: 'Example: PC-03'),
          onSubmitted: (value) => Navigator.pop(dialogContext, value)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(dialogContext, controller.text),
              child: const Text('Save')),
        ]));
    controller.dispose();
    if (value == null) return;
    try {
      await n.identity.rename(value);
      n.announce();
      if (mounted) setState(() {});
    } catch (_) { _toast('Enter a device name of 1 to 40 characters.'); }
  }

  static bool _imageName(String name) => RegExp(r'\.(jpg|jpeg|png|gif|webp|bmp)$',
      caseSensitive: false).hasMatch(name);

  Future<void> _openAttachment(String? path) async {
    if (path == null || !await File(path).exists()) {
      _toast('This file is no longer on this device.');
      return;
    }
    final result = await OpenFilex.open(path);
    if (result.type != ResultType.done) _toast('Unable to open this file: ${result.message}');
  }

  Future<void> _viewReceived() async {
    received = await node?.receivedFiles() ?? [];
    if (mounted) setState(() => showReceived = true);
  }

  static String _bytes(int size) {
    if (size < 1024) return '$size B';
    if (size < 1048576) return '${(size / 1024).toStringAsFixed(1)} KB';
    if (size < 1073741824) return '${(size / 1048576).toStringAsFixed(1)} MB';
    return '${(size / 1073741824).toStringAsFixed(2)} GB';
  }

  Widget _title() => Container(
    padding: const EdgeInsets.fromLTRB(20, 25, 20, 22),
    decoration: const BoxDecoration(color: Color(0xff103e82),
      borderRadius: BorderRadius.vertical(bottom: Radius.circular(24))),
    child: SafeArea(bottom: false, child: Row(children: [
      const Icon(Icons.forum_rounded, size: 36, color: Colors.white),
      const SizedBox(width: 14),
      const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('LAN Messenger', style: TextStyle(fontWeight: FontWeight.bold,
            fontSize: 25, color: Colors.white)),
        Text('Private conversations on your local network',
          style: TextStyle(color: Color(0xffdce9ff), fontSize: 13)),
      ])),
      IconButton(onPressed: _renameDevice,
        tooltip: 'Rename this device (optional)', icon: const Icon(Icons.edit_outlined, color: Colors.white)),
      IconButton(onPressed: _viewReceived,
        tooltip: 'Received files', icon: const Icon(Icons.folder_rounded, color: Colors.white)),
    ])));

  Widget _deviceList() {
    final peers = node?.peers.values.toList() ?? [];
    peers.sort((a, b) => a.name.compareTo(b.name));
    return Column(children: [
      Padding(padding: const EdgeInsets.all(16), child: Row(children: [
        const Icon(Icons.circle, color: Color(0xff21a56d), size: 13),
        const SizedBox(width: 10),
        Expanded(child: Text(node == null ? 'Starting...' :
          node!.discoveryReady ? 'Ready • ${node!.identity.displayName}' :
          'Discovery unavailable • check local network access',
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16))),
        IconButton(onPressed: () => node?.announce(), tooltip: 'Refresh',
          icon: const Icon(Icons.refresh, size: 28)),
      ])),
      Expanded(child: peers.isEmpty ? Center(child: Padding(
        padding: const EdgeInsets.all(30), child: Column(mainAxisSize: MainAxisSize.min,
          children: [Icon(Icons.wifi_tethering_rounded, size: 68,
            color: Theme.of(context).colorScheme.primary),
            const SizedBox(height: 20),
            const Text('Looking for nearby devices',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('Open LAN Messenger on another device connected to the same local network.',
                textAlign: TextAlign.center, style: TextStyle(fontSize: 17)),
          ]))) : ListView.separated(itemCount: peers.length,
          separatorBuilder: (_, __) => const Divider(height: 1),
          itemBuilder: (context, index) {
            final p = peers[index];
            return ListTile(minVerticalPadding: 18,
              leading: CircleAvatar(radius: 28, child: Text(p.name.characters.first.toUpperCase(),
                  style: const TextStyle(fontSize: 24))),
              title: Text(p.name, style: const TextStyle(fontSize: 20,
                  fontWeight: FontWeight.w600)),
              subtitle: Text('Online • ${p.shortCode}', style: const TextStyle(fontSize: 14)),
              trailing: const Icon(Icons.chevron_right, size: 28),
              onTap: () => setState(() { selected = p; showReceived = false; }),
            );
          })),
    ]);
  }

  Widget _attachmentBubble(ChatMessage message) {
    final path = message.filePath;
    final isImage = _imageName(message.text);
    return InkWell(onTap: () => _openAttachment(path),
      borderRadius: BorderRadius.circular(12),
      child: Column(mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (isImage && path != null && File(path).existsSync())
          ClipRRect(borderRadius: BorderRadius.circular(12), child:
            Image.file(File(path), width: 245, height: 180, fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => const Icon(Icons.broken_image, size: 48))),
        if (isImage) const SizedBox(height: 8),
        Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(isImage ? Icons.image_outlined : Icons.insert_drive_file_rounded,
              color: const Color(0xff164b94)),
          const SizedBox(width: 8),
          Flexible(child: Column(crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min, children: [
            Text(message.text, maxLines: 2, overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
            if (message.fileSize != null)
              Text(_bytes(message.fileSize!), style: const TextStyle(fontSize: 12)),
          ])),
          const SizedBox(width: 8),
          const Icon(Icons.open_in_new, size: 19),
        ]),
      ]));
  }

  Widget _chat() {
    final p = node?.peers[selected!.id] ?? selected!;
    final entries = chats[p.id] ?? [];
    final ongoing = transfers.values.where((t) => t.peerId == p.id &&
        (!t.finished || t.error != null)).toList();
    return Column(children: [
      ListTile(contentPadding: const EdgeInsets.symmetric(horizontal: 10),
        leading: IconButton(icon: const Icon(Icons.arrow_back, size: 28),
          onPressed: () => setState(() => selected = null)),
        title: Text(p.name, style: const TextStyle(fontSize: 21, fontWeight: FontWeight.bold)),
        subtitle: const Text('Local network'),
        trailing: intercom?.talkingTo?.id == p.id
          ? IconButton(tooltip: 'End call', onPressed: () => intercom?.hangUp(),
              icon: const Icon(Icons.call_end, color: Colors.red, size: 32))
          : IconButton(tooltip: 'Voice call', onPressed: node?.peers[p.id] == null ? null : _startCall,
              icon: const Icon(Icons.call_rounded, color: Color(0xff1a8c62), size: 31)),
      ),
      if (intercom?.talkingTo?.id == p.id)
        Container(color: const Color(0xffd7edff), width: double.infinity,
          padding: const EdgeInsets.all(12),
          child: Text(intercom!.connecting ? 'Connecting call...' :
                'Call active • Use your microphone to talk', textAlign: TextAlign.center)),
      Expanded(child: entries.isEmpty ? const Center(child: Text('Say hello 👋',
          style: TextStyle(fontSize: 22))) : ListView.builder(
        controller: scroll, padding: const EdgeInsets.all(16),
        itemCount: entries.length, itemBuilder: (context, index) {
          final msg = entries[index];
          return Align(alignment: msg.outgoing ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(margin: const EdgeInsets.only(bottom: 10),
              constraints: const BoxConstraints(maxWidth: 440),
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13),
              decoration: BoxDecoration(borderRadius: BorderRadius.circular(20),
                color: msg.outgoing ? const Color(0xffcfdefc) : Colors.white),
              child: msg.kind == 'file' ? _attachmentBubble(msg) :
                Text(msg.text, style: const TextStyle(fontSize: 18))));
        })),
      for (final transfer in ongoing.take(2))
        ListTile(dense: true, title: Text('${transfer.incoming ? 'Receiving' : 'Sending'} ${transfer.name}'),
          subtitle: transfer.error != null ? Text(transfer.error!) :
            LinearProgressIndicator(value: transfer.total == 0 ? 1 :
                (transfer.done / transfer.total).clamp(0.0, 1.0))),
      SafeArea(top: false, child: Padding(padding: const EdgeInsets.all(12),
        child: Row(children: [
          IconButton.filledTonal(iconSize: 28, tooltip: 'Send files',
              onPressed: busy ? null : _sendFiles, icon: const Icon(Icons.attach_file)),
          const SizedBox(width: 8),
          Expanded(child: TextField(controller: input, maxLines: 3, minLines: 1,
            maxLength: 4000, textInputAction: TextInputAction.send, onSubmitted: (_) => _send(),
            decoration: const InputDecoration(hintText: 'Write a message',
              counterText: '', border: OutlineInputBorder(), isDense: true))),
          const SizedBox(width: 8),
          IconButton.filled(iconSize: 28, tooltip: 'Send message',
              onPressed: busy ? null : _send, icon: const Icon(Icons.send)),
        ]))),
    ]);
  }

  Widget _files() => Column(children: [
    ListTile(leading: IconButton(onPressed: () => setState(() => showReceived = false),
        icon: const Icon(Icons.arrow_back, size: 28)),
        title: const Text('Received files', style: TextStyle(fontSize: 23, fontWeight: FontWeight.bold))),
    Expanded(child: received.isEmpty ? const Center(child: Text('No received files yet.')) :
      ListView.builder(itemCount: received.length, itemBuilder: (_, i) =>
        ListTile(leading: const Icon(Icons.insert_drive_file_outlined, size: 31),
          title: Text(received[i].uri.pathSegments.last),
          subtitle: Text(_bytes(received[i].lengthSync())),
          trailing: const Icon(Icons.open_in_new),
          onTap: () => _openAttachment(received[i].path)))),
    const Padding(padding: EdgeInsets.all(16), child: Text(
      'Tap a received file to open it. Files stay in the app’s local storage.',
      textAlign: TextAlign.center)),
  ]);

  @override
  Widget build(BuildContext context) => Scaffold(body: Column(children: [
    _title(),
    if (error != null) Padding(padding: const EdgeInsets.all(12), child: Text(error!,
        style: const TextStyle(color: Colors.red))),
    Expanded(child: showReceived ? _files() : selected == null ? _deviceList() : _chat()),
  ]));

  @override
  void dispose() {
    _ringTimer?.cancel();
    unawaited(intercom?.hangUp(notify: false) ?? Future<void>.value());
    unawaited(node?.dispose() ?? Future<void>.value());
    input.dispose();
    scroll.dispose();
    super.dispose();
  }
}