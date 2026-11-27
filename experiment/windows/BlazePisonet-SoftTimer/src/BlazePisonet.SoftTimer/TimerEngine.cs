using System.Diagnostics;

namespace BlazePisonet.SoftTimer;

public sealed class TimerEngine : IDisposable
{
    private readonly object _gate = new();
    private readonly System.Threading.Timer _tick;
    private RuntimeState _state;
    // Monotonic clock: wall-clock edits must not multiply or erase paid time.
    private long _lastTickStamp = Stopwatch.GetTimestamp();
    private long _lastPersistStamp;
    private double _fractionalSeconds;
    private bool _externalAuthority;
    private bool _paused;

    public event Action<long>? RemainingChanged;
    public event Action<bool>? ActiveChanged;
    public event Action<string>? Audit;

    public TimerEngine()
    {
        _state = Storage.LoadState();
        _paused = _state.PendingMemberOperation is not null;
        _tick = new System.Threading.Timer(_ => Tick(), null, 250, 250);
    }

    public long RemainingSeconds
    {
        get { lock (_gate) return Math.Max(0, _state.RemainingSeconds); }
    }

    public bool IsActive => RemainingSeconds > 0;
    public bool IsPaused { get { lock (_gate) return _paused; } }
    public long SalesPulseCount { get { lock (_gate) return _state.SalesPulseCount; } }

    public void SetExternalAuthority(bool external)
    {
        lock (_gate)
        {
            _externalAuthority = external;
            ResetTickClock();
        }
    }

    public void AddCoin(int secondsPerCoin, string source = "local")
    {
        if (secondsPerCoin <= 0) return;
        AddSeconds(secondsPerCoin, $"coin:{source}:{Guid.NewGuid():N}", true, $"Coin accepted from {source}");
    }

    public bool AddSeconds(long seconds, string eventId, bool countSale, string audit)
    {
        if (seconds <= 0 || string.IsNullOrWhiteSpace(eventId)) return false;
        bool wasActive;
        long remaining;
        lock (_gate)
        {
            if (_state.AppliedEventIds.Contains(eventId)) return false;
            wasActive = _state.RemainingSeconds > 0;
            _state.AppliedEventIds.Add(eventId);
            _state.RemainingSeconds = Math.Max(0, _state.RemainingSeconds) + seconds;
            _state.TimerRunning = _state.RemainingSeconds > 0;
            if (countSale) _state.SalesPulseCount++;
            _state.UpdatedUtc = DateTimeOffset.UtcNow;
            ResetTickClock();
            Storage.SaveState(_state);
            remaining = _state.RemainingSeconds;
        }
        Audit?.Invoke(audit + $"; +{seconds}s; remaining={remaining}s");
        RemainingChanged?.Invoke(remaining);
        if (!wasActive && remaining > 0) ActiveChanged?.Invoke(true);
        return true;
    }

    public void SetAuthoritativeSeconds(long seconds, string source)
    {
        seconds = Math.Max(0, seconds);
        bool oldActive;
        bool newActive;
        bool changed;
        lock (_gate)
        {
            _externalAuthority = true;
            oldActive = _state.RemainingSeconds > 0;
            changed = _state.RemainingSeconds != seconds;
            _state.RemainingSeconds = seconds;
            _state.TimerRunning = seconds > 0;
            _state.UpdatedUtc = DateTimeOffset.UtcNow;
            ResetTickClock();
            newActive = seconds > 0;
            if (changed && (ElapsedSince(Stopwatch.GetTimestamp(), _lastPersistStamp) >= 2))
            {
                Storage.SaveState(_state);
                _lastPersistStamp = Stopwatch.GetTimestamp();
            }
        }
        if (changed) RemainingChanged?.Invoke(seconds);
        if (oldActive != newActive) ActiveChanged?.Invoke(newActive);
    }

    public void Reset(string reason = "admin reset")
    {
        bool oldActive;
        lock (_gate)
        {
            oldActive = _state.RemainingSeconds > 0;
            _state.RemainingSeconds = 0;
            _state.TimerRunning = false;
            _state.UpdatedUtc = DateTimeOffset.UtcNow;
            ResetTickClock();
            Storage.SaveState(_state);
        }
        Audit?.Invoke($"Timer reset: {reason}");
        RemainingChanged?.Invoke(0);
        if (oldActive) ActiveChanged?.Invoke(false);
    }

    public void Pause(bool paused)
    {
        lock (_gate)
        {
            _paused = paused;
            ResetTickClock();
        }
        Audit?.Invoke(paused ? "Timer paused" : "Timer resumed");
    }

    public bool CreateOrUpdateMember(string username, string password)
    {
        username = username.Trim();
        if (username.Length < 2 || username.Length > 32 || password.Length < 4) return false;
        var hp = Passwords.HashMemberPassword(password);
        lock (_gate)
        {
            _state.Members[username] = new MemberAccount
            {
                Username = username,
                Enabled = true,
                PasswordScheme = "pbkdf2-sha256",
                PasswordRounds = 120000,
                PasswordSalt = hp.Salt,
                PasswordHash = hp.Hash,
                BankedSeconds = _state.Members.TryGetValue(username, out var old) ? old.BankedSeconds : 0,
                UpdatedUtc = DateTimeOffset.UtcNow
            };
            Storage.SaveState(_state);
        }
        Audit?.Invoke($"Member account created/updated: {username}");
        return true;
    }

    public bool BankCurrentTime(string username, string password)
    {
        lock (_gate)
        {
            if (!_state.Members.TryGetValue(username, out var member) || !Passwords.VerifyMemberPassword(member, password)) return false;
            member.BankedSeconds += Math.Max(0, _state.RemainingSeconds);
            member.UpdatedUtc = DateTimeOffset.UtcNow;
            _state.RemainingSeconds = 0;
            _state.TimerRunning = false;
            Storage.SaveState(_state);
        }
        RemainingChanged?.Invoke(0);
        ActiveChanged?.Invoke(false);
        Audit?.Invoke($"Time banked to member: {username}");
        return true;
    }

    public bool RestoreMemberTime(string username, string password)
    {
        long restored;
        lock (_gate)
        {
            if (!_state.Members.TryGetValue(username, out var member) || !Passwords.VerifyMemberPassword(member, password)) return false;
            restored = member.BankedSeconds;
            if (restored <= 0) return true;
            _state.RemainingSeconds += restored;
            _state.TimerRunning = true;
            member.BankedSeconds = 0;
            member.UpdatedUtc = DateTimeOffset.UtcNow;
            _state.UpdatedUtc = DateTimeOffset.UtcNow;
            ResetTickClock();
            Storage.SaveState(_state);
        }
        RemainingChanged?.Invoke(RemainingSeconds);
        ActiveChanged?.Invoke(true);
        Audit?.Invoke($"Member time restored: {username}; {restored}s");
        return true;
    }

    public bool TransferMemberTime(string fromUser, string fromPassword, string toUser, long seconds)
    {
        if (seconds <= 0) return false;
        lock (_gate)
        {
            if (!_state.Members.TryGetValue(fromUser, out var from) || !_state.Members.TryGetValue(toUser, out var to)) return false;
            if (!Passwords.VerifyMemberPassword(from, fromPassword) || from.BankedSeconds < seconds) return false;
            from.BankedSeconds -= seconds;
            to.BankedSeconds += seconds;
            from.UpdatedUtc = to.UpdatedUtc = DateTimeOffset.UtcNow;
            Storage.SaveState(_state);
        }
        Audit?.Invoke($"Member transfer: {fromUser} -> {toUser}; {seconds}s");
        return true;
    }

    public IReadOnlyList<MemberAccount> MembersSnapshot()
    {
        lock (_gate)
            return _state.Members.Values.Select(CloneMember).OrderBy(m => m.Username).ToList();
    }

    public long RemoteMemberRevision
    {
        get { lock (_gate) return _state.RemoteMemberRevision; }
    }

    public PendingMemberOperation? PendingMemberOperation
    {
        get
        {
            lock (_gate)
            {
                var p = _state.PendingMemberOperation;
                if (p is null) return null;
                return new PendingMemberOperation
                {
                    Action = p.Action,
                    Username = p.Username,
                    MemberToken = p.MemberToken,
                    EventId = p.EventId,
                    Seconds = p.Seconds,
                    MemberRevision = p.MemberRevision,
                    CreatedUtc = p.CreatedUtc
                };
            }
        }
    }

    public void SetPendingMemberOperation(PendingMemberOperation pending)
    {
        lock (_gate)
        {
            _state.PendingMemberOperation = pending;
            Storage.SaveState(_state);
        }
        Audit?.Invoke($"Pending BlazePwifi member operation recorded: {pending.Action}:{pending.Username}:{pending.EventId}");
    }

    public void ClearPendingMemberOperation(string eventId)
    {
        lock (_gate)
        {
            if (_state.PendingMemberOperation is null
                || !_state.PendingMemberOperation.EventId.Equals(eventId, StringComparison.OrdinalIgnoreCase))
                return;
            _state.PendingMemberOperation = null;
            Storage.SaveState(_state);
        }
        Audit?.Invoke($"Pending BlazePwifi member operation cleared: {eventId}");
    }

    public IReadOnlyList<MemberAccount> RemoteMembersSnapshot()
    {
        lock (_gate)
            return _state.RemoteMembers.Values.Select(CloneMember).OrderBy(m => m.Username).ToList();
    }

    public void ApplyRemoteMembers(IEnumerable<MemberAccount> members, long revision)
    {
        lock (_gate)
        {
            if (revision < _state.RemoteMemberRevision) return;
            var next = new Dictionary<string, MemberAccount>(StringComparer.OrdinalIgnoreCase);
            foreach (var member in members)
            {
                if (string.IsNullOrWhiteSpace(member.Username)) continue;
                member.RemoteManaged = true;
                next[member.Username] = CloneMember(member);
            }
            _state.RemoteMembers = next;
            _state.RemoteMemberRevision = revision;
            Storage.SaveState(_state);
        }
        Audit?.Invoke($"BlazePwifi member snapshot applied; revision={revision}; members={members.Count()}");
    }

    public MemberAccount? RemoteMember(string username)
    {
        lock (_gate)
            return _state.RemoteMembers.TryGetValue(username.Trim(), out var member) ? CloneMember(member) : null;
    }

    public bool VerifyRemoteMember(string username, string password)
    {
        lock (_gate)
            return _state.RemoteMembers.TryGetValue(username.Trim(), out var member)
                && member.Enabled
                && Passwords.VerifyMemberPassword(member, password);
    }

    private static MemberAccount CloneMember(MemberAccount m) => new()
    {
        Username = m.Username,
        Label = m.Label,
        Enabled = m.Enabled,
        PasswordScheme = m.PasswordScheme,
        PasswordSalt = m.PasswordSalt,
        PasswordHash = m.PasswordHash,
        PasswordRounds = m.PasswordRounds,
        BankedSeconds = m.BankedSeconds,
        Revision = m.Revision,
        RemoteManaged = m.RemoteManaged,
        UpdatedUtc = m.UpdatedUtc
    };

    // Deterministic, unit-testable portion of the billable elapsed-time logic.
    internal static long DebitWholeSeconds(ref double carry, double elapsed)
    {
        if (double.IsNaN(elapsed) || double.IsInfinity(elapsed) || elapsed <= 0)
            return 0;
        carry += elapsed;
        long whole = (long)Math.Floor(carry);
        carry -= whole;
        return whole;
    }

    internal static int VerifyTimerMath()
    {
        double carry = 0;
        for (int i = 0; i < 14400; i++)
        {
            long billed = DebitWholeSeconds(ref carry, 0.25); // 60 min at 250-ms cadence
            if (billed != (i % 4 == 3 ? 1L : 0L)) return 1;
        }
        if (Math.Abs(carry) > 0.000001) return 2;
        carry = 0;
        if (DebitWholeSeconds(ref carry, 0.375) != 0) return 3;
        if (DebitWholeSeconds(ref carry, 0.125) != 0) return 4;
        if (DebitWholeSeconds(ref carry, 0.625) != 1) return 5;
        if (Math.Abs(carry - 0.125) > 0.000001) return 6;
        if (DebitWholeSeconds(ref carry, -100) != 0) return 7;
        if (DebitWholeSeconds(ref carry, double.NaN) != 0) return 8;
        return 0;
    }

    private static double ElapsedSince(long now, long previous)
    {
        if (previous == 0) return double.PositiveInfinity;
        return Math.Max(0, (now - previous) / (double)Stopwatch.Frequency);
    }

    private void ResetTickClock()
    {
        _lastTickStamp = Stopwatch.GetTimestamp();
        _fractionalSeconds = 0;
    }

    private void Tick()
    {
        bool changed = false;
        bool becameInactive = false;
        long remaining = 0;
        lock (_gate)
        {
            long stamp = Stopwatch.GetTimestamp();
            double elapsed = ElapsedSince(stamp, _lastTickStamp);
            _lastTickStamp = stamp;
            if (_externalAuthority || _paused || _state.RemainingSeconds <= 0)
            {
                _fractionalSeconds = 0;
                return;
            }

            // Timer callback cadence is 250 ms. Debit only whole *elapsed*
            // seconds; carry fractions forward instead of billing 1s per tick.
            long secondsToDebit = DebitWholeSeconds(ref _fractionalSeconds, elapsed);
            if (secondsToDebit <= 0) return;

            long old = _state.RemainingSeconds;
            _state.RemainingSeconds = Math.Max(0, old - secondsToDebit);
            changed = _state.RemainingSeconds != old;
            if (changed)
            {
                _state.TimerRunning = _state.RemainingSeconds > 0;
                _state.UpdatedUtc = DateTimeOffset.UtcNow;
                remaining = _state.RemainingSeconds;
                becameInactive = old > 0 && remaining == 0;
                if (ElapsedSince(stamp, _lastPersistStamp) >= 5 || becameInactive)
                {
                    Storage.SaveState(_state);
                    _lastPersistStamp = stamp;
                }
            }
        }
        if (changed) RemainingChanged?.Invoke(remaining);
        if (becameInactive) ActiveChanged?.Invoke(false);
    }

    public void Dispose()
    {
        _tick.Dispose();
        lock (_gate) Storage.SaveState(_state);
    }
}
