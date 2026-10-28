import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// Preserve the last complete local JSON record across process termination.
///
/// Windows does not reliably support overwriting an existing file with
/// File.rename. Stage and flush the next version, move the previous one to a
/// recoverable backup, then promote the fully written file. Callers validate
/// data on read and may recover from an interrupted rename or truncated file.
class RecoverableJsonFile {
  RecoverableJsonFile._();

  static final Map<String, Future<void>> _writes = {};

  static File backupOf(File file) => File('${file.path}.bak');

  static Future<bool> hasSavedState(File file) async =>
      await file.exists() || await backupOf(file).exists();

  static Future<dynamic> read(
    File file, {
    required bool Function(dynamic) isValid,
  }) async {
    for (final candidate in [file, backupOf(file)]) {
      try {
        final decoded = jsonDecode(await candidate.readAsString());
        if (isValid(decoded)) {
          if (candidate.path != file.path) {
            // Restore the last valid backup while KEEPING the backup intact.
            // Otherwise the next save could replace the only good .bak with
            // a corrupt primary before promoting the new JSON file.
            try {
              await candidate.copy(file.path);
            } catch (_) {
              // The backup is still intact and can be read on next startup.
            }
          }
          return decoded;
        }
      } catch (_) {
        // Try the last complete version. Do not delete or overwrite either
        // copy; retain damaged input for later diagnostics/recovery.
      }
    }
    throw FileSystemException('No valid saved JSON or backup', file.path);
  }

  /// Serializes repeated UI saves of the same file, avoiding overlapping
  /// writers to a shared .pending filename. Capture the JSON snapshot now,
  /// rather than after another settings change mutates the input object.
  static Future<void> write(File file, Object? value) {
    final encoded = jsonEncode(value);
    final previous = _writes[file.path] ?? Future<void>.value();
    final current = previous.then((_) => _replace(file, encoded));
    // One failed write must not poison every later save attempt.
    _writes[file.path] =
        current.then<void>((_) {}, onError: (Object _, StackTrace __) {});
    return current;
  }

  static Future<void> _replace(File file, String encoded) async {
    final pending = File('${file.path}.pending');
    final backup = backupOf(file);
    await pending.writeAsString(encoded, flush: true);

    if (await file.exists()) {
      // Primary remains present until the complete pending write is flushed.
      if (await backup.exists()) await backup.delete();
      await file.rename(backup.path);
    }
    try {
      await pending.rename(file.path);
    } catch (_) {
      // If promotion fails, restore the last known primary where possible.
      if (!await file.exists() && await backup.exists()) {
        try {
          await backup.rename(file.path);
        } catch (_) {
          // Preserve the backup if the OS refuses rollback.
        }
      }
      rethrow;
    }
  }
}
