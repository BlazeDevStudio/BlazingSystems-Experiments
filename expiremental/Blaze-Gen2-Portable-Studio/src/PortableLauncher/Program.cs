using System.Diagnostics;
using System.Runtime.InteropServices;
using BlazeGen2;
namespace BlazeLauncher;
static class Program {
    [DllImport("user32.dll",CharSet=CharSet.Unicode)]static extern int MessageBoxW(nint owner,string message,string title,uint kind);
    [STAThread]static int Main(string[] args) {
        string baseDir=AppContext.BaseDirectory;string? log=null;
        try {
            var config=PortableConfig.Load(Path.Combine(baseDir,"PortableConfig.json"));
            var app=Paths.Inside(baseDir,config.AppDirectory);
            if(!Directory.Exists(app))throw new DirectoryNotFoundException("Packaged application directory missing.");
            var executable=ChooseExecutable(app,config);
            DisklessSafety.RejectUnverifiedRoblox(executable);
            if(Directory.EnumerateFiles(app,"RobloxPlayer*.exe",SearchOption.AllDirectories).Any())
                throw new NotSupportedException("Roblox game client detected; use official per-client installation.");
            if(!File.Exists(executable))throw new FileNotFoundException("Target executable missing",executable);
            foreach(var file in config.RequiredFiles)if(!File.Exists(Paths.Inside(app,file)))throw new FileNotFoundException("Required file missing",file);
            string data;
            switch(config.DataMode) {
                case DataMode.FullyLocal:
                    if(DisklessSafety.IsNetworkPath(baseDir))
                        throw new IOException("FullyLocal data cannot be shared between diskless clients.");
                    data=Path.Combine(baseDir,"Data");break;
                case DataMode.TemporarySession:data=Path.Combine(Path.GetTempPath(),"BlazeGen2",config.PackageId,Guid.NewGuid().ToString("N"));break;
                default:
                    data=string.IsNullOrWhiteSpace(config.WritableDataRoot)
                        ?DisklessSafety.ClientDataRoot(config)
                        :Environment.ExpandEnvironmentVariables(config.WritableDataRoot);
                    if(DisklessSafety.IsNetworkPath(data))
                        throw new IOException("Writable data must be local to each client; network share paths are unsafe.");
                    break;
            }
            Directory.CreateDirectory(data);var logs=Path.Combine(data,"Logs");Directory.CreateDirectory(logs);log=Path.Combine(logs,"launcher.log");
            if(DisklessSafety.IsNetworkPath(app) && !config.IsolateExecutablePerClient)
                throw new IOException("Unsafe shared executable directory: select client-local isolation.");
            // Never launch a writable program directly from the network share in isolated mode.
            if(config.IsolateExecutablePerClient) {
                var relative=Path.GetRelativePath(app,executable);
                var localApp=ClientIsolation.Prepare(baseDir,app,config,data);
                executable=Paths.Inside(localApp,relative);
                app=localApp;
                if(!File.Exists(executable))throw new FileNotFoundException("Local isolated executable missing",executable);
            }
            // Per-PC user-specific lock; other clients on the server cannot interfere with this handle.
            using var sessionLock=new FileStream(Path.Combine(data,"session.lock"),FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None);
            var work=Path.GetDirectoryName(executable)!;
            if(config.VersionStrategy==VersionStrategy.FixedExecutable && config.WorkingDirectory!=".")
                work=Paths.Inside(app,config.WorkingDirectory);
            if(!Directory.Exists(work))throw new DirectoryNotFoundException("Working directory missing: "+work);
            var start=new ProcessStartInfo(executable){WorkingDirectory=work,UseShellExecute=false,Arguments=config.Arguments};
            start.Environment["BLAZE_PORTABLE_DATA"]=data;
            if(config.RedirectEnvironmentFolders) {
                var roam=Path.Combine(data,"Roaming");var local=Path.Combine(data,"Local");Directory.CreateDirectory(roam);Directory.CreateDirectory(local);
                start.Environment["APPDATA"]=roam;start.Environment["LOCALAPPDATA"]=local;
            }
            foreach(var kv in config.Environment) {
                if(string.IsNullOrWhiteSpace(kv.Key)||kv.Key.Contains('=')||kv.Key.Contains('\0'))throw new InvalidDataException("Invalid environment variable name.");
                start.Environment[kv.Key]=kv.Value.Replace("{DATA}",data).Replace("{APP}",app);
            }
            File.AppendAllText(log,DateTimeOffset.UtcNow.ToString("O")+" starting "+executable+Environment.NewLine);
            using var process=Process.Start(start)??throw new InvalidOperationException("Process did not start.");
            process.WaitForExit();var exit=process.ExitCode;
            File.AppendAllText(log,DateTimeOffset.UtcNow.ToString("O")+" exit "+exit+Environment.NewLine);
            // Temporary directories may be held by child processes: do not delete live state.
            // Session lock is disposed at method exit; cleanup is best-effort only.
            return exit;
        } catch(Exception e) {
            try {
                var fallback=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"BlazeGen2","Errors");
                Directory.CreateDirectory(fallback);File.AppendAllText(Path.Combine(fallback,"launcher-errors.log"),DateTimeOffset.UtcNow.ToString("O")+" "+e+Environment.NewLine);
                if(log!=null)File.AppendAllText(log,e+Environment.NewLine);
            }catch(IOException){}
            MessageBoxW(0,"BlazePortableLauncher could not start the application.\n"+e.Message+"\nCheck BlazeGen2/Errors for diagnostics.","Blaze Gen2 Portable Studio",0x10);return 1;
        }
    }
    static string ChooseExecutable(string app,PortableConfig cfg) {
        if(cfg.VersionStrategy==VersionStrategy.FixedExecutable)return Paths.Inside(app,cfg.Executable);
        var versions=Paths.Inside(app,cfg.VersionDirectory);
        if(cfg.VersionStrategy==VersionStrategy.ConfiguredVersionPath)
            return Paths.Inside(Paths.Inside(versions,cfg.ConfiguredVersion),cfg.VersionExecutable);
        if(cfg.VersionStrategy==VersionStrategy.VersionManifest) {
            var version=File.ReadAllText(Paths.Inside(versions,cfg.VersionManifestFile)).Trim();
            return Paths.Inside(Paths.Inside(versions,version),cfg.VersionExecutable);
        }
        if(cfg.VersionStrategy==VersionStrategy.VersionDirectoryDiscovery) {
            if(!Directory.Exists(versions))throw new DirectoryNotFoundException("Versions directory missing.");
            var candidates=new List<(Version version,string path)>();
            foreach(var dir in Directory.GetDirectories(versions)) {
                if(Paths.IsLink(dir))continue;
                var versionName=Path.GetFileName(dir).TrimStart('v','V');
                if(!Version.TryParse(versionName,out var v))continue; // Ignore folders without parseable versions.
                var file=Paths.Inside(dir,cfg.VersionExecutable);
                if(File.Exists(file))candidates.Add((v,file));
            }
            return candidates.OrderByDescending(x=>x.version).Select(x=>x.path).FirstOrDefault()??throw new FileNotFoundException("No complete compatible version found.");
        }
        throw new NotSupportedException("Application-specific version profile needs an installed resolver.");
    }
}

