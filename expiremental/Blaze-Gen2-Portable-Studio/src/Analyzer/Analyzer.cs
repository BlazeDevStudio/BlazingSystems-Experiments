using System.Reflection.PortableExecutable;
using System.Text;
using Microsoft.Win32;
namespace BlazeGen2;
public static class Analyzer {
    static readonly string[] CriticalHints={"easyanticheat","battleye","vgk.sys","vanguard","anticheat","denuvo","secdrv","driverstore","kernelmode"};
    static readonly string[] SystemLibraries={"kernel32.dll","user32.dll","gdi32.dll","ntdll.dll","advapi32.dll","shell32.dll","ole32.dll","oleaut32.dll","ws2_32.dll","comdlg32.dll","comctl32.dll","ucrtbase.dll","msvcrt.dll"};
    public static Task<AnalysisReport> AnalyzeAsync(string executable,CancellationToken ct=default)=>Task.Run(()=>Analyze(executable,ct),ct);
    public static AnalysisReport Analyze(string executable,CancellationToken ct=default) {
        executable=Path.GetFullPath(executable);
        if(!File.Exists(executable)||!executable.EndsWith(".exe",StringComparison.OrdinalIgnoreCase))
            throw new FileNotFoundException("Select an existing Windows EXE.",executable);
        var root=Path.GetDirectoryName(executable)!;
        if(Paths.IsLink(root)||Paths.IsLink(executable))throw new InvalidOperationException("Links are not supported as source roots or executable.");
        var r=new AnalysisReport{MainExecutable=executable,SourceDirectory=root,DisplayName=Path.GetFileNameWithoutExtension(executable)};
        if(DisklessSafety.IsRoblox(executable)) {
            r.Classification=CompatibilityLevel.Unsupported;
            r.Warnings.Add("Roblox is not verified for multi-PC portable use. Sharing authenticated game state can transfer account sessions.");
            r.Evidence.Add("Roblox multi-device same-account Error 264 is enforced by Roblox servers; use official client and separate accounts.");
            return r;
        }
        var stack=new Stack<string>();stack.Push(root);
        while(stack.Count>0) {
            ct.ThrowIfCancellationRequested();var dir=stack.Pop();
            foreach(var sub in Directory.EnumerateDirectories(dir)) {ct.ThrowIfCancellationRequested();if(Paths.IsLink(sub)){r.Warnings.Add("Skipped directory link: "+sub);continue;}stack.Push(sub);}
            foreach(var file in Directory.EnumerateFiles(dir)) {
                ct.ThrowIfCancellationRequested();
                if(Paths.IsLink(file)){r.Warnings.Add("Skipped file link: "+file);continue;}
                var info=new FileInfo(file);r.TotalBytes+=info.Length;r.Files.Add(Path.GetRelativePath(root,file));
                var name=Path.GetFileName(file).ToLowerInvariant();
                if(CriticalHints.Any(h=>name.Contains(h)))r.Warnings.Add("Potential protected driver, anti-cheat, or licensing component: "+name);
                if(name.EndsWith(".sys"))r.Warnings.Add("Driver file requires a system-level installation: "+name);
            }
        }
        try {r.ImportedDlls=ReadPeImports(executable).Distinct(StringComparer.OrdinalIgnoreCase).ToList();}
        catch(Exception e) when(e is IOException or InvalidDataException or ArgumentException){r.Warnings.Add("PE import analysis incomplete: "+e.Message);}
        var dlls=r.Files.Select(Path.GetFileName).ToHashSet(StringComparer.OrdinalIgnoreCase);
        foreach(var dep in r.ImportedDlls)if(!SystemLibraries.Contains(dep,StringComparer.OrdinalIgnoreCase) && !dep.StartsWith("api-ms-win-",StringComparison.OrdinalIgnoreCase) && !dep.StartsWith("ext-ms-win-",StringComparison.OrdinalIgnoreCase) && !dlls.Contains(dep))r.Warnings.Add("Unbundled imported DLL (may be system/runtime-provided): "+dep);
        if(r.Files.Any(x=>x.EndsWith(".runtimeconfig.json",StringComparison.OrdinalIgnoreCase)))r.Evidence.Add(".NET runtime configuration found; check self-contained vs framework-dependent deployment.");
        if(r.Files.Any(x=>x.EndsWith(".manifest",StringComparison.OrdinalIgnoreCase)))r.Evidence.Add("Application manifest detected; inspect requested execution level.");
        r.Evidence.Add("Static inventory: "+r.Files.Count+" files; "+r.TotalBytes+" bytes; "+r.ImportedDlls.Count+" direct DLL imports.");
        r.Evidence.Add("Static scanning cannot prove complete application portability.");
        if(r.Files.Any(f=>DisklessSafety.IsRoblox(f))) {r.Warnings.Add("Roblox product content detected: sharing portable auth/cache is unsafe.");r.Classification=CompatibilityLevel.Unsupported;}
        else if(r.Warnings.Any(w=>w.Contains("anti-cheat",StringComparison.OrdinalIgnoreCase)||w.Contains("Driver file")))r.Classification=CompatibilityLevel.HighRiskManualConfiguration;
        else if(r.Warnings.Any(w=>w.StartsWith("Unbundled")))r.Classification=CompatibilityLevel.RequiresExternalDependencies;
        else if(r.Files.Count==1)r.Classification=CompatibilityLevel.PartiallyPortable;
        else r.Classification=CompatibilityLevel.FullyPortableCandidate;
        return r;
    }
    // Reads direct PE imports; delay-load, dynamic LoadLibrary and runtime dependencies are outside scope.
    public static List<string> ReadPeImports(string exe) {
        using var stream=File.OpenRead(exe);using var pe=new PEReader(stream);
        if(pe.PEHeaders.PEHeader==null)throw new InvalidDataException("Not a valid PE file.");
        var d=pe.PEHeaders.PEHeader.ImportTableDirectory;
        var list=new List<string>();if(d.RelativeVirtualAddress==0)return list;
        int Offset(int rva) {
            foreach(var s in pe.PEHeaders.SectionHeaders) {
                var limit=Math.Max(s.VirtualSize,s.SizeOfRawData);
                if(rva>=s.VirtualAddress && (long)rva<s.VirtualAddress+limit)return checked(rva-s.VirtualAddress+s.PointerToRawData);
            }
            throw new InvalidDataException("PE RVA outside sections.");
        }
        using var br=new BinaryReader(stream,Encoding.ASCII,leaveOpen:true);
        var pos=Offset(d.RelativeVirtualAddress);
        for(var i=0;i<512;i++) {
            if(pos+20>stream.Length)break;
            stream.Position=pos;
            var original=br.ReadUInt32();var stamp=br.ReadUInt32();var chain=br.ReadUInt32();var nameRva=br.ReadUInt32();var first=br.ReadUInt32();
            if(original==0&&stamp==0&&chain==0&&nameRva==0&&first==0)break;
            if(nameRva!=0) {
                stream.Position=Offset(checked((int)nameRva));
                var bytes=new List<byte>();for(int c=0;c<256&&stream.Position<stream.Length;c++){var b=br.ReadByte();if(b==0)break;bytes.Add(b);}
                var dll=Encoding.ASCII.GetString(bytes.ToArray());if(dll.Length>0)list.Add(dll);
            }
            pos+=20;
        }
        return list;
    }
    public static List<InstalledEntry> DiscoverInstalled() {
        var entries=new Dictionary<string,InstalledEntry>(StringComparer.OrdinalIgnoreCase);
        foreach(var hive in new[]{RegistryHive.LocalMachine,RegistryHive.CurrentUser})
        foreach(var view in new[]{RegistryView.Registry32,RegistryView.Registry64}) {
            try {
                using var baseKey=RegistryKey.OpenBaseKey(hive,view);
                using var uninstall=baseKey.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall");
                if(uninstall==null)continue;
                foreach(var keyName in uninstall.GetSubKeyNames()) {
                    using var key=uninstall.OpenSubKey(keyName);if(key==null)continue;
                    var name=key.GetValue("DisplayName") as string;var dir=key.GetValue("InstallLocation") as string;
                    if(string.IsNullOrWhiteSpace(name)||string.IsNullOrWhiteSpace(dir)||!Directory.Exists(dir))continue;
                    try {
                        var exes=Directory.EnumerateFiles(dir,"*.exe",SearchOption.TopDirectoryOnly).Take(30).ToList();
                        if(exes.Count==0)continue;
                        var preferred=exes.FirstOrDefault(x=>string.Equals(Path.GetFileNameWithoutExtension(x),name,StringComparison.OrdinalIgnoreCase))??exes[0];
                        entries.TryAdd(dir,new InstalledEntry{Name=name,Version=key.GetValue("DisplayVersion") as string??"",Directory=dir,Executable=preferred});
                    } catch(UnauthorizedAccessException){}
                }
            } catch(Exception e) when(e is UnauthorizedAccessException or System.Security.SecurityException or IOException){}
        }
        return entries.Values.OrderBy(x=>x.Name).ToList();
    }
    public static List<string> DiscoverExecutables(string dir) {
        if(!Directory.Exists(dir))throw new DirectoryNotFoundException(dir);
        return Directory.EnumerateFiles(dir,"*.exe",SearchOption.AllDirectories)
            .Where(x=>!Paths.IsLink(x)).OrderBy(x=>x.Count(c=>c==Path.DirectorySeparatorChar)).ThenBy(x=>x.Length).ToList();
    }
}

