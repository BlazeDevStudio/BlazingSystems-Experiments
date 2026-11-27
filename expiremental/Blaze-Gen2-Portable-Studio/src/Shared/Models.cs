using System.Text.Json;
using System.Text.Json.Serialization;

namespace BlazeGen2;

public enum CompatibilityLevel { FullyPortableCandidate, PartiallyPortable, RequiresExternalDependencies, HighRiskManualConfiguration, Unsupported }
public enum SourceKind { Installed, ExtractedDirectory, ManualExecutable }
public enum DataMode { PerClientWritable, FullyLocal, TemporarySession }
public enum VersionStrategy { FixedExecutable, ConfiguredVersionPath, VersionManifest, VersionDirectoryDiscovery, ApplicationSpecificProfile }

public sealed class AnalysisReport {
    public string SourceDirectory { get; set; } = "";
    public string MainExecutable { get; set; } = "";
    public string DisplayName { get; set; } = "";
    public CompatibilityLevel Classification { get; set; }
    public List<string> Evidence { get; set; } = new();
    public List<string> Warnings { get; set; } = new();
    public List<string> Files { get; set; } = new();
    public List<string> ImportedDlls { get; set; } = new();
    public long TotalBytes { get; set; }
}

public sealed class PortableConfig {
    public int SchemaVersion { get; set; } = 1;
    public string PackageId { get; set; } = Guid.NewGuid().ToString("N");
    public string DisplayName { get; set; } = "Portable application";
    public string AppDirectory { get; set; } = "App/Executables";
    public string Executable { get; set; } = "";
    public string WorkingDirectory { get; set; } = ".";
    public string Arguments { get; set; } = "";
    public DataMode DataMode { get; set; } = DataMode.PerClientWritable;
    public bool RedirectEnvironmentFolders { get; set; } = false;
    // Legacy v1.0 packages remain unchanged; v1.1 builder opts new per-client packages into safe local execution.
    public bool IsolateExecutablePerClient { get; set; } = false;
    public string? WritableDataRoot { get; set; }
    public VersionStrategy VersionStrategy { get; set; } = VersionStrategy.FixedExecutable;
    public string VersionDirectory { get; set; } = "Versions";
    public string VersionExecutable { get; set; } = "";
    public string ConfiguredVersion { get; set; } = "";
    public string VersionManifestFile { get; set; } = "current-version.txt";
    public List<string> RequiredFiles { get; set; } = new();
    public Dictionary<string,string> Environment { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public static readonly JsonSerializerOptions JsonOptions = new(){WriteIndented=true, PropertyNameCaseInsensitive=true, Converters={new JsonStringEnumConverter()}};
    public static PortableConfig Load(string path) => JsonSerializer.Deserialize<PortableConfig>(File.ReadAllText(path),JsonOptions) ?? throw new InvalidDataException("Invalid configuration");
    public void Save(string path) => File.WriteAllText(path,JsonSerializer.Serialize(this,JsonOptions));
}
public sealed class InstalledEntry {
    public string Name { get; set; } = "";
    public string Version { get; set; } = "";
    public string Directory { get; set; } = "";
    public string Executable { get; set; } = "";
    public override string ToString() => Name + (string.IsNullOrWhiteSpace(Version)?"":" ("+Version+")");
}
public sealed class ConversionOptions {
    public required string SourceExecutable { get; init; }
    public required string Destination { get; init; }
    public DataMode DataMode { get; init; } = DataMode.PerClientWritable;
    public string Arguments { get; init; } = "";
    public bool RedirectEnvironmentFolders { get; init; } = false;
    public bool IsolateExecutablePerClient { get; init; } = false;
}
public sealed class CompatibilityProfile {
    public string Name { get; set; } = "Generic";
    public string ExecutablePattern { get; set; } = "*.exe";
    public string? Arguments { get; set; }
    public string? WorkingDirectory { get; set; }
    public List<string> Warnings { get; set; } = new();
    public List<string> RequiredFiles { get; set; } = new();
}

