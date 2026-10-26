import 'dart:async';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/recoverable_json_file.dart';
import 'package:lan_messenger/src/serial_async_gate.dart';

void main() {
  test('recoverable JSON keeps a complete previous version', () async {
    final dir = await Directory.systemTemp.createTemp('lan-json-recovery-');
    try {
      final file = File('${dir.path}${Platform.pathSeparator}chats.json');
      final isValid = (dynamic value) => value is Map && value['n'] is int;
      await RecoverableJsonFile.write(file, {'n': 1});
      await RecoverableJsonFile.write(file, {'n': 2});
      expect((await RecoverableJsonFile.read(file, isValid: isValid))['n'], 2);

      // Interrupted replacement: previous version exists in .bak.
      await file.delete();
      expect(await RecoverableJsonFile.hasSavedState(file), isTrue);
      expect((await RecoverableJsonFile.read(file, isValid: isValid))['n'], 1);

      // If the primary is malformed (e.g. older direct-write builds),
      // a valid backup still protects the existing local data.
      await file.writeAsString('{', flush: true);
      expect((await RecoverableJsonFile.read(file, isValid: isValid))['n'], 1);
      // Recovery must restore the primary without destroying the backup:
      // a subsequent interrupted save must not replace the only valid copy
      // with the old corrupt JSON contents.
      expect(await file.exists(), isTrue);
      expect(await RecoverableJsonFile.backupOf(file).exists(), isTrue);
    } finally {
      await dir.delete(recursive: true);
    }
  });

  test('invalid primary shape cannot hide intact backup', () async {
    final dir = await Directory.systemTemp.createTemp('lan-json-shape-');
    try {
      final file = File('${dir.path}${Platform.pathSeparator}identity.json');
      await RecoverableJsonFile.write(file, {'private': 'old'});
      await RecoverableJsonFile.write(file, {'private': 'new'});
      await file.writeAsString('{"unexpected":true}', flush: true);
      final recovered = await RecoverableJsonFile.read(file,
          isValid: (value) => value is Map && value['private'] is String);
      expect(recovered['private'], 'old');
    } finally {
      await dir.delete(recursive: true);
    }
  });

  test('rapid settings saves are serialized and remain valid JSON', () async {
    final dir = await Directory.systemTemp.createTemp('lan-json-rapid-');
    try {
      final file = File('${dir.path}${Platform.pathSeparator}settings.json');
      await Future.wait(List.generate(12, (n) =>
          RecoverableJsonFile.write(file, {'sequence': n})));
      final current = await RecoverableJsonFile.read(file,
          isValid: (value) => value is Map && value['sequence'] is int);
      expect(current['sequence'], 11);
    } finally {
      await dir.delete(recursive: true);
    }
  });

  test('per-transfer asynchronous writes never overlap', () async {
    final gate = SerialAsyncGate();
    var active = 0;
    var maxActive = 0;
    final order = <int>[];
    await Future.wait(List.generate(14, (index) => gate.run(() async {
      active++;
      if (active > maxActive) maxActive = active;
      await Future<void>.delayed(const Duration(milliseconds: 2));
      order.add(index);
      active--;
    })));
    expect(maxActive, 1);
    expect(order, List<int>.generate(14, (n) => n));
    await expectLater(gate.run<void>(() async {
      throw StateError('bad chunk');
    }), throwsStateError);
    // One rejected request must not permanently deadlock the transfer.
    expect(await gate.run(() async => 'next chunk'), 'next chunk');
  });
}
