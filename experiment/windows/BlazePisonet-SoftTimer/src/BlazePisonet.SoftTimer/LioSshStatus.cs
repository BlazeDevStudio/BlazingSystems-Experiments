using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.RegularExpressions;

namespace BlazePisonet.SoftTimer;

internal sealed record LioSshProcessResult(int ExitCode, string StandardOutput);

// Reads only the existing Linux LIO status command. The server must separately
// provision a restricted, forced-command SSH key; this client does not do so.
public sealed class LioSshStatusClient
{
    private readonly string _executable;
    private readonly Func<ProcessStartInfo, CancellationToken, Task<LioSshProcessResult>> _run;

    public LioSshStatusClient() : this(
        Path.Combine(Environment.SystemDirectory, "OpenSSH", "ssh.exe"), RunProcessAsync) { }

    internal LioSshStatusClient(string executable,
        Func<ProcessStartInfo, CancellationToken, Task<LioSshProcessResult>> run)
    {
        _executable = executable;
        _run = run;
    }

    public async Task<string> InspectDisabledAsync(string targetIp, string user,
        string identityFile, string knownHostsFile, CancellationToken cancellationToken = default)
    {
        var start = BuildStartInfo(_executable, targetIp, user, identityFile, knownHostsFile);
        LioSshProcessResult result;
        try { result = await _run(start, cancellationToken); }
        catch (OperationCanceledException) { throw; }
        catch (Exception) { throw new InvalidOperationException("SSH status unavailable; inspect the lab server locally."); }
        if (result.ExitCode != 0 ||
            result.StandardOutput.Replace("\r\n", "\n", StringComparison.Ordinal) != "PREPARED_DISABLED\n")
            throw new InvalidOperationException("LIO status was not verified; inspect the lab server locally.");
        return "PREPARED_DISABLED";
    }

    internal static ProcessStartInfo BuildStartInfo(string executable, string targetIp,
        string user, string identityFile, string knownHostsFile)
    {
        if (!IPAddress.TryParse(targetIp, out var ip) ||
            ip.AddressFamily != AddressFamily.InterNetwork || ip.ToString() != targetIp)
            throw new InvalidOperationException("Select a saved profile with a canonical IPv4 target.");
        if (string.IsNullOrEmpty(user) ||
            !Regex.IsMatch(user, @"\A[a-z_][a-z0-9_-]{0,31}\z", RegexOptions.CultureInvariant))
            throw new InvalidOperationException("Enter a dedicated Linux SSH account name.");
        CheckPrivateFile(identityFile, "SSH identity");
        CheckPrivateFile(knownHostsFile, "pinned SSH known-hosts");
        if (!File.Exists(executable))
            throw new InvalidOperationException("Windows OpenSSH Client is unavailable.");

        var start = new ProcessStartInfo(executable)
        {
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            WorkingDirectory = AppContext.BaseDirectory
        };
        foreach (var arg in new[] {
            "-F", "none", "-4", "-T", "-n", "-a", "-x",
            "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", "UserKnownHostsFile=" + knownHostsFile,
            "-o", "GlobalKnownHostsFile=none", "-o", "UpdateHostKeys=no",
            "-o", "IdentitiesOnly=yes", "-o", "IdentityAgent=none",
            "-o", "PreferredAuthentications=publickey",
            "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no",
            "-o", "ConnectTimeout=5", "-o", "ConnectionAttempts=1",
            "-i", identityFile, "-p", "22", user + "@" + targetIp,
            "blaze-lio-status"
        }) start.ArgumentList.Add(arg);
        return start;
    }

    private static void CheckPrivateFile(string path, string name)
    {
        if (string.IsNullOrWhiteSpace(path) || !Path.IsPathFullyQualified(path))
            throw new InvalidOperationException(name + " file must have an absolute path.");
        try
        {
            var attributes = File.GetAttributes(path);
            if ((attributes & (FileAttributes.Directory | FileAttributes.ReparsePoint)) != 0 ||
                new FileInfo(path).Length is < 1 or > 65536)
                throw new InvalidOperationException(name + " file is unsafe or empty.");
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            throw new InvalidOperationException(name + " file is unavailable.");
        }
    }

    private static async Task<LioSshProcessResult> RunProcessAsync(ProcessStartInfo start,
        CancellationToken cancellationToken)
    {
        using var process = new Process { StartInfo = start };
        if (!process.Start()) throw new IOException("SSH did not start");
        process.StandardInput.Close();
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(12));
        try
        {
            var output = ReadLimitedAsync(process.StandardOutput, 128, timeout.Token);
            var error = ReadLimitedAsync(process.StandardError, 2048, timeout.Token);
            await Task.WhenAll(process.WaitForExitAsync(timeout.Token), output, error);
            return new LioSshProcessResult(process.ExitCode, await output);
        }
        catch
        {
            if (!process.HasExited) process.Kill(entireProcessTree: true);
            throw;
        }
    }

    private static async Task<string> ReadLimitedAsync(StreamReader reader, int limit,
        CancellationToken cancellationToken)
    {
        var result = new StringBuilder();
        var buffer = new char[256];
        while (true)
        {
            var count = await reader.ReadAsync(buffer.AsMemory(), cancellationToken);
            if (count == 0) return result.ToString();
            if (result.Length + count > limit) throw new IOException("SSH output too large");
            result.Append(buffer, 0, count);
        }
    }
}
