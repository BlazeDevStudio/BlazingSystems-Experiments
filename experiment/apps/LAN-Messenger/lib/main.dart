import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:window_manager/window_manager.dart' as wm;
import 'package:tray_manager/tray_manager.dart' as tray;
import 'package:flutter_background/flutter_background.dart';
import 'src/settings.dart';
import 'src/alerts.dart';
import 'src/identity.dart';
import 'src/intercom.dart';
import 'src/node.dart';
import 'src/protocol.dart';
import 'package:open_filex/open_filex.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';

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

class _HomePageState extends State<HomePage> with wm.WindowListener, tray.TrayListener {
  LanNode? node;
  AppSettings settings = AppSettings();
  final Alerts alerts = Alerts();
  bool showSettings = false;
  bool backgroundRunning = false;
  bool _exitRequested = false;
  bool _trayInitialized = false;
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
  BuildContext? _incomingDialogContext;
  List<File> received = [];
  Future<void> _historyQueue = Future<void>.value();

  @override
  void initState() { super.initState(); unawaited(_initialize()); }

  Future<void> _initialize() async {
    try {
      settings = await AppSettings.load();
      alerts.enabled = settings.soundsEnabled;
      // Start the tiny LAN service before initializing optional native UI plugins.
      // A slow tray or Android foreground-service permission must never block chat.
      final identity = await Identity.load();
      final n = LanNode(identity);
      n.autoReceiveFiles = settings.autoReceiveFiles;
      n.maxIncomingFileBytes = settings.maximumFileMb * 1024 * 1024;
      await _restoreChats();
      final inter = Intercom(n);
      n.onPeersChanged = () { if (mounted) setState(() {}); };
      n.onChat = (peer, message) {
        if (!mounted) return;
        setState(() => chats.putIfAbsent(peer.id, () => []).add(message));
        _persistChats();
        if (!message.outgoing || message.kind == 'file') {
          unawaited(alerts.notify(message.kind == 'file' ? AlertKind.file : AlertKind.message));
        }
        if (scroll.hasClients) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (scroll.hasClients) scroll.animateTo(scroll.position.maxScrollExtent,
                duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
          });
        }
      };
      n.onProgress = (progress) { if (mounted) setState(() => transfers[progress.id] = progress); };
      // Auto-receive is configurable. Received attachments are never opened automatically.
      n.onFileOffer = (peer, name, size) async => _ask(
          title: 'Receive a file?', detail: '${peer.name} wants to send:\n$name\n${_bytes(size)}',
          allowText: 'Receive');
      n.onSignal = (peer, data) => unawaited(inter.incomingSignal(peer, data));
      inter.onChanged = () {
        if (!mounted) return;
        if (_incomingDialogOpen && inter.talkingTo == null) {
          // Never pop a route synchronously during Flutter's widget lifecycle.
          WidgetsBinding.instance.addPostFrameCallback((_) {
            final dialog = _incomingDialogContext;
            if (dialog != null && dialog.mounted && _incomingDialogOpen &&
                ModalRoute.of(dialog)?.isCurrent == true) {
              Navigator.of(dialog).pop(false);
            }
          });
        }
        setState(() {});
      };
      inter.onIncoming = (peer, incomingVideo) async {
        if (!mounted) return false;
        setState(() { selected = peer; showReceived = false; });
        if (Platform.isWindows) _openWindow();
        _incomingDialogOpen = true;
        unawaited(alerts.ring(incomingVideo ? AlertKind.videoCall : AlertKind.call));
        try {
          return await _ask(title: incomingVideo ? 'Incoming video call' : 'Incoming call',
              detail: '${peer.name} is calling.', allowText: 'Answer', incomingCall: true);
        } finally {
          unawaited(alerts.stopRing());
          _incomingDialogOpen = false;
          _incomingDialogContext = null;
        }
      };
      await n.start();
      if (mounted) setState(() { node = n; intercom = inter; });
      if (Platform.isWindows) {
        unawaited(_initializeDesktop());
      } else if (Platform.isAndroid && settings.backgroundMode) {
        unawaited(_enableBackground());
      }
    } catch (e) {
      if (mounted) setState(() => error = 'Cannot start LAN Messenger: $e');
    }
  }

  Future<void> _initializeDesktop() async {
    try {
      await wm.windowManager.ensureInitialized();
      await wm.windowManager.setPreventClose(true);
      wm.windowManager.addListener(this);
      final dir = await Identity.appDirectory();
      final iconFile = File('${dir.path}${Platform.pathSeparator}tray_icon.ico');
      final asset = await rootBundle.load('assets/icons/lan_messenger.ico');
      await iconFile.writeAsBytes(asset.buffer.asUint8List(), flush: true);
      await tray.trayManager.setIcon(iconFile.path);
      await tray.trayManager.setToolTip('LAN Messenger — Local network');
      await tray.trayManager.setContextMenu(tray.Menu(items: [
        tray.MenuItem(key: 'open', label: 'Open LAN Messenger'),
        tray.MenuItem(key: 'exit', label: 'Exit LAN Messenger'),
      ]));
      tray.trayManager.addListener(this);
      _trayInitialized = true;
    } catch (e) {
      // Tray plugin failure should not prevent messaging in the main window.
      if (mounted) setState(() => error = 'System tray unavailable: $e');
    }
  }

  Future<void> _enableBackground() async {
    if (!Platform.isAndroid) return;
    try {
      final ready = await FlutterBackground.initialize(
        androidConfig: FlutterBackgroundAndroidConfig(
          notificationTitle: 'LAN Messenger is ready',
          notificationText: 'Listening for local messages and calls',
          notificationIcon: AndroidResource(name: 'ic_launcher', defType: 'mipmap'),
          enableWifiLock: true,
        ),
      );
      if (ready) backgroundRunning = await FlutterBackground.enableBackgroundExecution();
    } catch (_) {
      backgroundRunning = false;
      // Permissions may be unavailable. Continue in foreground normally.
    }
    if (mounted) setState(() {});
  }

  Future<void> _setBackground(bool value) async {
    if (Platform.isAndroid) {
      if (value) {
        await _enableBackground();
      } else {
        try { await FlutterBackground.disableBackgroundExecution(); } catch (_) {}
        backgroundRunning = false;
      }
    }
    settings.backgroundMode = value;
    await settings.save();
    if (mounted) setState(() {});
  }

  @override
  void onWindowClose() {
    if (!Platform.isWindows) return;
    if (settings.minimizeToTray && !_exitRequested) {
      unawaited(wm.windowManager.hide());
    } else {
      unawaited(_exitWindows());
    }
  }

  Future<void> _exitWindows() async {
    if (_exitRequested) return;
    _exitRequested = true;
    await wm.windowManager.setPreventClose(false);
    await wm.windowManager.close();
  }

  void _openWindow() {
    unawaited(() async {
      await wm.windowManager.show();
      await wm.windowManager.restore();
      await wm.windowManager.focus();
    }());
  }

  @override
  void onTrayIconMouseDown() => _openWindow();

  @override
  void onTrayMenuItemClick(tray.MenuItem item) {
    if (item.key == 'exit') {
      unawaited(_exitWindows());
    } else if (item.key == 'open') {
      _openWindow();
    }
  }

  Future<void> _saveSettings() async {
    final n = node;
    if (n != null) {
      n.autoReceiveFiles = settings.autoReceiveFiles;
      n.maxIncomingFileBytes = settings.maximumFileMb * 1024 * 1024;
    }
    alerts.enabled = settings.soundsEnabled;
    if (!settings.soundsEnabled) unawaited(alerts.stopRing());
    await settings.save();
    if (mounted) setState(() {});
  }

  Widget _settingsPanel() => ListView(children: [
    ListTile(leading: IconButton(onPressed: () => setState(() => showSettings = false),
      icon: const Icon(Icons.arrow_back)),
      title: const Text('Settings', style: TextStyle(fontSize: 23, fontWeight: FontWeight.bold))),
    ListTile(title: const Text('This device name'),
      subtitle: Text(node?.identity.displayName ?? 'Starting'),
      trailing: const Icon(Icons.edit), onTap: _renameDevice),
    SwitchListTile(title: const Text('Automatically receive files'),
      subtitle: const Text('Save nearby LAN attachments without popups. Never open automatically.'),
      value: settings.autoReceiveFiles,
      onChanged: (value) { settings.autoReceiveFiles = value; unawaited(_saveSettings()); }),
    ListTile(title: const Text('Maximum automatic file size'),
      subtitle: Text('${settings.maximumFileMb} MB per file'),
      trailing: DropdownButton<int>(value: settings.maximumFileMb,
        items: [128,512,1024,2048].map((v) => DropdownMenuItem(value:v,child:Text('${v} MB'))).toList(),
        onChanged: (value) { if (value != null) { settings.maximumFileMb = value; unawaited(_saveSettings()); } })),
    SwitchListTile(title: const Text('Distinct notification sounds'),
      subtitle: const Text('Different tones for voice calls, video calls, chats and files'),
      value: settings.soundsEnabled,
      onChanged: (value) {settings.soundsEnabled = value; unawaited(_saveSettings());}),
    if (Platform.isWindows) ...[
      SwitchListTile(title: const Text('Close button minimizes to tray'),
        subtitle: const Text('Leave LAN Messenger running in the taskbar hidden icons'),
        value: settings.minimizeToTray,
        onChanged: (value) {settings.minimizeToTray = value; unawaited(_saveSettings());}),
      SwitchListTile(title: const Text('Start with Windows'),
        subtitle: const Text('Run when this Windows account signs in'),
        value: settings.startWithWindows,
        onChanged: (value) async {
          try { await settings.configureWindowsStartup(value); if (mounted) setState(() {}); }
          catch (e) { _toast('$e'); }
        }),
      ListTile(leading: const Icon(Icons.power_settings_new),
        title: const Text('Exit LAN Messenger'), onTap: _exitWindows),
    ],
    if (Platform.isAndroid) SwitchListTile(
      title: const Text('Keep available in background'),
      subtitle: Text(backgroundRunning ?
        'Active — Android displays a persistent notification' :
        'Not active — allow system permissions to keep listening'),
      value: settings.backgroundMode,
      onChanged: (value) => _setBackground(value)),
    const Padding(padding: EdgeInsets.all(16), child: Text(
      'Internet is not required, but devices must share a reachable LAN. '
      'Android may suspend the application after force-stop or under battery restrictions. '
      'Your contacts are not authenticated by a separate account service.',
      style: TextStyle(color: Colors.black54))),
  ]);

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
      required String allowText, bool incomingCall = false}) async {
    if (!mounted) return false;
    return await showDialog<bool>(context: context, barrierDismissible: false,
      builder: (context) {
        if (incomingCall) _incomingDialogContext = context;
        return AlertDialog(title: Text(title, style: const TextStyle(fontSize: 24)),
        content: Text(detail, style: const TextStyle(fontSize: 18)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Decline')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: Text(allowText)),
        ],
      );
      }) ?? false;
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

  Future<void> _startCall({bool video = false}) async {
    final peer = node?.peers[selected?.id];
    if (peer == null || intercom == null) return;
    try { await intercom!.call(peer, withVideo: video); }
    catch (e) { _toast('Could not start call: $e'); }
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
    // showDialog resolves before its reverse animation finishes. Don't dispose
    // TextField's controller while a transitioning route still depends on it.
    Future<void>.delayed(const Duration(milliseconds: 550), controller.dispose);
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
      IconButton(onPressed: () => setState(() {showSettings = true; selected = null; showReceived = false;}),
        tooltip: 'Settings', icon: const Icon(Icons.settings, color: Colors.white)),
    ])));

  Widget _deviceList() {
    final peers = node?.peers.values.where((p) => node!.isOnline(p)).toList() ?? [];
    peers.sort((a, b) {
      final onlineA = node!.isOnline(a);
      final onlineB = node!.isOnline(b);
      if (onlineA != onlineB) return onlineA ? -1 : 1;
      return a.name.compareTo(b.name);
    });
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
              subtitle: Text('${node!.isOnline(p) ? 'Online' : 'Offline'} • ${p.shortCode}', style: const TextStyle(fontSize: 14)),
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
        subtitle: Text(node?.isOnline(p) == true ? 'Online • Local network' :
            'Offline • Waiting for this device'),
        trailing: intercom?.talkingTo?.id == p.id
          ? IconButton(tooltip: 'End call', onPressed: () => intercom?.hangUp(),
              icon: const Icon(Icons.call_end, color: Colors.red, size: 30))
          : Row(mainAxisSize: MainAxisSize.min, children: [
              IconButton(tooltip: 'Voice call', onPressed: node?.isOnline(p) != true
                  ? null : () => _startCall(),
                icon: const Icon(Icons.call_rounded, color: Color(0xff1a8c62), size: 29)),
              IconButton(tooltip: 'Video call', onPressed: node?.isOnline(p) != true
                  ? null : () => _startCall(video: true),
                icon: const Icon(Icons.videocam_rounded, color: Color(0xff1a8c62), size: 29)),
            ]),
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

  Widget _activeCall() {
    final call = intercom!;
    return Material(
      color: const Color(0xff102b4e),
      child: SafeArea(child: Column(children: [
        const SizedBox(height: 20),
        Text(call.talkingTo?.name ?? 'Call',
          style: const TextStyle(fontSize: 26, color: Colors.white,
              fontWeight: FontWeight.bold)),
        Text(call.connecting ? 'Connecting...' : 'Connected • Local network',
          style: const TextStyle(fontSize: 17, color: Colors.white70)),
        Expanded(child: call.video
          ? Stack(fit: StackFit.expand, children: [
              if (call.remoteRenderer != null)
                RTCVideoView(call.remoteRenderer!, objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitContain)
              else const Center(child: Icon(Icons.videocam, color: Colors.white54, size: 80)),
              if (call.localRenderer != null)
                Positioned(top: 20, right: 12, height: 150, width: 120,
                  child: ClipRRect(borderRadius: BorderRadius.circular(12),
                    child: RTCVideoView(call.localRenderer!, mirror: true))),
            ])
          : const Center(child: Icon(Icons.call, color: Colors.white70, size: 105))),
        Padding(padding: const EdgeInsets.all(24), child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
            IconButton.filledTonal(tooltip: call.muted ? 'Unmute' : 'Mute',
              iconSize: 32, onPressed: () => call.setMuted(!call.muted),
              icon: Icon(call.muted ? Icons.mic_off : Icons.mic)),
            IconButton.filled(tooltip: 'End call', iconSize: 36,
              style: IconButton.styleFrom(backgroundColor: Colors.red),
              onPressed: () => call.hangUp(), icon: const Icon(Icons.call_end)),
          ])),
      ])),
    );
  }

  @override
  Widget build(BuildContext context) => Stack(children: [
    Scaffold(body: Column(children: [
    _title(),
    if (error != null) Padding(padding: const EdgeInsets.all(12), child: Text(error!,
        style: const TextStyle(color: Colors.red))),
    Expanded(child: showSettings ? _settingsPanel() : showReceived ? _files() :
      selected == null ? _deviceList() : _chat()),
  ])),
    if (intercom?.talkingTo != null && !_incomingDialogOpen)
      Positioned.fill(child: _activeCall()),
  ]);

  @override
  void dispose() {
    unawaited(intercom?.hangUp(notify: false) ?? Future<void>.value());
    unawaited(node?.dispose() ?? Future<void>.value());
    unawaited(alerts.dispose());
    if (_trayInitialized) {
      tray.trayManager.removeListener(this);
      unawaited(tray.trayManager.destroy());
      wm.windowManager.removeListener(this);
    }
    if (Platform.isAndroid && backgroundRunning) {
      unawaited(FlutterBackground.disableBackgroundExecution());
    }
    input.dispose();
    scroll.dispose();
    super.dispose();
  }
}