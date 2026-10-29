import 'dart:async';
import 'dart:typed_data';
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:crypto/crypto.dart' as hash;
import 'package:flutter/services.dart';
import 'identity.dart';
import 'serial_async_gate.dart';
import 'protocol.dart';
import 'lan_reconnect_policy.dart';
import 'call_peer_watchdog.dart';

class TransferProgress {
  final String id;
  final String peerId;
  final String name;
  final int done;
  final int total;
  final bool incoming;
  final bool finished;
  final String? error;
  final bool waiting;
  const TransferProgress(this.id, this.peerId, this.name, this.done, this.total,
      this.incoming, {this.finished = false, this.error, this.waiting = false});
}

class _ReceiveState {
  final String name;
  final String checksum;
  final int total;
  final File temporary;
  final String senderId;
  int written = 0;
  final SerialAsyncGate writes = SerialAsyncGate();
  _ReceiveState(this.name, this.checksum, this.total, this.temporary, this.senderId);
  int get nextChunk => (written / chunkSize).ceil();
}

class _CompletedIncomingFile {
  final String senderId;
  final String checksum;
  final int bytes;
  _CompletedIncomingFile(this.senderId, this.checksum, this.bytes);
  int get next => (bytes / chunkSize).ceil();
}

class LanNode {
  final Identity identity;
  late final PeerCipher cipher = PeerCipher(identity);
  HttpServer? _server;
  RawDatagramSocket? _udp;
  Timer? _ticker;
  final Map<String, Peer> peers = {};
  final Set<String> _unreachablePeers = {};
  final Set<String> _peerIntroductionsPending = {};
  static const int maxConcurrentPeerIntroductions = 4;
  final Map<String, _ReceiveState> _incoming = {};
  final Set<String> _pendingOfferIds = {};
  final SerialAsyncGate _completionGate = SerialAsyncGate();
  final Map<String, _CompletedIncomingFile> _completedIncoming = {};
  final Set<String> _routedPeerSeeds = {};
  int reconnectGraceSeconds = 60;

  /// Manually configured IPv4 discovery destinations, not a NAT relay.
  /// On separately routed networks both sides still need a return route,
  /// permitted TCP ports and compatible ICE connectivity.
  void setRoutedPeerSeeds(Iterable<String> targets) {
    _routedPeerSeeds.clear();
    for (final target in targets) {
      final ip = LanReconnectPolicy.privateIpv4Seed(target);
      if (ip != null && _routedPeerSeeds.length < 8) {
        _routedPeerSeeds.add(ip);
      }
    }
    announce();
  }

  final Set<String> _seenMessages = {};
  // A peer's identity must outlive a missed UDP announcement. Presence is a
  // separate concept from whether we will authenticate its HTTP requests.
  static const peerOnlineWindow = Duration(seconds: 35);
  bool autoReceiveFiles = true;
  int maxIncomingFileBytes = 512 * 1024 * 1024;
  static const int maxConcurrentIncoming = 4;
  bool _checkingPeers = false;
  bool isOnline(Peer peer) =>
      !_unreachablePeers.contains(peer.id) &&
      DateTime.now().difference(peers[peer.id]?.seen ?? peer.seen) < peerOnlineWindow;
  /// A failed authenticated call heartbeat overrides a stale UDP presence.
  /// The peer identity remains pinned and is reinstated on a valid reply.
  void markPeerUnreachable(Peer peer) {
    if (peers[peer.id]?.key != peer.key) return;
    if (_unreachablePeers.add(peer.id)) onPeersChanged?.call();
  }
  void _markSeen(Peer peer) {
    final old = peers[peer.id];
    if (old == null || old.key != peer.key) return;
    final wasUnreachable = _unreachablePeers.remove(peer.id);
    peers[peer.id] = Peer(id: old.id, name: old.name, key: old.key,
        host: old.host, port: old.port, seen: DateTime.now());
    if (wasUnreachable) onPeersChanged?.call();
  }
  /// Complete one-way UDP discovery using the existing authenticated HTTP
  /// ping. The receiving node can introduce its identity to a sender that
  /// never received the reverse UDP multicast or unicast packet.
  ///
  /// Only already-parsed, pinned discovery peers are eligible; limit parallel
  /// first-contact connections so unsolicited LAN announcements cannot create
  /// an unbounded burst of outbound TCP attempts.
  Future<bool> introduceDiscoveredPeer(Peer peer) async {
    if (_server == null || peers[peer.id]?.key != peer.key ||
        peers[peer.id]?.host != peer.host ||
        _peerIntroductionsPending.contains(peer.id) ||
        _peerIntroductionsPending.length >= maxConcurrentPeerIntroductions) {
      return false;
    }
    _peerIntroductionsPending.add(peer.id);
    try {
      final reply = await _post(peer, '/v1/event',
          utf8.encode(jsonEncode({'kind': 'ping'})),
          timeout: const Duration(seconds: 3));
      return reply['ok'] == true;
    } catch (_) {
      // UDP discovery remains available even when the remote TCP port is
      // blocked by an asymmetric emulator/router/firewall path.
      return false;
    } finally {
      _peerIntroductionsPending.remove(peer.id);
    }
  }

  Future<void> _checkPeerReachability() async {
    if (_checkingPeers) return;
    _checkingPeers = true;
    try {
      final old = peers.values.where((p) =>
          DateTime.now().difference(p.seen) > const Duration(seconds: 9)).toList();
      await Future.wait(old.take(16).map((peer) async {
        try {
          final reply = await _event(peer, {'kind': 'ping'}).timeout(
              const Duration(seconds: 3));
          if (reply['ok'] == true) _markSeen(peer);
        } catch (_) { /* Stale peers remain known, but appear offline. */ }
      }));
    } finally { _checkingPeers = false; }
  }
  final HttpClient _http = HttpClient()..connectionTimeout = const Duration(seconds: 6);

  void Function()? onPeersChanged;
  void Function(Peer, ChatMessage)? onChat;
  void Function(Peer, Map<String, dynamic>)? onSignal;
  bool Function(Peer, String sessionId)? onCallProbe;
  void Function(TransferProgress)? onProgress;
  Timer? _progressPulse;
  final Map<String, TransferProgress> _progressPending = {};
  void _reportProgress(TransferProgress p) {
    if (p.finished || p.error != null) {
      _progressPending.remove(p.id);
      onProgress?.call(p);
      return;
    }
    _progressPending[p.id] = p;
    _progressPulse ??= Timer(const Duration(milliseconds: 250), () {
      _progressPulse = null;
      final batch = List<TransferProgress>.of(_progressPending.values);
      _progressPending.clear();
      for (final progress in batch) { onProgress?.call(progress); }
    });
  }
  Future<bool> Function(Peer, String, int)? onFileOffer;
  final Directory? storageDirectory;
  LanNode(this.identity, {this.storageDirectory});
  Future<Directory> _storage() async {
    final override = storageDirectory;
    if (override != null) return override;
    return Identity.appDirectory();
  }

  static const _wifiMulticast = MethodChannel('lan_messenger/multicast');

  /// Stable TCP ingress simplifies an explicit firewall rule for a manually
  /// routed subnet. The UDP discovery port remains discoveryPort (39823).
  /// A second local process may use an ephemeral port, which is advertised
  /// honestly in discovery rather than pretending that 39824 is reachable.
  static const int preferredListenPort = 39824;
  bool get usingPreferredListenPort => _server?.port == preferredListenPort;

  Future<void> start() async {
    try { await _wifiMulticast.invokeMethod<void>('acquire'); } catch (_) {}
    try {
      _server = await HttpServer.bind(
          InternetAddress.anyIPv4, preferredListenPort);
    } on SocketException {
      // Keep local-LAN operation available if another local app owns 39824;
      // discovery publishes the ACTUAL bound port in every announcement.
      _server = await HttpServer.bind(InternetAddress.anyIPv4, 0);
    }
    _server!.listen(_serve, onError: (_) {});
    try {
      _udp = await RawDatagramSocket.bind(InternetAddress.anyIPv4, discoveryPort,
          reuseAddress: true);
      _udp!.broadcastEnabled = true;
      try { _udp!.joinMulticast(InternetAddress(multicastIp)); } catch (_) {}
      _udp!.listen((event) {
        if (event != RawSocketEvent.read) return;
        Datagram? packet;
        while ((packet = _udp!.receive()) != null) {
          _handleAnnouncement(packet!);
        }
      }, onError: (_) {});
    } on SocketException {
      // UI remains open and reports discovery failure instead of crashing.
    }
    announce();
    _ticker = Timer.periodic(const Duration(seconds: 4), (_) {
      announce();
      // Unicast announcements also reach a previously discovered peer if the
      // router temporarily stops forwarding multicast or broadcast packets.
      for (final peer in peers.values) {
        try {
          final body = utf8.encode(announcement(identity.id,
              identity.displayName, identity.publicKeyB64, _server!.port));
          _udp?.send(body, InternetAddress(peer.host), discoveryPort);
        } catch (_) {}
      }
      unawaited(_checkPeerReachability());
      onPeersChanged?.call();
    });
  }

  bool get discoveryReady => _udp != null;
  int get listenPort => _server?.port ?? 0;

  void announce() {
    if (_udp == null || _server == null) return;
    final message = utf8.encode(announcement(identity.id, identity.displayName,
        identity.publicKeyB64, _server!.port));
    _udp!.send(message, InternetAddress(multicastIp), discoveryPort);
    _udp!.send(message, InternetAddress('255.255.255.255'), discoveryPort);
    // Unicast packets can cross ordinary L3 subnets when firewall/router
    // policy permits; multicast generally cannot. No brute force scanning.
    for (final ip in _routedPeerSeeds) {
      _udp!.send(message, InternetAddress(ip), discoveryPort);
    }
  }

  void _handleAnnouncement(Datagram packet) {
    if (packet.data.length > 1024) return;
    try {
      final decoded = jsonDecode(utf8.decode(packet.data));
      if (decoded is! Map<String, dynamic> || decoded['app'] != 'lan-messenger') return;
      final peer = Peer.fromDiscovery(decoded, packet.address.address);
      if (peer == null || peer.id == identity.id) return;
      final old = peers[peer.id];
      // Never allow a different public key to replace a pinned identity.
      if (old != null && old.key != peer.key) return;
      peers[peer.id] = peer;
      if (old == null || old.host != peer.host || old.port != peer.port ||
          old.name != peer.name) {
        onPeersChanged?.call();
        if (old == null && _udp != null) {
          // Respond once to a new unicast discovery sender using its NAT
          // source port, instead of assuming its source UDP port is 39823.
          try {
            _udp!.send(utf8.encode(announcement(identity.id,
                identity.displayName, identity.publicKeyB64, _server!.port)),
                packet.address, packet.port);
          } catch (_) {}
          // If the sender cannot hear our reverse UDP packets, an encrypted
          // first-contact ping lets it learn us from the authenticated request.
          unawaited(introduceDiscoveredPeer(peer));
        }
      }
    } catch (_) { /* Untrusted malformed multicast is ignored. */ }
  }

  Future<void> _serve(HttpRequest request) async {
    request.response.headers.set('cache-control', 'no-store');
    try {
      if (request.method != 'POST' ||
          (request.uri.path != '/v1/event' && request.uri.path != '/v1/chunk')) {
        request.response.statusCode = HttpStatus.notFound;
        return;
      }
      if (request.contentLength > 180000) {
        request.response.statusCode = HttpStatus.requestEntityTooLarge;
        return;
      }
      final builder = BytesBuilder();
      await for (final chunk in request) {
        if (builder.length + chunk.length > 180000) {
          throw const FormatException('Oversize payload');
        }
        builder.add(chunk);
      }
      final data = utf8.decode(builder.takeBytes());
      final packet = jsonDecode(data) as Map<String, dynamic>;
      final senderId = PeerCipher.senderId(packet);
      final known = peers[senderId];
      if (known != null && known.key != packet['from']) {
        request.response.statusCode = HttpStatus.forbidden;
        return;
      }
      // Authenticate first. A lost/asymmetric multicast announcement must not
      // cause HTTP 403 for a peer with a valid encrypted request. The reply
      // identity is a first-contact introduction, not a verified real name.
      final plaintext = await cipher.open(packet);
      var peer = known;
      if (peer == null) {
        final port = packet['replyPort'];
        final name = packet['replyName'];
        final remoteAddress = request.connectionInfo?.remoteAddress.address;
        if (port is! int || port < 1 || port > 65535 ||
            name is! String || name.trim().isEmpty || name.length > 80 ||
            remoteAddress == null || packet['from'] is! String) {
          request.response.statusCode = HttpStatus.forbidden;
          return;
        }
        peer = Peer(id: senderId, key: packet['from'] as String,
            host: remoteAddress, port: port, name: name, seen: DateTime.now());
        peers[senderId] = peer;
        onPeersChanged?.call();
      }
      _markSeen(peer);
      Map<String, dynamic> output;
      if (request.uri.path == '/v1/chunk') {
        output = await _receiveChunk(peer, plaintext);
      } else {
        final event = jsonDecode(utf8.decode(plaintext)) as Map<String, dynamic>;
        output = await _handleEvent(peer, event);
      }
      request.response.headers.contentType = ContentType.json;
      request.response.write(jsonEncode(await cipher.seal(peer.key,
          utf8.encode(jsonEncode(output)))));
    } catch (_) {
      request.response.statusCode = HttpStatus.badRequest;
    } finally {
      await request.response.close();
    }
  }

  Future<Map<String, dynamic>> _post(Peer peer, String path, List<int> body,
      {Duration timeout = const Duration(seconds: 15)}) async {
    final packet = await cipher.seal(peer.key, body);
    // Reply address lets new peers join even when UDP discovery is one-way.
    packet['replyName'] = identity.displayName;
    packet['replyPort'] = _server?.port;
    final request = await _http.postUrl(peer.uri(path)).timeout(timeout);
    request.headers.contentType = ContentType.json;
    request.add(utf8.encode(jsonEncode(packet)));
    final response = await request.close().timeout(timeout);
    final raw = await utf8.decoder.bind(response).join().timeout(timeout);
    if (response.statusCode != HttpStatus.ok) {
      throw HttpException('Peer rejected request: ${response.statusCode}');
    }
    final reply = jsonDecode(raw) as Map<String, dynamic>;
    if (reply['from'] != peer.key) throw const FormatException('Untrusted response');
    final opened = jsonDecode(utf8.decode(await cipher.open(reply))) as Map<String, dynamic>;
    _markSeen(peer);
    return opened;
  }

  Future<Map<String, dynamic>> _event(Peer peer, Map<String, dynamic> event) =>
      _post(peer, '/v1/event', utf8.encode(jsonEncode(event)),
        timeout: event['kind'] == 'file-offer'
            ? const Duration(minutes: 3) : const Duration(seconds: 15));

  /// A two-way encrypted call-specific probe. Modern peers can prove that
  /// THIS call ID remains active; an older v0.3.2 peer falls back to encrypted
  /// ping for compatibility, with weaker session-liveness guarantees.
  Future<CallProbeResult> probeCall(Peer peer, String callId) async {
    try {
      final probe = await _post(peer, '/v1/event',
          utf8.encode(jsonEncode({'kind': 'call-probe', 'callId': callId})),
          timeout: const Duration(seconds: 3));
      if (probe['active'] is bool) {
        return probe['active'] == true
            ? CallProbeResult.active : CallProbeResult.ended;
      }
      // Legacy versions reply {'ok': false} for unknown 'call-probe'.
      // Do not break voice/video across mixed preview versions.
      final legacy = await _post(peer, '/v1/event',
          utf8.encode(jsonEncode({'kind': 'ping'})),
          timeout: const Duration(seconds: 3));
      return legacy['ok'] == true
          ? CallProbeResult.active : CallProbeResult.unreachable;
    } catch (_) {
      return CallProbeResult.unreachable;
    }
  }

  Future<void> sendMessage(Peer peer, String body) async {
    if (body.trim().isEmpty || body.length > 4000) throw ArgumentError('Invalid message');
    final id = randomId();
    final result = await _event(peer, {'kind': 'message', 'id': id, 'text': body,
      'time': DateTime.now().toUtc().toIso8601String()});
    if (result['ok'] != true) throw StateError('Message not accepted');
    onChat?.call(peer, ChatMessage(id: id, peerId: peer.id, text: body,
        outgoing: true, time: DateTime.now()));
  }

  Future<void> signal(Peer peer, Map<String, dynamic> payload) async {
    // Diagnostic only: no peer IDs, keys, SDP, or other private data in logs.
    if (payload['type'] == 'offer') {
      print('LAN_CALL_TRACE outgoing_offer_post_started');
    }
    final result = await _event(peer, {'kind': 'signal', ...payload});
    if (result['ok'] != true) throw StateError('Signaling unavailable');
    if (payload['type'] == 'offer') {
      print('LAN_CALL_TRACE outgoing_offer_http_accepted');
    }
  }

  Future<Map<String, dynamic>> _handleEvent(Peer peer, Map<String, dynamic> event) async {
    switch (event['kind']) {
      case 'ping':
        return {'ok': true};
      case 'call-probe':
        final id = event['callId'];
        return {'ok': true, 'active':
          id is String && id.isNotEmpty && id.length <= 64 &&
          onCallProbe?.call(peer, id) == true};
      case 'message':
        final text = event['text'];
        final id = event['id'];
        if (text is! String || text.isEmpty || text.length > 4000 ||
            id is! String || id.length > 100 || id.isEmpty) return {'ok': false};
        if (_seenMessages.add('${peer.id}/$id')) {
          if (_seenMessages.length > 10000) _seenMessages.clear();
          onChat?.call(peer, ChatMessage(id: id, peerId: peer.id,
              text: text, outgoing: false, time: DateTime.now()));
        }
        return {'ok': true};
      case 'signal':
        if (jsonEncode(event).length > 28000) return {'ok': false};
        if (event['type'] == 'offer') {
          print('LAN_CALL_TRACE inbound_offer_http_authenticated');
        }
        onSignal?.call(peer, event);
        return {'ok': true};
      case 'file-offer':
        return _acceptOffer(peer, event);
      case 'file-status':
        final transfer = _incoming[event['id']];
        if (transfer != null && transfer.senderId == peer.id) {
          return {'ok': true, 'next': transfer.nextChunk};
        }
        final receipt = _completedIncoming[event['id']];
        if (receipt != null && receipt.senderId == peer.id) {
          return {'ok': true, 'done': true, 'next': receipt.next};
        }
        return {'ok': false};
      default:
        return {'ok': false};
    }
  }

  Future<Map<String, dynamic>> _acceptOffer(Peer peer, Map<String, dynamic> data) async {
    final id = data['id'], name = data['name'], total = data['size'], sha = data['sha256'];
    if (id is! String || !RegExp(r'^[a-f0-9]{32}$').hasMatch(id) ||
        name is! String || name.isEmpty || name.length > 255 ||
        total is! int || total < 0 || total > maxIncomingFileBytes ||
        sha is! String || !RegExp(r'^[a-f0-9]{64}$').hasMatch(sha)) return {'ok': false, 'reason': 'invalid or over configured size limit'};
    if (_incoming.containsKey(id)) {
      final previous = _incoming[id]!;
      final identicalOffer = previous.senderId == peer.id &&
          previous.checksum == sha && previous.total == total &&
          previous.name == safeFileName(name);
      return {'ok': identicalOffer,
        if (identicalOffer) 'next': previous.nextChunk,
        if (!identicalOffer) 'reason': 'conflicting transfer identity'};
    }
    final finished = _completedIncoming[id];
    if (finished != null) {
      return {'ok': finished.senderId == peer.id &&
          finished.checksum == sha && finished.bytes == total,
          'done': true, 'next': finished.next};
    }
    if (_pendingOfferIds.contains(id)) return {'ok': false, 'reason': 'pending'};
    if (_incoming.length + _pendingOfferIds.length >= maxConcurrentIncoming) {
      return {'ok': false, 'reason': 'busy'};
    }
    _pendingOfferIds.add(id);
    try {
      if (!autoReceiveFiles) {
        final ask = onFileOffer;
        if (ask == null || !await ask(peer, safeFileName(name), total)) {
          return {'ok': false, 'reason': 'declined'};
        }
      }
      final dir = await _storage();
      final tempDir = Directory('${dir.path}${Platform.pathSeparator}pending');
      await tempDir.create(recursive: true);
      final temporary = File('${tempDir.path}${Platform.pathSeparator}$id.part');
      await temporary.writeAsBytes([], flush: true);
      _incoming[id] = _ReceiveState(safeFileName(name), sha, total, temporary, peer.id);
      _reportProgress(TransferProgress(id, peer.id, safeFileName(name), 0, total, true));
      if (total == 0) return {'ok': await _finish(id, _incoming[id]!), 'next': 0};
      return {'ok': true, 'next': 0};
    } finally {
      _pendingOfferIds.remove(id);
    }
  }

  Future<Map<String, dynamic>> _receiveChunk(Peer peer, List<int> plain) async {
    final data = jsonDecode(utf8.decode(plain)) as Map<String, dynamic>;
    final id = data['id'];
    final idx = data['index'];
    final payload = data['bytes'];
    if (id is! String || idx is! int || payload is! String) return {'ok': false};
    final transfer = _incoming[id];
    if (transfer == null) {
      final finished = _completedIncoming[id];
      return {'ok': finished != null && finished.senderId == peer.id,
        if (finished != null && finished.senderId == peer.id) ...{
          'done': true, 'next': finished.next,
        }};
    }
    if (transfer.senderId != peer.id) return {'ok': false};
    return transfer.writes.run(() async {
      if (!identical(_incoming[id], transfer)) {
        final completed = _completedIncoming[id];
        if (completed != null && completed.senderId == peer.id) {
          return {'ok': true, 'done': true, 'next': completed.next};
        }
        return {'ok': false};
      }
      if (idx < 0) return {'ok': false};
      if (idx < transfer.nextChunk) return {'ok': true, 'next': transfer.nextChunk};
      if (idx != transfer.nextChunk) return {'ok': false, 'next': transfer.nextChunk};
      final bytes = base64Decode(payload);
      if (bytes.isEmpty || bytes.length > chunkSize ||
          transfer.written + bytes.length > transfer.total) return {'ok': false};
      await transfer.temporary.writeAsBytes(bytes, mode: FileMode.append);
      transfer.written += bytes.length;
      _reportProgress(TransferProgress(id, peer.id, transfer.name, transfer.written,
          transfer.total, true));
      if (transfer.written == transfer.total && !await _finish(id, transfer)) {
        return {'ok': false};
      }
      return {'ok': true, 'next': idx + 1};
    });
  }

  // A shared completion gate protects same-name destination allocation.
  // Per-transfer chunk gates alone cannot prevent two different file IDs
  // simultaneously choosing the same Received/filename.
  Future<bool> _finish(String id, _ReceiveState transfer) =>
      _completionGate.run(() async {
    final actual = (await hash.sha256.bind(transfer.temporary.openRead()).first).toString();
    if (actual != transfer.checksum) {
      await transfer.temporary.delete();
      _incoming.remove(id);
      _reportProgress(TransferProgress(id, transfer.senderId, transfer.name, transfer.written,
        transfer.total, true, error: 'Integrity check failed'));
      return false;
    }
    final dir = await _storage();
    final destination = Directory('${dir.path}${Platform.pathSeparator}Received');
    await destination.create(recursive: true);
    var name = transfer.name;
    final dot = name.lastIndexOf('.');
    final stem = dot > 0 ? name.substring(0, dot) : name;
    final ext = dot > 0 ? name.substring(dot) : '';
    var n = 1;
    while (await File('${destination.path}${Platform.pathSeparator}$name').exists()) {
      name = '$stem (${n++})$ext';
    }
    final completed = await transfer.temporary.rename(
        '${destination.path}${Platform.pathSeparator}$name');
    _incoming.remove(id);
    // Volatile duplicate-completion witness for lost final HTTP response.
    // Deliberately not claimed to survive process restart.
    if (_completedIncoming.length >= 128) {
      _completedIncoming.remove(_completedIncoming.keys.first);
    }
    _completedIncoming[id] = _CompletedIncomingFile(
        transfer.senderId, transfer.checksum, transfer.total);
    _reportProgress(TransferProgress(id, transfer.senderId, name, transfer.total, transfer.total,
        true, finished: true));
    final sender = peers[transfer.senderId];
    if (sender != null) {
      onChat?.call(sender, ChatMessage(id: id, peerId: sender.id, text: name,
          outgoing: false, time: DateTime.now(), kind: 'file',
          filePath: completed.path, fileSize: transfer.total));
    }
    return true;
  });

  Future<void> sendFile(Peer peer, File file) async {
    final id = randomId();
    final name = safeFileName(file.uri.pathSegments.last);
    final total = await file.length();
    final sha = (await hash.sha256.bind(file.openRead()).first).toString();
    final reply = await _event(peer, {'kind': 'file-offer', 'id': id,
      'name': name, 'size': total, 'sha256': sha});
    if (reply['ok'] != true) throw StateError('Receiver cannot accept file: ${reply['reason'] ?? 'unavailable'}');
    var index = (reply['next'] as int?) ?? 0;
    final finalIndex = (total / chunkSize).ceil();
    if (index < 0 || index > finalIndex) {
      throw StateError('Receiver reported impossible transfer offset');
    }
    if (reply['done'] == true && index != finalIndex) {
      throw StateError('Receiver reported inconsistent completion');
    }
    try {
      final input = await file.open();
      try {
        await input.setPosition(index * chunkSize);
        while (index * chunkSize < total) {
          final chunk = await input.read(min(chunkSize, total - index * chunkSize));
          if (chunk.isEmpty) throw const FileSystemException('Unable to read file');
          DateTime? firstFailure;
          var accepted = false;
          while (!accepted) {
            try {
              final res = await _post(peer, '/v1/chunk', utf8.encode(jsonEncode({
                'id': id, 'index': index, 'bytes': base64Encode(chunk),
              })));
              if (res['ok'] != true) {
                throw StateError('Receiver rejected file chunk');
              }
              accepted = true;
            } catch (e) {
              firstFailure ??= DateTime.now();
              if (DateTime.now().difference(firstFailure) >=
                  Duration(seconds: reconnectGraceSeconds)) rethrow;
              _reportProgress(TransferProgress(id, peer.id, name,
                  min(index * chunkSize, total), total, false, waiting: true));
              // Preserve the same ID/chunk. An ACK may have been lost while
              // the receiver already appended the chunk; query its signed
              // next index before retrying to avoid appending it twice.
              await Future<void>.delayed(const Duration(seconds: 1));
              try {
                final status = await _event(peer, {
                  'kind': 'file-status', 'id': id,
                });
                if (status['ok'] == true) {
                  final next = status['next'];
                  if (next == index + 1) {
                    accepted = true; // Receiver already acknowledged on disk.
                  } else if (next != index) {
                    throw StateError(
                        'Transfer offset changed; retry requires a new file offer');
                  }
                }
              } on StateError {
                rethrow; // Never silently skip or duplicate missing bytes.
              } catch (_) {
                // Peer still unreachable: honor the same bounded deadline.
              }
            }
          }
          index++;
          _reportProgress(TransferProgress(id, peer.id, name,
              min(index * chunkSize, total), total, false));
        }
      } finally { await input.close(); }
      _reportProgress(TransferProgress(id, peer.id, name, total, total, false, finished: true));
      onChat?.call(peer, ChatMessage(id: id, peerId: peer.id, text: name,
          outgoing: true, time: DateTime.now(), kind: 'file',
          filePath: file.path, fileSize: total));
    } catch (e) {
      _reportProgress(TransferProgress(id, peer.id, name, min(index * chunkSize, total),
          total, false, error: e.toString()));
      rethrow;
    }
  }

  Future<List<File>> receivedFiles() async {
    final dir = await _storage();
    final folder = Directory('${dir.path}${Platform.pathSeparator}Received');
    if (!await folder.exists()) return [];
    return folder.listSync().whereType<File>().toList()
      ..sort((a, b) => b.statSync().modified.compareTo(a.statSync().modified));
  }

  Future<void> dispose() async {
    _ticker?.cancel();
    _progressPulse?.cancel();
    _progressPending.clear();
    _pendingOfferIds.clear();
    _peerIntroductionsPending.clear();
    _udp?.close();
    await _server?.close(force: true);
    _http.close(force: true);
    try { await _wifiMulticast.invokeMethod<void>('release'); } catch (_) {}
  }
}