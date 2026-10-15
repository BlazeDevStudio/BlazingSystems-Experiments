namespace BlazePisonet.SoftTimer;

// Local operator assignments only. These records do not provision an iSCSI target.
public sealed record DisklessClientAssignment(string ClientLabel, string TargetIp,
    string TargetIqn, string InitiatorIqn)
{
    public DisklessBootProfile BootProfile() =>
        DisklessBootProfile.Create(ClientLabel, TargetIp, TargetIqn, InitiatorIqn);

    public override string ToString() => $"{ClientLabel} · {TargetIp} · {TargetIqn}";
}

public static class DisklessProfileRegistry
{
    private const int MaxClients = 256;

    public static IReadOnlyList<DisklessClientAssignment> Validate(
        IEnumerable<DisklessClientAssignment>? assignments)
    {
        if (assignments is null)
            throw new InvalidOperationException("Saved diskless client profiles are missing or corrupt.");
        var result = new List<DisklessClientAssignment>();
        foreach (var assignment in assignments)
        {
            if (assignment is null || string.IsNullOrWhiteSpace(assignment.ClientLabel) ||
                string.IsNullOrWhiteSpace(assignment.TargetIp) ||
                string.IsNullOrWhiteSpace(assignment.TargetIqn) ||
                string.IsNullOrWhiteSpace(assignment.InitiatorIqn))
                throw new InvalidOperationException("Saved diskless client profile is incomplete.");
            assignment.BootProfile();
            if (result.Count >= MaxClients)
                throw new InvalidOperationException("Too many diskless client profiles.");
            if (result.Any(old => Same(old.ClientLabel, assignment.ClientLabel) ||
                                  Same(old.TargetIqn, assignment.TargetIqn) ||
                                  Same(old.InitiatorIqn, assignment.InitiatorIqn)))
                throw new InvalidOperationException("Saved diskless profiles reuse a client, target or initiator identity.");
            result.Add(assignment);
        }
        return result;
    }

    public static IReadOnlyList<DisklessClientAssignment> Add(
        IEnumerable<DisklessClientAssignment>? assignments, DisklessClientAssignment candidate)
    {
        var current = Validate(assignments);
        if (candidate is null)
            throw new InvalidOperationException("Select a complete diskless client profile.");
        return Validate(current.Append(candidate));
    }

    public static IReadOnlyList<DisklessClientAssignment> Remove(
        IEnumerable<DisklessClientAssignment>? assignments, string clientLabel)
    {
        var current = Validate(assignments);
        var remaining = current.Where(x => !Same(x.ClientLabel, clientLabel)).ToArray();
        if (remaining.Length == current.Count)
            throw new InvalidOperationException("Saved diskless client profile was not found.");
        return remaining;
    }

    private static bool Same(string left, string right) =>
        left.Equals(right, StringComparison.OrdinalIgnoreCase);
}
