using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace BlazeGen2;

/// <summary>Conservative checks. Product policy is not bypassed by rewriting game state.</summary>
public static class DisklessSafety {
    public static bool IsRoblox(string path) {
        var normalized=path.Replace('/',Path.DirectorySeparatorChar);
        var parts=normalized.Split(Path.DirectorySeparatorChar,StringSplitOptions.RemoveEmptyEntries);
        return parts.Any(p=>p.Equals("Roblox",StringComparison.OrdinalIgnoreCase)
           ||p.StartsWith("RobloxPlayer",StringComparison.OrdinalIgnoreCase)
           ||p.StartsWith("RobloxStudio",StringComparison.OrdinalIgnoreCase));
    }
    public static void RejectUnverifiedRoblox(string path) {
        if(IsRoblox(path))throw new NotSupportedException(
            "Roblox is not validated for portable multi-PC deployment. " +
            "Shared Roblox installations or account/session state may affect other clients. " +
            "Use the official Roblox client with separate per-PC writable Windows user profiles " +
            "and separate Roblox accounts for simultaneous play. " +
            "Blaze Gen2 will not package or launch Roblox in experimental v1.1.0.");
    }
    public static bool IsNetworkPath(string path) {
        var full=Path.GetFullPath(path);
        if(full.StartsWith(@"\\",StringComparison.Ordinal))return true;
        try {
            var root=Path.GetPathRoot(full);
            return root!=null && new DriveInfo(root).DriveType==DriveType.Network;
        } catch(IOException){return true;}
    }
    public static string SafeMachineName() {
        var name=new string(Environment.MachineName.Where(c=>char.IsLetterOrDigit(c)||c=='-'||c=='_').ToArray());
        return string.IsNullOrWhiteSpace(name)?"UnknownMachine":name;
    }
    public static string ClientDataRoot(PortableConfig config) {
        var local=Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        if(string.IsNullOrWhiteSpace(local)||IsNetworkPath(local))
            throw new IOException("Client LOCALAPPDATA must be on a local writable disk; a shared user profile is not safe.");
        // Machine namespace prevents reuse of shared identity when usernames are identical on multiple PCs.
        return Path.Combine(local,"BlazeGen2","Clients",SafeMachineName(),config.PackageId);
    }
}
public sealed class FileManifestEntry {
    public string RelativePath {get;set;}="";
    public long Size {get;set;}
    public string Sha256 {get;set;}="";
}
public sealed class PackageManifest {
    public int SchemaVersion {get;set;}=1;
    public List<FileManifestEntry> Files {get;set;}=new();
    public static PackageManifest Load(string filename) =>
        JsonSerializer.Deserialize<PackageManifest>(File.ReadAllText(filename))
        ??throw new InvalidDataException("Invalid package file manifest");
    public void Save(string filename)=>File.WriteAllText(filename,JsonSerializer.Serialize(this,new JsonSerializerOptions{WriteIndented=true}));
}
public static class ClientIsolation {
    /// <summary>Creates or reuses a local, content-addressed, per-user-per-PC copy of package files.</summary>
    public static string Prepare(string packageRoot,string appRoot,PortableConfig cfg,string localData) {
        if(!cfg.IsolateExecutablePerClient)return appRoot;
        if(DisklessSafety.IsNetworkPath(localData))
            throw new IOException("Client data folder must be physically local, not SMB/UNC.");
        var manifestFile=Path.Combine(packageRoot,"FileManifest.json");
        if(!File.Exists(manifestFile))throw new InvalidDataException("Client-local execution needs FileManifest.json.");
        var manifest=PackageManifest.Load(manifestFile);
        if(manifest.SchemaVersion!=1||manifest.Files.Count<1)throw new InvalidDataException("Invalid manifest.");
        var fingerprint=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(manifestFile))).ToLowerInvariant();
        var cacheBase=Path.Combine(localData,"AppCache");
        Directory.CreateDirectory(cacheBase);
        // FileShare.None: only one launcher in this Windows user/machine sandbox at a time.
        var lockFile=Path.Combine(cacheBase,"copy.lock");
        using var copyLock=new FileStream(lockFile,FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None);
        var final=Path.Combine(cacheBase,fingerprint);
        var ready=Path.Combine(final,".complete");
        if(File.Exists(ready))return final;
        if(Directory.Exists(final))throw new IOException("An incomplete local cache exists. Remove it manually after inspection: "+final);
        var staging=Path.Combine(cacheBase,"staging-"+Guid.NewGuid().ToString("N"));
        try {
            Directory.CreateDirectory(staging);
            var seen=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach(var entry in manifest.Files) {
                var input=Paths.Inside(appRoot,entry.RelativePath);
                var output=Paths.Inside(staging,entry.RelativePath);
                if(!seen.Add(output))throw new InvalidDataException("Duplicate manifest path");
                if(!File.Exists(input)||Paths.IsLink(input))throw new IOException("Package file missing or linked: "+entry.RelativePath);
                if(new FileInfo(input).Length!=entry.Size)throw new IOException("Package file size changed: "+entry.RelativePath);
                Directory.CreateDirectory(Path.GetDirectoryName(output)!);
                using(var source=File.OpenRead(input))
                using(var dest=new FileStream(output,FileMode.CreateNew,FileAccess.Write,FileShare.None))
                    source.CopyTo(dest);
                using var readBack=File.OpenRead(output);
                var actual=Convert.ToHexString(SHA256.HashData(readBack));
                if(!string.Equals(actual,entry.Sha256,StringComparison.OrdinalIgnoreCase))
                    throw new IOException("SHA256 package integrity mismatch: "+entry.RelativePath);
            }
            File.WriteAllText(Path.Combine(staging,".complete"),fingerprint);
            Directory.Move(staging,final);
            return final;
        } finally {
            if(Directory.Exists(staging))Directory.Delete(staging,true);
        }
    }
}

