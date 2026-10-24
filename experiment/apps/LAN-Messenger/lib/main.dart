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
import 'src/group_rooms.dart';
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

class _HomePageState extends State<HomePage> with wm.WindowListener, tray.TrayListener, WidgetsBindingObserver {
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
  GroupCoordinator? groups;
  String? selectedGroupId;
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
  Offset _incomingPopupPosition = const Offset(16, 55);
  bool _incomingDialogOpen = false;
  BuildContext? _incomingDialogContext;
  bool? _pendingIncomingDecision;
  Completer<bool>? _incomingAnswer;
  Peer? _incomingPeer;
  bool _incomingVideo = false;
  bool _nativeIncomingAvailable = false;
  bool _androidForeground = true;
  bool _incomingBackground = false;
  bool _presentingCall = false;
  bool _androidInPip = false;
  String? _activeCallUiId;
  bool? _lastNativeMuted;
  bool _compactWindowsVideo = false;
  bool _restoringCompactWindow = false;
  Size? _normalWindowSize;
  Offset? _normalWindowPosition;
  bool _normalWindowWasVisible = true;
  bool _normalWindowWasMinimized = false;
  List<File> received = [];
  Future<void> _historyQueue = Future<void>.value();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    if (Platform.isAndroid) {
      _notifications.setMethodCallHandler(_handleNativeCallAction);
    }
    if (Platform.isWindows) {
      _desktopCalls.setMethodCallHandler(_handleDesktopCallAction);
    }
    unawaited(_initialize());
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _androidForeground = state == AppLifecycleState.resumed;
    if (mounted && Platform.isAndroid) setState(() {});
  }

  Future<bool> _isDesktopBackground() async {
    if (!Platform.isWindows) return false;
    try {
      return !(await wm.windowManager.isVisible()) ||
          await wm.windowManager.isMinimized();
    } catch (_) { return false; }
  }

  Future<dynamic> _handleNativeCallAction(MethodCall call) async {
    if (!mounted) return;
    if (call.method == 'pipState') {
      if (mounted) setState(() => _androidInPip =
          call.arguments is Map && (call.arguments as Map)['active'] == true);
      return;
    }
    if (call.method != 'callAction') return;
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
    if (intercom?.callId != id || intercom?.talkingTo?.id != peer.id) return;
    final args = {
      'caller': peer.name, 'callId': id,
      'video': video, 'muted': intercom?.muted ?? false,
    };
    _activeCallUiId = id;
    _lastNativeMuted = intercom?.muted;
    if (Platform.isAndroid) {
      try {
        await _notifications.invokeMethod<void>('configurePip', args);
        await _notifications.invokeMethod<bool>('ongoing', args);
      } catch (_) {}
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
      _normalWindowWasMinimized = await wm.windowManager.isMinimized();
      if (_normalWindowWasMinimized) {
        // Native SW_SHOWNOACTIVATE restores the minimized window without
        // stealing focus from the PC user who answered from the toast.
        await _desktopCalls.invokeMethod<bool>('restoreMainInactive');
      }
      _normalWindowSize = await wm.windowManager.getSize();
      _normalWindowPosition = await wm.windowManager.getPosition();
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
      if (forceOpen) {
        await wm.windowManager.show();
        await wm.windowManager.focus();
      } else if (_normalWindowWasMinimized) {
        await wm.windowManager.minimize();
      } else if (_normalWindowWasVisible) {
        await wm.windowManager.show(inactive: true);
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

  Future<void> _enterAndroidPip() async {
    if (!Platform.isAndroid || intercom?.video != true ||
        intercom?.connecting == true || intercom?.callId == null) return;
    try {
      final result = await _notifications.invokeMethod<bool>('enterPip');
      if (result != true) _toast('System picture-in-picture is unavailable.');
    } catch (e) {
      _toast('Picture-in-picture failed: $e');
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
    if (Platform.isAndroid) {
      try {
        await _notifications.invokeMethod<void>('configurePip',
            {'callId': '', 'video': false, 'muted': false});
      } catch (_) {}
    }
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
      final group = GroupCoordinator(n);
      group.onChanged = () { if (mounted) setState(() {}); };
      group.onCallInvite = (room, inviter, video) async {
        if (!mounted || inter.talkingTo != null) return false;
        return _ask(title: video ? 'Join group video call?' : 'Join group voice call?',
          detail: '${inviter.name} invited you to ${room.name} (${room.members.length} devices). '
              'Only accept from trusted LAN devices.',
          allowText: 'Join call');
      };
      await group.load();
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
      n.onSignal = (peer, data) => unawaited(() async {
        if (await group.incoming(peer, data)) return;
        await inter.incomingSignal(peer, data);
      }());
      inter.onChanged = () {
        if (!mounted) return;
        // Present the ongoing call only after media setup/SDP negotiation
        // succeeds. Showing native windows inside the incoming-offer finally
        // block raced WebRTC initialization and caused answer regressions.
        final readyId = inter.callId;
        final readyPeer = inter.talkingTo;
        if (!_incomingDialogOpen && !_presentingCall && !inter.connecting &&
            readyId != null && readyPeer != null && _activeCallUiId != readyId) {
          _presentingCall = true;
          unawaited(() async {
            try {
              if (_incomingBackground) {
                await _showOngoingCall(readyPeer, readyId, inter.video);
              } else if (mounted) {
                _activeCallUiId = readyId;
                _lastNativeMuted = inter.muted;
                setState(() => _callMinimized = false);
              }
            } catch (e) {
              if (mounted) setState(() => error = 'Call UI error: $e');
            } finally {
              _presentingCall = false;
            }
          }());
        }
        if (_incomingDialogOpen && inter.talkingTo == null) {
          _resolveIncomingDialog(false);
        }
        if (_activeCallUiId != null && inter.talkingTo == null) {
          _activeCallUiId = null;
          _lastNativeMuted = null;
          unawaited(_endCallPresentation());
        } else if (_incomingBackground && _activeCallUiId == inter.callId &&
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
        _incomingBackground = Platform.isAndroid
            ? !_androidForeground : await _isDesktopBackground();
        _callMinimized = _incomingBackground;
        setState(() { selected = peer; showReceived = false; });
        // Never focus or restore the Windows app on an inbound call.
        // Android uses a system CallStyle heads-up notification with actions.
        if (Platform.isWindows) {
          unawaited(alerts.ring(incomingVideo
              ? AlertKind.videoCall : AlertKind.call));
          _nativeIncomingAvailable = _incomingBackground &&
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
          _nativeIncomingAvailable = _incomingBackground &&
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
          // Never create a video viewer here. Negotiation and media acquisition
          // begin only AFTER this incoming callback returns to Intercom.
          if (!accepted) await _dismissDesktopCall();
          if (mounted) setState(() {});
        }
      };
      await n.start();
      if (mounted) setState(() { node = n; intercom = inter; groups = group; });
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
    if (groups?.activeCall != null) {
      _toast('Finish the group call before calling one device.');
      return;
    }
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
            showSettings = true; selected = null; selectedGroupId = null; showReceived = false;
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
      ListTile(leading: const Icon(Icons.group_add),
        title: const Text('New group chat'),
        subtitle: const Text('2–3 other devices • voice and video conferences'),
        onTap: _createGroup),
      if (groups != null)
        for (final room in groups!.rooms.values)
          ListTile(
            leading: const Icon(Icons.groups_2_outlined),
            title: Text(room.name, maxLines: 1,
              overflow: TextOverflow.ellipsis),
            subtitle: Text('${room.members.length} devices • '
              '${room.messages.length} messages'),
            onTap: () => setState(() {
              selectedGroupId = room.id;
              selected = null; showReceived = false;
            }),
          ),
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

  Future<void> _createGroup() async {
    final live = node?.peers.values.where((p) => node!.isOnline(p)).toList() ?? <Peer>[];
    if (live.length < 2) {
      _toast('Connect at least two other devices to create a group.');
      return;
    }
    final name = TextEditingController(text: 'My LAN group');
    final selectedIds = <String>{};
    final accepted = await showDialog<bool>(context: context,
      builder: (dialog) => StatefulBuilder(builder: (context, change) =>
        AlertDialog(title: const Text('Create LAN group'),
          content: SizedBox(width: 390, height: 380,
            child: Column(children: [
              TextField(controller: name, maxLength: 60,
                decoration: const InputDecoration(labelText: 'Group name')),
              const Text('Choose 2–3 other devices. Messages are encrypted for each peer.'),
              Expanded(child: ListView(children: [
                for (final peer in live)
                  CheckboxListTile(title: Text(peer.name), dense: true,
                    value: selectedIds.contains(peer.id),
                    onChanged: (yes) => change(() {
                      if (yes == true && selectedIds.length < 3) {
                        selectedIds.add(peer.id);
                      } else if (yes == false) { selectedIds.remove(peer.id); }
                    })),
              ])),
            ])),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialog, false),
              child: const Text('Cancel')),
            FilledButton(onPressed: selectedIds.length < 2 ? null :
              () => Navigator.pop(dialog, true), child: const Text('Create')),
          ])));
    Future<void>.delayed(const Duration(milliseconds: 550), name.dispose);
    if (accepted != true) return;
    try {
      final members = live.where((p) => selectedIds.contains(p.id)).toList();
      final room = await groups!.create(name.text, members);
      if (mounted) setState(() {
        selectedGroupId = room.id;
        selected = null; showReceived = false;
      });
    } catch (e) { _toast('Group creation failed: $e'); }
  }

  Widget _groupChat(GroupRoom room) {
    final session = groups?.activeCall;
    return Column(children: [
      ListTile(
        leading: IconButton(icon: const Icon(Icons.arrow_back),
          onPressed: () => setState(() => selectedGroupId = null)),
        title: Text(room.name, maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text('${room.members.length} LAN devices • E2E peer encrypted'),
        trailing: Row(mainAxisSize: MainAxisSize.min, children: [
          IconButton(tooltip: 'Group voice call', icon: const Icon(Icons.call),
            onPressed: session != null || intercom?.talkingTo != null
              ? null : () => unawaited(_startGroupCall(room, false))),
          IconButton(tooltip: 'Group video call', icon: const Icon(Icons.videocam),
            onPressed: session != null || intercom?.talkingTo != null
              ? null : () => unawaited(_startGroupCall(room, true))),
        ]),
      ),
      Expanded(child: room.messages.isEmpty
        ? const Center(child: Text('This group has no messages yet.'))
        : ListView.builder(padding: const EdgeInsets.all(12),
          itemCount: room.messages.length,
          itemBuilder: (_, i) {
            final msg = room.messages[i];
            final mine = msg.senderId == node?.identity.id;
            final sender = mine ? 'You' : node?.peers[msg.senderId]?.name ??
                msg.senderId.substring(0, 8);
            return Align(alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
              child: Container(
                constraints: const BoxConstraints(maxWidth: 390),
                padding: const EdgeInsets.symmetric(vertical: 9, horizontal: 14),
                margin: const EdgeInsets.symmetric(vertical: 4),
                decoration: BoxDecoration(
                  color: mine ? const Color(0xffd8ebff) : Colors.white,
                  borderRadius: BorderRadius.circular(15)),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(sender, style: const TextStyle(fontSize: 12,
                    fontWeight: FontWeight.bold)),
                  Text(msg.text),
                ])));
          })),
      SafeArea(top: false, child: Padding(padding: const EdgeInsets.all(10),
        child: Row(children: [
          Expanded(child: TextField(controller: input,
            maxLength: 4000, minLines: 1, maxLines: 3,
            textInputAction: TextInputAction.send,
            onSubmitted: (_) => unawaited(_sendGroupText(room)),
            decoration: const InputDecoration(hintText: 'Message the group',
              counterText: '', border: OutlineInputBorder()))),
          const SizedBox(width: 8),
          IconButton.filled(icon: const Icon(Icons.send),
            onPressed: () => unawaited(_sendGroupText(room))),
        ]))),
    ]);
  }

  Future<void> _sendGroupText(GroupRoom room) async {
    final value = input.text.trim();
    if (value.isEmpty) return;
    try {
      await groups!.sendText(room, value);
      if (mounted) input.clear();
    } catch (e) { _toast('Cannot send group message: $e'); }
  }

  Future<void> _startGroupCall(GroupRoom room, bool video) async {
    if (intercom?.talkingTo != null) {
      _toast('Finish the current call before joining a group.');
      return;
    }
    try { await groups!.startCall(room, video: video); }
    catch (e) { _toast('Group call could not start: $e'); }
  }

  Widget _groupCallUI(GroupMediaCall call) {
    return Material(color: const Color(0xff122744),
      child: SafeArea(child: Column(children: [
        ListTile(title: Text(call.room.name, style: const TextStyle(color: Colors.white)),
          subtitle: Text('Group ${call.video ? "video" : "voice"} • '
            '${call.participantCount} connected/joining',
            style: const TextStyle(color: Colors.white70)),
          trailing: IconButton(tooltip: 'Leave group call',
            color: Colors.redAccent, icon: const Icon(Icons.call_end),
            onPressed: () => unawaited(groups!.endCall()))),
        Expanded(child: call.video
          ? GridView.count(crossAxisCount: 2,
            childAspectRatio: 1.1, children: [
              _groupVideoTile('You', call.localVideo),
              for (final memberId in call.room.members)
                if (memberId != node?.identity.id)
                  _groupVideoTile(node?.peers[memberId]?.name ?? 'Device',
                    call.remoteVideos[memberId]),
            ])
          : Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Icon(Icons.groups, size: 85, color: Colors.white70),
              const SizedBox(height: 20),
              Text('Voice conference • ${call.participantCount}/${call.room.members.length}',
                style: const TextStyle(color: Colors.white, fontSize: 18)),
            ]))),
        Padding(padding: const EdgeInsets.all(12), child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
          IconButton.filledTonal(tooltip: call.muted ? 'Unmute' : 'Mute',
            onPressed: () => unawaited(call.setMuted(!call.muted)),
            icon: Icon(call.muted ? Icons.mic_off : Icons.mic)),
          IconButton.filled(tooltip: 'End group call',
            style: IconButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => unawaited(groups!.endCall()),
            icon: const Icon(Icons.call_end)),
        ])),
      ])));
  }

  Widget _groupVideoTile(String name, RTCVideoRenderer? renderer) =>
    Padding(padding: const EdgeInsets.all(4),
      child: ClipRRect(borderRadius: BorderRadius.circular(11),
        child: Stack(children: [
          Positioned.fill(child: renderer == null
            ? const ColoredBox(color: Colors.black38,
                child: Center(child: Icon(Icons.videocam_off,
                  color: Colors.white70, size: 33)))
            : RTCVideoView(renderer,
                objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitContain)),
          Positioned(bottom: 7, left: 7,
            child: Text(name, style: const TextStyle(color: Colors.white))),
        ])));

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

  Widget _foregroundIncomingCall() {
    final peer = _incomingPeer;
    if (peer == null) return const SizedBox.shrink();
    return Material(color: const Color(0xff102b4e), child: SafeArea(
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        CircleAvatar(radius: 47, backgroundColor: Colors.white24,
          child: Icon(_incomingVideo ? Icons.videocam : Icons.call,
            color: Colors.white, size: 48)),
        const SizedBox(height: 24),
        Text(peer.name, textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 26, color: Colors.white,
            fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Text(_incomingVideo ? 'Incoming video call' : 'Incoming voice call',
          style: const TextStyle(color: Colors.white70, fontSize: 16)),
        const SizedBox(height: 38),
        Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
          FilledButton.icon(onPressed: () => _resolveIncomingDialog(false),
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            icon: const Icon(Icons.call_end), label: const Text('Decline')),
          FilledButton.icon(onPressed: () => _resolveIncomingDialog(true),
            style: FilledButton.styleFrom(backgroundColor: Colors.green),
            icon: const Icon(Icons.call), label: const Text('Answer')),
        ]),
      ])));
  }

  Widget _incomingPopup() {
    final peer = _incomingPeer;
    if (peer == null || !_incomingDialogOpen) {
      return const SizedBox.shrink();
    }
    final size = MediaQuery.sizeOf(context);
    const width = 308.0;
    return Positioned(
      right: _incomingPopupPosition.dx.clamp(4.0, size.width - 24.0),
      top: _incomingPopupPosition.dy.clamp(4.0, size.height - 130.0),
      width: width.clamp(0, size.width - 8.0).toDouble(),
      child: Material(
        elevation: 11, borderRadius: BorderRadius.circular(18),
        color: const Color(0xff132a48),
        child: GestureDetector(
          onPanUpdate: (details) => setState(() {
            _incomingPopupPosition = Offset(
              (_incomingPopupPosition.dx - details.delta.dx).clamp(
                  4.0, size.width - 24.0).toDouble(),
              (_incomingPopupPosition.dy + details.delta.dy).clamp(
                  4.0, size.height - 130.0).toDouble());
          }),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Row(children: [
                const Icon(Icons.call_received, color: Colors.lightBlueAccent),
                const SizedBox(width: 8),
                Expanded(child: Text(peer.name,
                    maxLines: 1, overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.white,
                        fontWeight: FontWeight.bold, fontSize: 16))),
                const Icon(Icons.drag_indicator, color: Colors.white54),
              ]),
              Text(_incomingVideo ? 'Incoming video call' : 'Incoming voice call',
                  style: const TextStyle(color: Colors.white70)),
              const SizedBox(height: 8),
              Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
                FilledButton.icon(
                  style: FilledButton.styleFrom(backgroundColor: Colors.green),
                  onPressed: () => _resolveIncomingDialog(true),
                  icon: const Icon(Icons.call), label: const Text('Answer')),
                FilledButton.icon(
                  style: FilledButton.styleFrom(backgroundColor: Colors.redAccent),
                  onPressed: () => _resolveIncomingDialog(false),
                  icon: const Icon(Icons.call_end), label: const Text('Decline')),
              ]),
            ]),
          ),
        ),
      ),
    );
  }

  Widget _miniCall() {
    final call = intercom!;
    final size = MediaQuery.sizeOf(context);
    const width = 246.0;
    const height = 180.0;
    return Positioned(
      left: _miniCallPosition.dx.clamp(0.0, (size.width - width).clamp(0.0, size.width)).toDouble(),
      top: _miniCallPosition.dy.clamp(0.0, (size.height - height).clamp(0.0, size.height)).toDouble(),
      width: width.clamp(100.0, size.width).toDouble(),
      height: height.clamp(100.0, size.height).toDouble(),
      child: Material(
        elevation: 12, color: const Color(0xff102b4e),
        borderRadius: BorderRadius.circular(14),
        child: Column(children: [
          GestureDetector(
            behavior: HitTestBehavior.opaque,
            onPanUpdate: (d) => setState(() { _miniCallPosition += d.delta; }),
            child: Padding(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
              child: Row(children: [
                const Icon(Icons.drag_indicator, color: Colors.white70, size: 18),
                Expanded(child: Text(call.talkingTo?.name ?? 'In call',
                    maxLines: 1, overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.white, fontSize: 12))),
                Text(call.muted ? 'Muted' : 'Live',
                    style: const TextStyle(color: Colors.white70, fontSize: 11)),
              ])),
          ),
          Expanded(child: ClipRRect(borderRadius: BorderRadius.circular(6),
            child: call.video && call.remoteRenderer != null
              ? RTCVideoView(call.remoteRenderer!,
                  objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitContain)
              : const Center(child: Icon(Icons.graphic_eq,
                  color: Colors.white70, size: 36)))),
          Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
            IconButton(tooltip: call.muted ? 'Unmute microphone' : 'Mute microphone',
              icon: Icon(call.muted ? Icons.mic_off : Icons.mic, color: Colors.white),
              onPressed: () => unawaited(call.setMuted(!call.muted))),
            IconButton(tooltip: 'End call',
              icon: const Icon(Icons.call_end, color: Colors.redAccent),
              onPressed: () => unawaited(call.hangUp())),
            IconButton(tooltip: 'Open conversation thread',
              icon: const Icon(Icons.forum_outlined, color: Colors.white),
              onPressed: () => unawaited(_openCallThread())),
            if (Platform.isAndroid && call.video)
              IconButton(tooltip: 'Float video above other apps',
                icon: const Icon(Icons.picture_in_picture_alt, color: Colors.white),
                onPressed: () => unawaited(_enterAndroidPip())),
            IconButton(tooltip: 'Expand call controls',
              icon: const Icon(Icons.open_in_full, color: Colors.white),
              onPressed: () => setState(() => _callMinimized = false)),
          ]),
        ]),
      ),
    );
  }

  Widget _compactVideoView() {
    final call = intercom;
    return Scaffold(backgroundColor: const Color(0xff102b4e),
      body: SafeArea(child: Column(children: [
        GestureDetector(
          behavior: HitTestBehavior.opaque,
          onPanStart: (_) => unawaited(wm.windowManager.startDragging()),
          child: Padding(padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 8),
            child: Row(children: [
              const Icon(Icons.drag_indicator, color: Colors.white70, size: 20),
              const SizedBox(width: 4),
              Expanded(child: Text(call?.talkingTo?.name ?? 'Video call',
                  maxLines: 1, overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold))),
              IconButton(tooltip: 'Open full conversation',
                icon: const Icon(Icons.open_in_full, color: Colors.white, size: 18),
                onPressed: () => unawaited(_openCallThread())),
            ])),
        ),
        Expanded(child: call?.remoteRenderer == null
          ? const Center(child: Icon(Icons.videocam, size: 48, color: Colors.white54))
          : RTCVideoView(call!.remoteRenderer!,
              objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitContain)),
        Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
          IconButton.filledTonal(tooltip: call?.muted == true ? 'Unmute microphone' : 'Mute microphone',
            onPressed: call == null ? null : () => unawaited(call.setMuted(!call.muted)),
            icon: Icon(call?.muted == true ? Icons.mic_off : Icons.mic)),
          IconButton.filled(tooltip: 'End call',
            style: IconButton.styleFrom(backgroundColor: Colors.red),
            onPressed: call == null ? null : () => unawaited(call.hangUp()),
            icon: const Icon(Icons.call_end)),
          IconButton.filledTonal(tooltip: 'Open thread',
            onPressed: () => unawaited(_openCallThread()),
            icon: const Icon(Icons.forum_outlined)),
        ]),
        const SizedBox(height: 8),
      ])));
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
                if (Platform.isAndroid && call.video)
                  IconButton.filledTonal(
                    tooltip: 'Float call above other apps',
                    onPressed: () => unawaited(_enterAndroidPip()),
                    icon: const Icon(Icons.picture_in_picture_alt)),
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

  Widget _androidPipVideo() {
    final renderer = intercom?.remoteRenderer;
    return Material(color: Colors.black,
      child: Center(child: renderer != null
        ? RTCVideoView(renderer,
            objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitContain)
        : const Icon(Icons.call, size: 50, color: Colors.white)));
  }

  @override
  Widget build(BuildContext context) => Theme(
    data: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: settings.accent),
      useMaterial3: true, scaffoldBackgroundColor: const Color(0xfff7f9fd)),
    child: _compactWindowsVideo
      ? _compactVideoView()
      : Platform.isAndroid && _androidInPip
        ? _androidPipVideo()
        : Stack(children: [
    Scaffold(body: Column(children: [
    _title(),
    if (error != null) Padding(padding: const EdgeInsets.all(12), child: Text(error!,
        style: const TextStyle(color: Colors.red))),
    Expanded(child: showSettings ? _settingsPanel() : showReceived ? _files() :
      selectedGroupId != null && groups?.rooms[selectedGroupId] != null
        ? _groupChat(groups!.rooms[selectedGroupId]!)
        : selected == null ? _deviceList() : _chat()),
  ])),
    if (_incomingDialogOpen && _incomingPeer != null && !_incomingBackground)
      Positioned.fill(child: _foregroundIncomingCall()),
    if (intercom?.talkingTo != null && !_incomingDialogOpen)
      _callMinimized ? _miniCall() : Positioned.fill(child: _activeCall()),
    if (groups?.activeCall != null && groups!.activeCall!.joined)
      Positioned.fill(child: _groupCallUI(groups!.activeCall!)),
  ]));

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    unawaited(intercom?.hangUp(notify: false) ?? Future<void>.value());
    unawaited(groups?.endCall() ?? Future<void>.value());
    unawaited(node?.dispose() ?? Future<void>.value());
    unawaited(alerts.dispose());
    if (Platform.isAndroid) _notifications.setMethodCallHandler(null);
    if (Platform.isWindows) _desktopCalls.setMethodCallHandler(null);
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