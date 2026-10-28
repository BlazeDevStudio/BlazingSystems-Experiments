/// Prevents overlapping asynchronous mutations of one resource.
///
/// A failed operation must not poison the queue: later operations still run
/// and receive their own result/error. Each file transfer owns a separate gate
/// so unrelated file downloads remain parallel.
class SerialAsyncGate {
  Future<void> _tail = Future<void>.value();

  Future<T> run<T>(Future<T> Function() action) {
    final result = _tail.then((_) => action());
    _tail = result.then<void>((_) {}, onError: (Object _, StackTrace __) {});
    return result;
  }
}
