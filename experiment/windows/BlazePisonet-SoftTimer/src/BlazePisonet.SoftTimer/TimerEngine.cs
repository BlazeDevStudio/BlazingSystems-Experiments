namespace BlazePisonet.SoftTimer;

public sealed class TimerEngine : IDisposable
{
    private readonly object _gate = new();
    private readonly System.Threading.Timer _tick;
    private RuntimeState _state;
    private DateTimeOffset _lastTick = DateTimeOffset.UtcNow;
    private DateTimeOffset _lastPersist = DateTimeOffset.MinValue;
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
            _lastTick = DateTimeOffset.UtcNow;
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
            _lastTick = _state.UpdatedUtc;
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
            _lastTick = _state.UpdatedUtc;
            newActive = seconds > 0;
            if (changed && (DateTimeOffset.UtcNow - _lastPersist).TotalSeconds >= 2)
            {
                Storage.SaveState(_state);
                _lastPersist = DateTimeOffset.UtcNow;
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
            _lastTick = DateTimeOffset.UtcNow;
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
            _lastTick = _state.UpdatedUtc;
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

    private void Tick()
    {
        bool changed = false;
        bool becameInactive = false;
        long remaining = 0;
        lock (_gate)
        {
            var now = DateTimeOffset.UtcNow;
            var elapsed = Math.Max(0, (now - _lastTick).TotalSeconds);
            _lastTick = now;
            if (_externalAuthority || _paused || _state.RemainingSeconds <= 0 || elapsed < 0.2) return;

            var old = _state.RemainingSeconds;
            _state.RemainingSeconds = Math.Max(0, old - Math.Max(1, (long)Math.Floor(elapsed)));
            if (_state.RemainingSeconds != old)
            {
                changed = true;
                _state.TimerRunning = _state.RemainingSeconds > 0;
                _state.UpdatedUtc = now;
                remaining = _state.RemainingSeconds;
                becameInactive = old > 0 && remaining == 0;
                if ((now - _lastPersist).TotalSeconds >= 5 || becameInactive)
                {
                    Storage.SaveState(_state);
                    _lastPersist = now;
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
