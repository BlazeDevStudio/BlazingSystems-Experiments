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
import 'src/inline_preview.dart';
import 'src/remote_control_surface.dart';
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
  static const _notifications = MethodChannel('lan_messenger/notifications');
  static const _desktopCalls = MethodChannel('lan_messenger/desktop_call');
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
  bool _callMinimized = false;
  Offset _videoPosition = const Offset(16, 20);
  ControlInputMode _controlMode = ControlInputMode.trackpad;
  Offset _miniCallPosition = const Offset(20, 110);
  bool _incomingDialogOpen = false;
  BuildContext? _incomingDialogContext;
  bool? _pendingIncomingDecision;
  Completer<bool>? _incomingAnswer;
  Peer? _incomingPeer;
  bool _incomingVideo = false;
  bool _nativeIncomingAvailable = false;
  String? _activeCallUiId;
  bool? _lastNativeMuted;
  bool _compactWindowsVideo = false;
  bool _restoringCompactWindow = false;
  Size? _normalWindowSize;
  Offset? _normalWindowPosition;
  bool _normalWindowWasVisible = true;
  List<File> received = [];
  Future<void> _historyQueue = Future<void>.value();

  @override
  void initState() {
    super.initState();
    if (Platform.isAndroid) {
      _notifications.setMethodCallHandler(_handleNativeCallAction);
    }
    if (Platform.isWindows) {
      _desktopCalls.setMethodCallHandler(_handleDesktopCallAction);
    }
    unawaited(_initialize());
  }

  Future<dynamic> _handleNativeCallAction(MethodCall call) async {
    if (call.method != 'callAction' || !mounted) return;
    final data = call.arguments;
    if (data is! Map) return;
    final id = data['callId'];
    final action = data['action'];
    if (id is! String || id != intercom?.callId) return;
    if (action == 'answer' || action == 'decline') {
      _resolveIncomingDialog(action == 'answer');
    } else if (!_incomingDialogOpen) {
      if (action == 'end') {
        unawaited(intercom?.hangUp() ?? Future<void>.value());
      } else if (action == 'mute') {
        unawaited(intercom?.setMuted(!(intercom?.muted ?? false)) ??
            Future<void>.value());
      } else if (action == 'open') {
        unawaited(_openCallThread());
      }
    }
  }

  Future<dynamic> _handleDesktopCallAction(MethodCall call) async {
    if (call.method != 'callAction' || !mounted) return;
    final data = call.arguments;
    if (data is! Map || data['callId'] != intercom?.callId) return;
    final action = data['action'];
    if (action == 'answer' || action == 'decline') {
      _resolveIncomingDialog(action == 'answer');
    } else if (action == 'open') {
      unawaited(_openCallThread());
    } else if (!_incomingDialogOpen && action == 'end') {
      unawaited(intercom?.hangUp() ?? Future<void>.value());
    } else if (!_incomingDialogOpen && action == 'mute') {
      unawaited(intercom?.setMuted(!(intercom?.muted ?? false)) ??
          Future<void>.value());
    }
  }

  void _resolveIncomingDialog(bool answered) {
    if (!_incomingDialogOpen) return;
    // A system banner or tray action may arrive before the Flutter dialog has
    // completed its first frame; retain the answer until its route is ready.
    final decision = _incomingAnswer;
    if (decision != null && !decision.isCompleted) {
      decision.complete(answered);
      return;
    }
    _pendingIncomingDecision = answered;
    _flushIncomingDecision();
  }

  void _flushIncomingDecision() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final dialog = _incomingDialogContext;
      final decision = _pendingIncomingDecision;
      if (decision == null || !_incomingDialogOpen || !mounted) return;
      if (dialog != null && dialog.mounted &&
          ModalRoute.of(dialog)?.isCurrent == true) {
        _pendingIncomingDecision = null;
        Navigator.of(dialog).pop(decision);
      }
    });
  }

  Future<bool> _showNativeIncoming(Peer peer, bool video) async {
    if (!Platform.isAndroid || !settings.headsUpNotifications) return false;
    try {
      return await _notifications.invokeMethod<bool>('incoming', {
        'caller': peer.name,
        'callId': intercom?.callId ?? '',
        'video': video,
      }) ?? false;
    } catch (_) { return false; }
  }

  Future<void> _dismissNativeIncoming() async {
    if (!Platform.isAndroid) return;
    try { await _notifications.invokeMethod<void>('dismissIncoming'); }
    catch (_) {}
  }

  Future<bool> _showDesktopIncoming(Peer peer, bool video) async {
    if (!Platform.isWindows) return false;
    try {
      return await _desktopCalls.invokeMethod<bool>('incoming', {
        'callId': intercom?.callId ?? '',
        'caller': peer.name,
        'video': video,
      }) ?? false;
    } catch (_) {
      // The tray remains usable if Windows refuses native popup creation.
      return false;
    }
  }

  Future<void> _dismissDesktopCall() async {
    if (!Platform.isWindows) return;
    try { await _desktopCalls.invokeMethod<void>('dismiss'); } catch (_) {}
  }

  Future<void> _showOngoingCall(Peer peer, String id, bool video) async {
    final args = {
      'caller': peer.name, 'callId': id,
      'video': video, 'muted': intercom?.muted ?? false,
    };
    _activeCallUiId = id;
    _lastNativeMuted = intercom?.muted;
    if (Platform.isAndroid) {
      try { await _notifications.invokeMethod<bool>('ongoing', args); }
      catch (_) {}
    } else if (Platform.isWindows) {
      if (video) {
        await _dismissDesktopCall();
        await _openCompactVideoWindow();
      } else {
        try { await _desktopCalls.invokeMethod<bool>('ongoing', args); }
        catch (_) {}
      }
    }
  }

  Future<void> _openCompactVideoWindow() async {
    if (!Platform.isWindows || _compactWindowsVideo) return;
    try {
      await wm.windowManager.ensureInitialized();
      _normalWindowWasVisible = await wm.windowManager.isVisible();
      _normalWindowSize = await wm.windowManager.getSize();
      _normalWindowPosition = await wm.windowManager.getPosition();
      if (await wm.windowManager.isMinimized()) {
        // Restore only the app's own surface, without activating it.
        await wm.windowManager.restore();
      }
      _compactWindowsVideo = true;
      if (mounted) setState(() {});
      await wm.windowManager.setMinimumSize(const Size(290, 230));
      await wm.windowManager.setSize(const Size(358, 310));
      await wm.windowManager.setAlignment(Alignment.bottomRight);
      await wm.windowManager.setAlwaysOnTop(true);
      await wm.windowManager.setSkipTaskbar(true);
      // Unlike show(), show(inactive: true) deliberately does not take focus
      // away from the current PC app (game, document, presenter etc.).
      await wm.windowManager.show(inactive: true);
    } catch (e) {
      _compactWindowsVideo = false;
      if (mounted) setState(() {
        error = 'Could not open compact video viewer: $e';
      });
    }
  }

  Future<void> _restoreCompactVideo({bool forceOpen = false}) async {
    if (!Platform.isWindows || !_compactWindowsVideo ||
        _restoringCompactWindow) return;
    _restoringCompactWindow = true;
    _compactWindowsVideo = false;
    if (mounted) setState(() {});
    try {
      await wm.windowManager.setAlwaysOnTop(false);
      await wm.windowManager.setSkipTaskbar(false);
      await wm.windowManager.setMinimumSize(const Size(0, 0));
      if (_normalWindowSize != null) {
        await wm.windowManager.setSize(_normalWindowSize!);
      }
      if (_normalWindowPosition != null) {
        await wm.windowManager.setPosition(_normalWindowPosition!);
      }
      if (forceOpen || _normalWindowWasVisible) {
        await wm.windowManager.show(inactive: !forceOpen);
        if (forceOpen) await wm.windowManager.focus();
      } else {
        await wm.windowManager.hide();
      }
    } catch (_) {
      // Do not interrupt a call if Windows rejects a geometry change.
    } finally {
      _normalWindowPosition = null;
      _normalWindowSize = null;
      _restoringCompactWindow = false;
    }
  }

  Future<void> _openCallThread() async {
    if (!mounted) return;
    setState(() {
      _callMinimized = true;
      showSettings = false;
      showReceived = false;
      selected = intercom?.talkingTo ?? _incomingPeer ?? selected;
    });
    if (Platform.isWindows) {
      if (_compactWindowsVideo) {
        await _restoreCompactVideo(forceOpen: true);
      } else {
        _openWindow();
      }
    }
  }

  Future<void> _endCallPresentation() async {
    await _dismissNativeIncoming();
    await _dismissDesktopCall();
    if (Platform.isWindows) await _restoreCompactVideo();
  }

  Future<void> _restoreWindowAfterCall() async {
    if (!Platform.isWindows) return;
    try {
      await wm.windowManager.setAlwaysOnTop(false);
      if (_trayInitialized) {
        await tray.trayManager.setToolTip('LAN Messenger — Local network');
        await tray.trayManager.setContextMenu(tray.Menu(items: [
          tray.MenuItem(key: 'open', label: 'Open LAN Messenger'),
          tray.MenuItem(key: 'exit', label: 'Exit LAN Messenger'),
        ]));
      }
    } catch (_) {}
  }

  Future<void> _initialize() async {
    try {
      settings = await AppSettings.load();
      alerts.enabled = settings.soundsEnabled;
      _applySounds();
      // Optional OS integrations cannot block LAN discovery or messaging.
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
        if (!message.outgoing) {
          if (!Platform.isAndroid || !settings.headsUpNotifications) {
            unawaited(alerts.notify(message.kind == 'file' ? AlertKind.file : AlertKind.message));
          }
          if (!message.outgoing) {
            _nativeNotify(message.kind == 'file' ? 'file' : 'message',
                peer.name, message.kind == 'file' ? 'Sent a file: ${message.text}' : message.text);
          }
        }
        if (scroll.hasClients) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (scroll.hasClients) scroll.animateTo(scroll.position.maxScrollExtent,
                duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
          });
        }
      };
      n.onProgress = (progress) {
        if (mounted) setState(() => transfers[progress.id] = progress);
        if (progress.finished && !progress.incoming) {
          _nativeNotify('file', 'File sent', progress.name);
        }
      };
      // Auto-receive is configurable. Received attachments are never opened automatically.
      n.onFileOffer = (peer, name, size) async => _ask(
          title: 'Receive a file?', detail: '${peer.name} wants to send:\n$name\n${_bytes(size)}',
          allowText: 'Receive');
      n.onSignal = (peer, data) => unawaited(inter.incomingSignal(peer, data));
      inter.onChanged = () {
        if (!mounted) return;
        if (_incomingDialogOpen && inter.talkingTo == null) {
          _resolveIncomingDialog(false);
        }
        if (_activeCallUiId != null && inter.talkingTo == null) {
          _activeCallUiId = null;
          _lastNativeMuted = null;
          unawaited(_endCallPresentation());
        } else if (_activeCallUiId == inter.callId &&
            _lastNativeMuted != inter.muted) {
          _lastNativeMuted = inter.muted;
          final currentPeer = inter.talkingTo;
          final id = inter.callId;
          if (currentPeer != null && id != null) {
            unawaited(_showOngoingCall(currentPeer, id, inter.video));
          }
        }
        setState(() {});
      };
      inter.onChooseDesktopSource = (sources) async {
        if (!mounted || !Platform.isWindows) return null;
        return showDialog<DesktopCapturerSource>(
          context: context, barrierDismissible: true,
          builder: (dialogContext) => AlertDialog(
            title: const Text('Choose screen to share'),
            content: SizedBox(
              width: 440, height: 300,
              child: ListView.builder(
                itemCount: sources.length,
                itemBuilder: (context, i) {
                  final source = sources[i];
                  return ListTile(
                    leading: Icon(source.type == SourceType.Screen
                        ? Icons.monitor : Icons.web_asset),
                    title: Text(source.name, maxLines: 1,
                      overflow: TextOverflow.ellipsis),
                    subtitle: Text(source.type == SourceType.Screen
                        ? 'Full display • Recommended'
                        : 'Application window • May show black if minimized'),
                    onTap: () => Navigator.of(dialogContext).pop(source),
                  );
                },
              ),
            ),
            actions: [TextButton(onPressed:
              () => Navigator.of(dialogContext).pop(),
              child: const Text('Cancel'))],
          ),
        );
      };
      inter.onControlStatus = (message) {
        if (mounted) _toast(message);
      };
      inter.onRemoteControlRequest = (peer) async {
        if (!mounted || inter.talkingTo?.id != peer.id ||
            !inter.sharingScreen) return false;
        if (Platform.isAndroid) {
          final available = await const MethodChannel('lan_messenger/remote')
              .invokeMethod<bool>('available').catchError((_) => false);
          if (available != true) {
            _toast('Android remote control needs Accessibility permission. '
                'Enable LAN Messenger Remote Touch in Android Accessibility settings.');
            return false;
          }
        }
        return _ask(title: 'Allow remote control?',
          detail: '${peer.name} requests temporary control of your shared '
              '${Platform.isAndroid ? "Android screen" : "Windows screen"}. '
              'Permission lasts up to 5 minutes. Stop sharing or revoke at any time.',
          allowText: 'Allow for 5 minutes');
      };
      inter.onIncoming = (peer, incomingVideo) async {
        if (!mounted) return false;
        final id = inter.callId;
        if (id == null) return false;
        final answer = Completer<bool>();
        _incomingAnswer = answer;
        _incomingPeer = peer;
        _incomingVideo = incomingVideo;
        _incomingDialogOpen = true;
        _pendingIncomingDecision = null;
        _callMinimized = true;
        setState(() { selected = peer; showReceived = false; });
        // Never focus or restore the Windows app on an inbound call.
        // Android uses a system CallStyle heads-up notification with actions.
        if (Platform.isWindows) {
          unawaited(alerts.ring(incomingVideo
              ? AlertKind.videoCall : AlertKind.call));
          _nativeIncomingAvailable =
              await _showDesktopIncoming(peer, incomingVideo);
          if (_trayInitialized) {
            unawaited(tray.trayManager.setContextMenu(tray.Menu(items: [
              tray.MenuItem(key: 'answer', label: 'Answer ${peer.name}'),
              tray.MenuItem(key: 'decline', label: 'Decline call'),
              tray.MenuItem(key: 'open', label: 'Open LAN Messenger'),
              tray.MenuItem(key: 'exit', label: 'Exit LAN Messenger'),
            ])));
          }
        } else {
          _nativeIncomingAvailable =
              await _showNativeIncoming(peer, incomingVideo);
          if (!_nativeIncomingAvailable) {
            unawaited(alerts.ring(incomingVideo
                ? AlertKind.videoCall : AlertKind.call));
          }
        }
        bool accepted = false;
        try {
          // Also resolves on remote hangup; never leave an orphaned modal route.
          accepted = await answer.future.timeout(const Duration(seconds: 42),
              onTimeout: () => false);
          if (id != inter.callId || inter.talkingTo?.id != peer.id) {
            return false;
          }
          return accepted;
        } finally {
          _incomingAnswer = null;
          _incomingDialogOpen = false;
          _incomingPeer = null;
          _nativeIncomingAvailable = false;
          _incomingDialogContext = null;
          _pendingIncomingDecision = null;
          await _dismissNativeIncoming();
          unawaited(alerts.stopRing());
          unawaited(_restoreWindowAfterCall());
          if (accepted && inter.callId == id &&
              inter.talkingTo?.id == peer.id) {
            await _showOngoingCall(peer, id, incomingVideo);
          } else {
            await _dismissDesktopCall();
          }
          if (mounted) setState(() {});
        }
      };
      await n.start();
      if (mounted) setState(() { node = n; intercom = inter; });
      if (Platform.isWindows) {
        unawaited(_initializeDesktop());
      } else if (Platform.isAndroid) {
        unawaited(_notifications.invokeMethod<void>('setup').catchError((_) {}));
        if (settings.backgroundMode) unawaited(_enableBackground());
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
    if (item.key == 'answer' || item.key == 'decline') {
      _resolveIncomingDialog(item.key == 'answer');
    } else if (item.key == 'exit') {
      unawaited(_exitWindows());
    } else if (item.key == 'open') {
      _openWindow();
    }
  }

  void _applySounds() {
    alerts.enabled = settings.soundsEnabled;
    alerts.useAppSounds = settings.useAppSounds;
    alerts.customSounds.clear();
    for (final kind in AlertKind.values) {
      final path = settings.soundPaths[kind.name];
      if (path != null && path.isNotEmpty) alerts.customSounds[kind] = path;
    }
  }

  Future<void> _openAndroidAssistiveSettings() async {
    if (!Platform.isAndroid || !mounted) return;
    final action = await showDialog<String>(context: context, builder: (ctx) =>
      AlertDialog(
        title: const Text('Enable optional remote control'),
        content: const Text(
          'LAN Messenger Remote Touch needs Android Accessibility access. '
          'On Android 13+ an APK installed outside an app store may be '
          'restricted: first try enabling LAN Messenger Remote Touch under '
          'Settings > Accessibility > Installed apps. If the switch is gray, '
          'open Settings > Apps > LAN Messenger > three-dot menu > '
          'Allow restricted settings, then return to Accessibility. '
          'Only permit this on your own trusted device. The caller must '
          'still approve each remote session, and approval expires in five minutes.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(ctx, 'app'),
            child: const Text('App info')),
          FilledButton(onPressed: () => Navigator.pop(ctx, 'accessibility'),
            child: const Text('Accessibility')),
        ],
      ));
    if (action == null) return;
    try {
      await const MethodChannel('lan_messenger/remote').invokeMethod<void>(
        action == 'app' ? 'openAppInfo' : 'openAccessibilitySettings');
    } catch (e) { _toast('Could not open Android settings: $e'); }
  }

  Future<void> _openAndroidCallNotificationSettings() async {
    if (!Platform.isAndroid) return;
    try {
      await const MethodChannel('lan_messenger/remote')
          .invokeMethod<void>('openCallSettings');
    } catch (e) { _toast('Could not open call notification settings: $e'); }
  }

  void _nativeNotify(String kind, String title, String message) {
    if (!Platform.isAndroid || !settings.headsUpNotifications) return;
    unawaited(_notifications.invokeMethod<void>('show', {
      'kind': kind, 'title': title, 'body': message,
    }).catchError((_) {}));
  }

  Future<void> _pickAvatar() async {
    final selected = await FilePicker.pickFiles(type: FileType.image);
    if (selected.isEmpty || selected.first.path == null) return;
    final file = File(selected.first.path!);
    if (await file.length() > 4 * 1024 * 1024) { _toast('Choose a profile image below 4 MB.'); return; }
    final dir = await Identity.appDirectory();
    final target = File('${dir.path}${Platform.pathSeparator}avatar.${file.path.split('.').last.toLowerCase()}');
    await file.copy(target.path);
    settings.avatarPath = target.path;
    await _saveSettings();
  }

  Future<void> _pickTone(AlertKind kind) async {
    final picked = await FilePicker.pickFiles(type: FileType.custom, allowedExtensions: ['wav','mp3','m4a','ogg']);
    if (picked.isEmpty || picked.first.path == null) return;
    final file = File(picked.first.path!);
    if (await file.length() > 5 * 1024 * 1024) { _toast('Choose an audio file below 5 MB.'); return; }
    final dir = await Identity.appDirectory();
    final target = File('${dir.path}${Platform.pathSeparator}tone_${kind.name}.${file.path.split('.').last.toLowerCase()}');
    await file.copy(target.path);
    settings.soundPaths[kind.name] = target.path;
    settings.useAppSounds = false;
    await _saveSettings();
    unawaited(alerts.notify(kind));
  }

  static const _swatches = <int>[
    0xff1267d8, 0xff008577, 0xff7051c5, 0xffc44c78,
    0xffdf7c25, 0xff546b7d, 0xff303d58,
  ];

  Widget _colorPicker(int selected, ValueChanged<int> onPick) =>
      Wrap(spacing: 8, runSpacing: 8, children: _swatches.map((value) =>
        Tooltip(message: 'Choose this accent color', child: InkWell(
          onTap: () => onPick(value), borderRadius: BorderRadius.circular(40),
          child: Container(width: 32, height: 32,
            decoration: BoxDecoration(color: Color(value), shape: BoxShape.circle,
              border: Border.all(color: selected == value ? Colors.black : Colors.transparent, width: 2)),
            child: selected == value ? const Icon(Icons.check, color: Colors.white, size: 18) : null),
        ))).toList());

    Future<void> _saveSettings() async {
    final n = node;
    if (n != null) {
      n.autoReceiveFiles = settings.autoReceiveFiles;
      n.maxIncomingFileBytes = settings.maximumFileMb * 1024 * 1024;
    }
    _applySounds();
    if (!settings.soundsEnabled) unawaited(alerts.stopRing());
    await settings.save();
    if (mounted) setState(() {});
  }

  Widget _settingsPanel() => ListView(children: [
    ListTile(leading: IconButton(onPressed: () => setState(() => showSettings = false),
      icon: const Icon(Icons.arrow_back)),
      title: const Text('Settings', style: TextStyle(fontSize: 23, fontWeight: FontWeight.bold))),
    ListTile(leading: _myAvatar(radius: 18),
      title: const Text('Profile picture'), subtitle: const Text('Pick an image from this device'),
      trailing: IconButton(icon: const Icon(Icons.image_outlined), onPressed: _pickAvatar),
      onTap: _pickAvatar),
    const Padding(padding: EdgeInsets.fromLTRB(16, 12, 16, 2),
      child: Text('Appearance', style: TextStyle(fontWeight: FontWeight.bold))),
    Padding(padding: const EdgeInsets.fromLTRB(16, 10, 16, 10), child: Column(
      crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Accent color'), const SizedBox(height: 8),
        _colorPicker(settings.accentValue, (value) {
          settings.accentValue = value; unawaited(_saveSettings());
        }),
      ])),
    ListTile(title: const Text('Message font'),
      trailing: DropdownButton<String>(value: settings.fontFamily,
        items: ['Default','Serif','Monospace'].map((v)=>DropdownMenuItem(value:v,child:Text(v))).toList(),
        onChanged: (v) { if (v != null) { settings.fontFamily = v; unawaited(_saveSettings()); } })),
    ListTile(title: const Text('Message text size'), subtitle: Slider(
      min: 0.85, max: 1.4, divisions: 11, label: '${(settings.fontScale * 100).round()}%',
      value: settings.fontScale,
      onChanged: (value) => setState(() => settings.fontScale = value),
      onChangeEnd: (_) => unawaited(_saveSettings()),
    )),
    const Divider(height: 16),
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
    if (Platform.isAndroid) SwitchListTile(
      title: const Text('Pop-up notifications'),
      subtitle: const Text('Android heads-up alerts for incoming calls, messages and files (requires notification permission)'),
      value: settings.headsUpNotifications,
      onChanged: (v) {
        settings.headsUpNotifications = v;
        if (v) unawaited(_notifications.invokeMethod<void>('setup').catchError((_) {}));
        unawaited(_saveSettings());
      }),
    if (Platform.isAndroid) ListTile(
      leading: const Icon(Icons.call),
      title: const Text('Incoming call banners'),
      subtitle: const Text('Allow heads-up call notifications, Answer and Decline buttons in Android settings'),
      trailing: const Icon(Icons.open_in_new),
      onTap: _openAndroidCallNotificationSettings),
    if (Platform.isAndroid) ListTile(
      leading: const Icon(Icons.touch_app),
      title: const Text('Enable Android Remote Touch'),
      subtitle: const Text('If Accessibility is gray on a sideloaded APK: App info > three dots > Allow restricted settings. Permission is optional and each call still requires approval.'),
      trailing: const Icon(Icons.open_in_new),
      onTap: _openAndroidAssistiveSettings),
    SwitchListTile(title: const Text('Use LAN Messenger sounds'),
      subtitle: const Text('Default: distinctive sounds for each event. Turn off to use the custom tones below.'),
      value: settings.useAppSounds,
      onChanged: (v) { settings.useAppSounds = v; unawaited(_saveSettings()); }),
    if (!settings.useAppSounds)
      for (final kind in AlertKind.values)
        ListTile(dense: true, leading: const Icon(Icons.music_note_outlined),
          title: Text('Customize ${kind.name == 'videoCall' ? 'video call' : kind.name} sound'),
          subtitle: Text(settings.soundPaths[kind.name]?.split(Platform.pathSeparator).last ?? 'Using application default'),
          trailing: IconButton(icon: const Icon(Icons.folder_open), onPressed: () => _pickTone(kind)),
          onTap: () => _pickTone(kind)),
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
        if (incomingCall) {
          _incomingDialogContext = context;
          if (_pendingIncomingDecision != null) _flushIncomingDecision();
        }
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
    _callMinimized = false;
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

  Widget _myAvatar({double radius = 15}) {
    final file = settings.avatarPath.isNotEmpty ? File(settings.avatarPath) : null;
    return CircleAvatar(radius: radius,
      backgroundColor: settings.accent.withValues(alpha: 0.16),
      backgroundImage: file != null && file.existsSync() ? FileImage(file) : null,
      child: file == null || !file.existsSync()
        ? Icon(Icons.person, color: settings.accent, size: radius * 1.2) : null);
  }

  Widget _title() => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
    color: settings.accent,
    child: SafeArea(bottom: false, child: Row(children: [
      _myAvatar(radius: 15), const SizedBox(width: 9),
      const Expanded(child: Text('LAN Messenger',
          maxLines: 1, overflow: TextOverflow.ellipsis,
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white))),
      IconButton(icon: const Icon(Icons.folder_outlined, color: Colors.white, size: 21),
          tooltip: 'Received files', onPressed: _viewReceived),
      IconButton(icon: const Icon(Icons.settings_outlined, color: Colors.white, size: 21),
          tooltip: 'Settings', onPressed: () => setState(() {
            showSettings = true; selected = null; showReceived = false;
          })),
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
            return ListTile(minVerticalPadding: 8,
              leading: CircleAvatar(radius: 23, child: Text(p.name.characters.first.toUpperCase(),
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

  Widget _attachmentBubble(ChatMessage message) => InlineAttachment(
    key: ValueKey(message.id), path: message.filePath,
    name: message.text, size: message.fileSize,
    openExternally: () => _openAttachment(message.filePath));

  Widget _chat() {
    final p = node?.peers[selected!.id] ?? selected!;
    final entries = chats[p.id] ?? [];
    final ongoing = transfers.values.where((t) => t.peerId == p.id &&
        (!t.finished || t.error != null)).toList();
    return Column(children: [
      ListTile(contentPadding: const EdgeInsets.symmetric(horizontal: 10),
        leading: IconButton(icon: const Icon(Icons.arrow_back, size: 28),
          onPressed: () => setState(() => selected = null)),
        title: Text(p.name, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
        subtitle: Text(node?.isOnline(p) == true ? 'Online • Local network' :
            'Offline • Waiting for this device'),
        trailing: intercom?.talkingTo?.id == p.id
          ? IconButton(tooltip: 'End call', onPressed: () => intercom?.hangUp(),
              icon: const Icon(Icons.call_end, color: Colors.red, size: 30))
          : Row(mainAxisSize: MainAxisSize.min, children: [
              IconButton(tooltip: 'Voice call', onPressed: node?.isOnline(p) != true
                  ? null : () => _startCall(),
                icon: const Icon(Icons.call_rounded, color: Color(0xff1a8c62), size: 29)),
              PopupMenuButton<int>(tooltip: 'Conversation theme', icon: const Icon(Icons.palette_outlined, size: 22),
                itemBuilder: (_) => _swatches.map((v) => PopupMenuItem<int>(value: v,
                    child: Row(children: [CircleAvatar(radius: 9, backgroundColor: Color(v)),
                      const SizedBox(width: 8), const Text('Thread theme')]))).toList(),
                onSelected: (v) { settings.threadAccents[p.id] = v; unawaited(_saveSettings()); }),
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
                color: msg.outgoing ? settings.threadAccent(p.id).withValues(alpha: 0.17) : Colors.white),
              child: msg.kind == 'file' ? _attachmentBubble(msg) :
                Text(msg.text, style: TextStyle(fontSize: 18 * settings.fontScale,
                    fontFamily: settings.fontFamily == 'Default' ? null : (settings.fontFamily == 'Serif' ? 'serif' : 'monospace'))))); 
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

  Future<void> _switchCamera() async {
    try { await intercom?.switchCamera(); }
    catch (e) { _toast('Camera switching unavailable: $e'); }
  }

  Future<void> _toggleScreenShare() async {
    final call = intercom;
    if (call == null) return;
    try {
      if (call.sharingScreen) {
        await call.stopScreenShare();
      } else {
        await call.startScreenShare();
      }
    } catch (e) {
      _toast('Screen share could not start: $e');
    }
  }

  Widget _miniCall() {
    final call = intercom!;
    final width = MediaQuery.sizeOf(context).width;
    final height = MediaQuery.sizeOf(context).height;
    return Positioned(
      left: _miniCallPosition.dx.clamp(0.0, (width - 195).clamp(0.0, width)),
      top: _miniCallPosition.dy.clamp(0.0, (height - 145).clamp(0.0, height)),
      child: GestureDetector(
        onPanUpdate: (d) => setState(() {
          _miniCallPosition += d.delta;
        }),
        child: Material(
          elevation: 10, borderRadius: BorderRadius.circular(14),
          color: const Color(0xff102b4e),
          child: SizedBox(width: 190, height: 116, child: Stack(children: [
            Positioned.fill(child: call.video && call.remoteRenderer != null
              ? ClipRRect(borderRadius: BorderRadius.circular(14),
                child: RTCVideoView(call.remoteRenderer!,
                  objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitContain))
              : Center(child: Text(call.talkingTo?.name ?? 'Connected',
                  style: const TextStyle(color: Colors.white)))),
            Positioned(top: 0, right: 0, child: IconButton(
              tooltip: 'Expand call', color: Colors.white,
              icon: const Icon(Icons.open_in_full),
              onPressed: () => setState(() => _callMinimized = false))),
            Positioned(bottom: 0, right: 0, child: IconButton(
              tooltip: 'End call', color: Colors.redAccent,
              icon: const Icon(Icons.call_end),
              onPressed: () => call.hangUp())),
            const Positioned(bottom: 9, left: 9,
              child: Icon(Icons.drag_indicator, size: 16, color: Colors.white70)),
          ])),
        ),
      ),
    );
  }

  Widget _activeCall() {
    final call = intercom!;
    return Material(
      color: const Color(0xff102b4e),
      child: SafeArea(child: OrientationBuilder(builder: (context, orientation) {
        final windowSize = MediaQuery.sizeOf(context);
        final remoteWidth = call.remoteRenderer?.videoWidth ?? 0;
        final remoteHeight = call.remoteRenderer?.videoHeight ?? 0;
        // Use frame dimensions from WebRTC: portrait vs landscape changes as
        // the remote device rotates. fitContain avoids cropping either case.
        final sourceRatio = remoteWidth > 0 && remoteHeight > 0
            ? remoteWidth / remoteHeight
            : orientation == Orientation.landscape ? 16 / 9 : 9 / 16;
        final previewWidth = windowSize.width < 460 ? 105.0 : 148.0;
        final previewHeight = previewWidth * 0.82;
        return Column(children: [
          Row(children: [
            IconButton(tooltip: 'Minimize; call stays connected',
              color: Colors.white,
              icon: const Icon(Icons.picture_in_picture_alt_rounded),
              onPressed: () => setState(() => _callMinimized = true)),
            Expanded(child: Column(children: [
              Text(call.talkingTo?.name ?? 'Call',
                maxLines: 1, overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 19, color: Colors.white,
                    fontWeight: FontWeight.bold)),
              Text(call.sharingScreen ? 'Sharing your screen • Local LAN' :
                call.connecting ? 'Connecting…' : 'Connected • Local LAN',
                style: const TextStyle(fontSize: 12, color: Colors.white70)),
            ])),
            IconButton(tooltip: 'End call', color: Colors.redAccent,
              icon: const Icon(Icons.call_end_rounded),
              onPressed: () => call.hangUp()),
          ]),
          Expanded(child: call.video ? LayoutBuilder(builder: (context, size) {
            return Stack(children: [
              Positioned.fill(child: RemoteControlSurface(
                enabled: call.remoteControlActive && call.peerSharingScreen,
                mode: _controlMode,
                sourceRatio: sourceRatio,
                onInput: (action, x, y, wheel) =>
                    unawaited(call.sendRemoteInput(action, x, y, wheel)),
                child: Center(child: AspectRatio(
                  aspectRatio: sourceRatio,
                  child: call.remoteRenderer != null
                      ? RTCVideoView(call.remoteRenderer!,
                          objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitContain)
                      : const Center(child: Icon(Icons.videocam,
                          color: Colors.white54, size: 70)))))),
              if (call.localRenderer != null)
                Positioned(
                  left: _videoPosition.dx.clamp(0.0,
                    (size.maxWidth - previewWidth).clamp(0.0, size.maxWidth)),
                  top: _videoPosition.dy.clamp(0.0,
                    (size.maxHeight - previewHeight).clamp(0.0, size.maxHeight)),
                  width: previewWidth, height: previewHeight,
                  child: GestureDetector(
                    onPanUpdate: (delta) => setState(() {
                      _videoPosition += delta.delta;
                    }),
                    onDoubleTap: call.canSwitchCamera
                        ? () => unawaited(_switchCamera()) : null,
                    child: DecoratedBox(
                      decoration: BoxDecoration(color: Colors.black,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: Colors.white54, width: 1)),
                      child: ClipRRect(borderRadius: BorderRadius.circular(14),
                        child: RTCVideoView(call.localRenderer!, mirror: !call.sharingScreen,
                          objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitContain)),
                    ),
                  ),
                ),
              if (call.remoteControlActive)
                const Positioned(top: 9, left: 9, child: DecoratedBox(
                  decoration: BoxDecoration(color: Colors.teal, borderRadius: BorderRadius.all(Radius.circular(6))),
                  child: Padding(padding: EdgeInsets.all(6), child:
                    Text('REMOTE CONTROL ACTIVE', style: TextStyle(
                      fontSize: 11, color: Colors.white))))),
              if (call.sharingScreen)
                const Positioned(bottom: 12, left: 12, child: DecoratedBox(
                  decoration: BoxDecoration(color: Colors.red, borderRadius: BorderRadius.all(Radius.circular(6))),
                  child: Padding(padding: EdgeInsets.all(6),
                    child: Text('SCREEN SHARING • TAP TO STOP BELOW',
                      style: TextStyle(color: Colors.white, fontSize: 11))))),
            ]);
          }) : const Center(child: Icon(Icons.call,
            color: Colors.white70, size: 100))),
          Padding(padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 6),
            child: Wrap(alignment: WrapAlignment.center, spacing: 10, runSpacing: 6,
              children: [
                IconButton.filledTonal(tooltip: call.muted ? 'Unmute' : 'Mute',
                  onPressed: () => call.setMuted(!call.muted),
                  icon: Icon(call.muted ? Icons.mic_off : Icons.mic)),
                if (call.video && call.canSwitchCamera)
                  IconButton.filledTonal(tooltip: 'Switch camera (also double tap preview)',
                    onPressed: () => unawaited(_switchCamera()),
                    icon: const Icon(Icons.flip_camera_android_rounded)),
                if (call.video && call.remoteControlActive && call.peerSharingScreen)
                  PopupMenuButton<ControlInputMode>(
                    tooltip: 'Choose touch control mode',
                    initialValue: _controlMode,
                    icon: const Icon(Icons.touch_app, color: Colors.white),
                    onSelected: (mode) => setState(() => _controlMode = mode),
                    itemBuilder: (_) => [
                      for (final mode in ControlInputMode.values)
                        PopupMenuItem(value: mode, child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(mode.title, style: const TextStyle(fontWeight: FontWeight.bold)),
                            Text(mode.hint, style: const TextStyle(fontSize: 11)),
                          ])),
                    ],
                  ),
                if (call.video && call.peerSharingScreen && !call.remoteControlActive)
                  IconButton.filledTonal(tooltip: 'Ask permission to control the shared screen',
                    onPressed: () async {
                      try { await call.requestRemoteControl(); }
                      catch (e) { _toast('Control request failed: $e'); }
                    },
                    icon: const Icon(Icons.touch_app_outlined)),
                if (call.sharingScreen && call.remoteControlApproved)
                  IconButton.filled(tooltip: 'Revoke remote control now',
                    style: IconButton.styleFrom(backgroundColor: Colors.deepOrange),
                    onPressed: () => unawaited(call.revokeRemoteControl()),
                    icon: const Icon(Icons.gpp_bad)),
                if (call.video)
                  IconButton.filledTonal(
                    tooltip: call.sharingScreen ? 'Stop screen sharing' : 'Share my screen',
                    onPressed: () => unawaited(_toggleScreenShare()),
                    icon: Icon(call.sharingScreen ? Icons.stop_screen_share :
                        Icons.screen_share_rounded)),
                IconButton.filled(tooltip: 'End call',
                  style: IconButton.styleFrom(backgroundColor: Colors.red),
                  onPressed: () => call.hangUp(),
                  icon: const Icon(Icons.call_end)),
              ])),
        ]);
      })),
    );
  }

  @override
  Widget build(BuildContext context) => Theme(
    data: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: settings.accent),
      useMaterial3: true, scaffoldBackgroundColor: const Color(0xfff7f9fd)),
    child: Stack(children: [
    Scaffold(body: Column(children: [
    _title(),
    if (error != null) Padding(padding: const EdgeInsets.all(12), child: Text(error!,
        style: const TextStyle(color: Colors.red))),
    Expanded(child: showSettings ? _settingsPanel() : showReceived ? _files() :
      selected == null ? _deviceList() : _chat()),
  ])),
    if (intercom?.talkingTo != null && !_incomingDialogOpen)
      _callMinimized ? _miniCall() : Positioned.fill(child: _activeCall()),
  ]));

  @override
  void dispose() {
    unawaited(intercom?.hangUp(notify: false) ?? Future<void>.value());
    unawaited(node?.dispose() ?? Future<void>.value());
    unawaited(alerts.dispose());
    if (Platform.isAndroid) _notifications.setMethodCallHandler(null);
    unawaited(_dismissNativeIncoming());
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