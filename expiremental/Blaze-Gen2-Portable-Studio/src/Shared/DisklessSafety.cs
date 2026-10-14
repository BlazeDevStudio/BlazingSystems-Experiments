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
    public static bool RequiresStationIsolation(string path) => IsRoblox(path);

    public static string SafeMachineName() {
        var configured=Environment.GetEnvironmentVariable("BLAZE_STATION_ID");
        var raw=string.IsNullOrWhiteSpace(configured)?Environment.MachineName:configured;
        var name=new string(raw.Where(c=>char.IsLetterOrDigit(c)||c=='-'||c=='_').ToArray());
        return string.IsNullOrWhiteSpace(name)?"UnknownMachine":name;
    }
    public static bool IsNetworkPath(string path) {
        var full=Path.GetFullPath(path);
        if(full.StartsWith(@"\\",StringComparison.Ordinal))return true;
        try {
            var root=Path.GetPathRoot(full);
            return root!=null && new DriveInfo(root).DriveType==DriveType.Network;
        } catch(IOException){return true;}
    }
    public static string ClientDataRoot(PortableConfig config) {
        var local=Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        return ClientDataRoot(config,SafeMachineName(),local);
    }
    public static string ClientDataRoot(PortableConfig config,string stationId,string localAppData) {
        if(string.IsNullOrWhiteSpace(localAppData)||IsNetworkPath(localAppData))
            throw new IOException("Client LOCALAPPDATA must be on a local writable disk; a shared user profile is not safe.");
        var station=new string(stationId.Where(c=>char.IsLetterOrDigit(c)||c=='-'||c=='_').ToArray());
        if(string.IsNullOrWhiteSpace(station))throw new IOException("Set a unique BLAZE_STATION_ID or Windows computer name for each diskless station.");
        // LocalAppData is scoped to the signed-in Windows profile; station ID prevents collisions between cloned stations.
        return Path.Combine(Path.GetFullPath(localAppData),"BlazeGen2","Clients",station,config.PackageId);
    }
    public static string ProfileAppData(string clientDataRoot,string kind) {
        if(!kind.Equals("Roaming",StringComparison.OrdinalIgnoreCase)&&!kind.Equals("Local",StringComparison.OrdinalIgnoreCase))
            throw new ArgumentException("Profile data kind must be Roaming or Local.",nameof(kind));
        return Path.Combine(clientDataRoot,"WindowsProfile",kind);
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
        var roblox=DisklessSafety.RequiresStationIsolation(appRoot)
            ||Directory.EnumerateFiles(appRoot,"RobloxPlayer*.exe",SearchOption.AllDirectories).Any();
        if(!cfg.IsolateExecutablePerClient&&!roblox)return appRoot;
        if(DisklessSafety.IsNetworkPath(localData))
            throw new IOException("Client data folder must be physically local, not SMB/UNC.");
        var manifestFile=Path.Combine(packageRoot,"FileManifest.json");
        var hasManifest=File.Exists(manifestFile);
        var manifest=hasManifest?PackageManifest.Load(manifestFile):CreateManifest(appRoot);
        if(manifest.SchemaVersion!=1||manifest.Files.Count<1)throw new InvalidDataException("Invalid manifest.");
        var manifestBytes=hasManifest?File.ReadAllBytes(manifestFile):JsonSerializer.SerializeToUtf8Bytes(manifest);
        var fingerprint=Convert.ToHexString(SHA256.HashData(manifestBytes)).ToLowerInvariant();
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
    static PackageManifest CreateManifest(string appRoot) {
        // Legacy packages have no builder manifest. Snapshot and hash their files before making a station-local copy.
        var manifest=new PackageManifest();
        var dirs=new Stack<string>();dirs.Push(appRoot);
        while(dirs.Count>0) {
            var dir=dirs.Pop();
            if(Paths.IsLink(dir))throw new IOException("Application contains a linked directory: "+dir);
            foreach(var sub in Directory.EnumerateDirectories(dir)) {
                if(Paths.IsLink(sub))throw new IOException("Application contains a linked directory: "+sub);
                dirs.Push(sub);
            }
            foreach(var file in Directory.EnumerateFiles(dir)) {
                if(Paths.IsLink(file))throw new IOException("Application contains a linked file: "+file);
                using var input=File.OpenRead(file);
                manifest.Files.Add(new FileManifestEntry{
                    RelativePath=Path.GetRelativePath(appRoot,file).Replace('\\','/'),
                    Size=input.Length,Sha256=Convert.ToHexString(SHA256.HashData(input)).ToLowerInvariant()
                });
            }
        }
        manifest.Files=manifest.Files.OrderBy(x=>x.RelativePath,StringComparer.OrdinalIgnoreCase).ToList();
        return manifest;
    }
}

