using System.Diagnostics;

namespace BlazePisonet.SoftTimer;

// Diagnostic-only, first-party bounded same-owned-HANDLE sampled CTS capture.
// Caller MUST invoke SampleOnce on a monotonic schedule with intervals shorter
// than the intended pulse. This does NOT authorize coins or prove physical
// pulse completeness. Unlike a COM-number SerialPort it uses only the handle
// already owned by NativeComInterfaceSession (GetCommModemStatus).
internal interface INativePulseClock
{
    TimeSpan Elapsed { get; }
}

internal sealed class StopwatchNativePulseClock : INativePulseClock
{
    private readonly long _origin = Stopwatch.GetTimestamp();
    public TimeSpan Elapsed => Stopwatch.GetElapsedTime(_origin);
}

// Immutable in-process observation, never a paid event/receipt. Its source and
// constructor are internal; the session epoch makes callbacks from A unable
// to claim an event against a replacement session B even at the same path.
internal sealed class NativeObservedPulse
{
    internal NativeComInterfaceSession Source { get; }
    internal NativeObservedPulse(NativeComInterfaceSession source,
        long generation, long sequence, TimeSpan start, TimeSpan end)
    {
        Source = source;
        Generation = generation;
        Sequence = sequence;
        DeviceInstanceId = source.DeviceInstanceId;
        InterfacePath = source.InterfacePath;
        StartedAt = start;
        EndedAt = end;
    }
    internal long Generation { get; }
    internal long Sequence { get; }
    internal string DeviceInstanceId { get; }
    internal string InterfacePath { get; }
    internal TimeSpan StartedAt { get; }
    internal TimeSpan EndedAt { get; }
    internal double WidthMs => (EndedAt - StartedAt).TotalMilliseconds;
}

internal sealed class NativeComPulseCapture : IDisposable
{
    private readonly object _gate = new();
    private readonly INativePulseClock _clock;
    private readonly int _minimumMs, _maximumMs, _debounceMs, _maximumGapMs;
    private readonly HashSet<NativeObservedPulse> _unclaimed = new();
    private NativeComInterfaceSession? _session;
    private long _generation, _sequence;
    private TimeSpan? _lastSample, _pulseStarted, _lastAccepted;
    private bool _armed;
    private bool _active;
    private bool _disposed;

    internal NativeComPulseCapture(
        INativePulseClock? clock = null, int minimumMs = 20,
        int maximumMs = 1000, int debounceMs = 50, int maximumGapMs = 40)
    {
        if (minimumMs < 1 || maximumMs < minimumMs || debounceMs < 0 ||
            maximumGapMs < 1)
            throw new ArgumentOutOfRangeException(nameof(minimumMs),
                "Pulse duration, debounce and maximum sample interval must be bounded.");
        _clock = clock ?? new StopwatchNativePulseClock();
        _minimumMs = minimumMs;
        _maximumMs = maximumMs;
        _debounceMs = debounceMs;
        _maximumGapMs = maximumGapMs;
    }

    // Fired only outside _gate. Treat as diagnostic, NOT coin-authoritative.
    internal event Action<NativeObservedPulse>? Observed;
    internal long Generation { get { lock (_gate) return _generation; } }

    // Transfers ownership of an already opened exact device-interface HANDLE.
    // Passing null retires/disposes the prior HANDLE and every unclaimed event.
    internal void Rebind(NativeComInterfaceSession? replacement)
    {
        NativeComInterfaceSession? previous;
        lock (_gate)
        {
            ObjectDisposedException.ThrowIf(_disposed, this);
            if (replacement?.IsClosed == true)
                throw new ArgumentException("Cannot bind closed interface HANDLE", nameof(replacement));
            previous = _session;
            // Never reuse the same object as a new epoch while it is open.
            if (ReferenceEquals(previous, replacement) && previous is not null)
                throw new ArgumentException("Cannot rebind the same owned session", nameof(replacement));
            _session = replacement;
            unchecked { _generation++; }
            ResetLocked();
        }
        previous?.Dispose();
    }

    // Explicit unplug/driver invalidation hook. An unsupported or failing
    // status read also retires the handle through the same path.
    internal void Invalidate() => Rebind(null);

    // One synchronous sample; callers control the sampling cadence, and
    // missed/late/unknown samples MUST NOT be converted into edges.
    // Never invokes callbacks under _gate; no async background capture here.
    internal void SampleOnce()
    {
        NativeObservedPulse? observed = null;
        NativeComInterfaceSession? retired = null;
        lock (_gate)
        {
            if (_disposed || _session is null) return;
            var source = _session;
            var now = _clock.Elapsed;

            if (_lastSample is { } earlier &&
                (now < earlier || (now - earlier).TotalMilliseconds > _maximumGapMs))
            {
                // Too much unobserved time, or clock rollback: a pulse may
                // have started/ended unseen. Wait for a VERIFIED idle sample.
                _armed = false;
                _active = false;
                _pulseStarted = null;
                _unclaimed.Clear();
            }
            _lastSample = now;

            bool sampleOk;
            bool level;
            try { sampleOk = source.TryReadSignal(ModemSignal.Cts, out level); }
            catch (Exception) { sampleOk = false; level = false; }

            if (!sampleOk)
            {
                retired = _session;
                _session = null;
                unchecked { _generation++; }
                ResetLocked();
            }
            else if (!level)
            {
                if (!_armed)
                {
                    // Verified idle is required after bind, gap, error or
                    // accepted pulse. An already-high first sample cannot
                    // supply a beginning edge.
                    _armed = true;
                    _active = false;
                    _pulseStarted = null;
                }
                else if (_active && _pulseStarted is { } start)
                {
                    var width = (now - start).TotalMilliseconds;
                    if (width >= _minimumMs && width <= _maximumMs &&
                        (_lastAccepted is null ||
                         (now - _lastAccepted.Value).TotalMilliseconds >= _debounceMs))
                    {
                        _lastAccepted = now;
                        observed = new NativeObservedPulse(
                            source, _generation, ++_sequence, start, now);
                        _unclaimed.Add(observed);
                    }
                    _armed = false; // demand another explicit idle sample
                    _active = false;
                    _pulseStarted = null;
                }
            }
            else if (_armed && !_active)
            {
                _active = true;
                _pulseStarted = now;
            }
        }
        retired?.Dispose();
        if (observed is null) return;

        try
        {
            // A concurrent Rebind can retire the event between capture and
            // dispatch. Only a successful one-time TryClaimObserved validates
            // ownership at the point of consumption; never assume callback
            // arrival means current session or monetary authorization.
            Observed?.Invoke(observed);
        }
        finally
        {
            lock (_gate) _unclaimed.Remove(observed);
        }
    }

    internal bool TryClaimObserved(NativeObservedPulse observed)
    {
        if (observed is null) return false;
        lock (_gate)
        {
            if (!_unclaimed.Remove(observed)) return false;
            if (_disposed || _session is null ||
                !ReferenceEquals(_session, observed.Source) ||
                observed.Generation != _generation)
                return false;

            // Removal after a good sample, before this listener claims it,
            // must revoke the ENTIRE capture generation, not just the event.
            // TryVerifyPresent closes the original invalid handle.
            if (_session.IsClosed || !_session.TryVerifyPresent())
            {
                _session = null;
                unchecked { _generation++; }
                ResetLocked();
                return false;
            }
            return true;
        }
    }

    private void ResetLocked()
    {
        _armed = false;
        _active = false;
        _lastSample = null;
        _pulseStarted = null;
        _lastAccepted = null;
        _unclaimed.Clear();
    }

    public void Dispose()
    {
        NativeComInterfaceSession? old;
        lock (_gate)
        {
            if (_disposed) return;
            _disposed = true;
            old = _session;
            _session = null;
            unchecked { _generation++; }
            ResetLocked();
        }
        old?.Dispose();
    }
}
