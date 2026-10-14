using System.Diagnostics;
using BlazeGen2;
class Tests {
    static int successes;
    static void Check(bool ok,string message){if(!ok)throw new Exception("FAILED: "+message);Console.WriteLine("PASS: "+message);successes++;}
    static void Pe(string p){
        using var f=File.OpenRead(p);using var b=new BinaryReader(f);
        Check(b.ReadUInt16()==0x5A4D,"MZ signature: "+Path.GetFileName(p));
        f.Position=0x3C;var pos=b.ReadInt32();f.Position=pos;
        Check(b.ReadUInt32()==0x00004550,"PE signature: "+Path.GetFileName(p));
    }
    static Process Start(string path,string? args=null,string? stationId=null) {
        var start=new ProcessStartInfo(path,args??""){UseShellExecute=false};
        if(stationId!=null)start.Environment["BLAZE_STATION_ID"]=stationId;
        return Process.Start(start)??throw new Exception("Cannot launch "+path);
    }
    static int Run(string path,string? args=null,int seconds=60) {
        using var p=Start(path,args);
        if(!p.WaitForExit(seconds*1000)){p.Kill(entireProcessTree:true);throw new TimeoutException("Timed out: "+path);}
        return p.ExitCode;
    }
    static async Task Main(string[] args){
        if(args.Length!=3)throw new ArgumentException("Pass SyntheticApp.exe, BlazePortableLauncher.exe, Create.exe");
        foreach(var file in args)Pe(file);
        var home=Path.Combine(Path.GetTempPath(),"Blaze Gen2 QA "+Guid.NewGuid().ToString("N"));
        var source=Path.Combine(home,"Program with spaces ü");var release=Path.Combine(home,"Portable Test Package");
        Directory.CreateDirectory(source);
        try {
            File.Copy(args[0],Path.Combine(source,"SyntheticApp.exe"));
            var res=Path.Combine(source,"Resources");Directory.CreateDirectory(res);File.WriteAllText(Path.Combine(res,"test.txt"),"synthetic payload");
            // App-side extra native DLL and nearby support files are copied, not reinterpreted.
            File.WriteAllText(Path.Combine(source,"SyntheticHelper.dll"),"synthetic sidecar fixture");
            var found=Analyzer.Analyze(Path.Combine(source,"SyntheticApp.exe"));
            Check(found.Files.Count>=3,"Static file inventory includes resources and supporting DLL");
            Check(found.MainExecutable.EndsWith("SyntheticApp.exe"),"Main executable recognized");
            Check(found.Classification!=CompatibilityLevel.Unsupported,"Generic app receives a non-guarantee assessment");
            var steps=new List<int>();
            var progress=new Progress<int>(x=>steps.Add(x));
            var result=await PackageBuilder.BuildAsync(new ConversionOptions{SourceExecutable=Path.Combine(source,"SyntheticApp.exe"),
                Destination=release,Arguments="--synthetic-argument",DataMode=DataMode.FullyLocal},args[1],progress);
            Check(File.Exists(result),"Generated launcher EXE exists");
            Pe(result);
            Check(File.Exists(Path.Combine(release,"PortableConfig.json")),"Config produced");
            Check(File.Exists(Path.Combine(release,"App","Executables","Resources","test.txt")),"Resource directory copied");
            Check(File.Exists(Path.Combine(release,"App","Executables","SyntheticHelper.dll")),"Sidecar DLL copied");
            Check(File.Exists(Path.Combine(source,"SyntheticApp.exe")),"Source retained");
            var config=PortableConfig.Load(Path.Combine(release,"PortableConfig.json"));
            Check(config.Executable=="SyntheticApp.exe","Relative executable path stored");
            Check(Run(result)==0,"Portable launcher starts synthetic app and argument");
            Check(File.ReadAllText(Path.Combine(release,"Data","test-result.txt"))=="synthetic payload","Portable data writable and resource read");
            Check(File.Exists(Path.Combine(release,"Data","child.txt")),"Child process inherits portable environment");
            Check(File.Exists(Path.Combine(release,"Data","Logs","launcher.log")),"Launcher diagnostic log");
            // Changed parent location simulates a changed drive/root; all paths must remain relative.
            var relocated=Path.Combine(home,"Another Location");
            Directory.Move(release,relocated);
            var renamed=Path.Combine(relocated,Path.GetFileName(result));
            Check(Run(renamed)==0,"Launcher works after package relocation");
            // Missing resource must result in a non-success process exit.
            File.Delete(Path.Combine(relocated,"App","Executables","Resources","test.txt"));
            Check(Run(renamed)==10,"Missing application resource reports failure exit code");
            var bad=Path.Combine(home,"Invalid package");
            var rejected=false;
            try{await PackageBuilder.BuildAsync(new ConversionOptions{SourceExecutable=Path.Combine(source,"SyntheticApp.exe"),Destination=source+"\\inside"},args[1]);}
            catch(InvalidOperationException){rejected=true;}
            Check(rejected,"Unsafe nested destination rejected");
            var token=new CancellationToken(true);var cancelled=false;
            try{await PackageBuilder.BuildAsync(new ConversionOptions{SourceExecutable=Path.Combine(source,"SyntheticApp.exe"),Destination=bad},args[1],null,token);}
            catch(OperationCanceledException){cancelled=true;}
            Check(cancelled&&!Directory.Exists(bad),"Cancellation cleans staging without touching source");
            // Version directory resolver only accepts parseable version and an existing target.
            var versionPkg=Path.Combine(home,"Versioned Package");
            var versionExe=await PackageBuilder.BuildAsync(new ConversionOptions{SourceExecutable=Path.Combine(source,"SyntheticApp.exe"),Destination=versionPkg,
                Arguments="--synthetic-argument",DataMode=DataMode.FullyLocal},args[1]);
            var versionRoot=Path.Combine(versionPkg,"App","Executables","Versions");
            foreach(var version in new[]{"1.0","2.0"}) {
                var v=Path.Combine(versionRoot,version);Directory.CreateDirectory(v);
                File.Copy(Path.Combine(source,"SyntheticApp.exe"),Path.Combine(v,"SyntheticApp.exe"));
                Directory.CreateDirectory(Path.Combine(v,"Resources"));
                File.WriteAllText(Path.Combine(v,"Resources","test.txt"),version);
            }
            var c=PortableConfig.Load(Path.Combine(versionPkg,"PortableConfig.json"));
            c.VersionStrategy=VersionStrategy.VersionDirectoryDiscovery;c.VersionDirectory="Versions";c.VersionExecutable="SyntheticApp.exe";
            c.Save(Path.Combine(versionPkg,"PortableConfig.json"));
            Check(Run(versionExe)==0,"Version-directory launcher finds executable");
            Check(File.ReadAllText(Path.Combine(versionPkg,"Data","test-result.txt"))=="2.0","Highest parseable complete version used");
            // v1.1.0: every client must get private executable and data roots.
            var isolatedPackage=Path.Combine(home,"Diskless Shared Source");
            var isolatedLaunch=await PackageBuilder.BuildAsync(new ConversionOptions{
                SourceExecutable=Path.Combine(source,"SyntheticApp.exe"), Destination=isolatedPackage,
                Arguments="--synthetic-argument",DataMode=DataMode.PerClientWritable,IsolateExecutablePerClient=true
            },args[1]);
            var isoCfg=PortableConfig.Load(Path.Combine(isolatedPackage,"PortableConfig.json"));
            Check(isoCfg.IsolateExecutablePerClient,"v1.1 builder opts into client-local execution");
            Check(File.Exists(Path.Combine(isolatedPackage,"FileManifest.json")),"SHA256 manifest is packaged");
            var isoRoot=DisklessSafety.ClientDataRoot(isoCfg);
            Check(!DisklessSafety.IsNetworkPath(isoRoot),"Client writable root is local");
            Check(Run(isolatedLaunch)==0,"Isolated package launcher starts test app");
            Check(File.Exists(Path.Combine(isoRoot,"test-result.txt")),"Isolated app writes to per-client state");
            var manifest=PackageManifest.Load(Path.Combine(isolatedPackage,"FileManifest.json"));
            Check(manifest.Files.Any(x=>x.RelativePath=="Resources/test.txt"&&x.Sha256.Length==64),"Manifest records per-file SHA256");
            var appRoot=Path.Combine(isolatedPackage,"App","Executables");
            var privateA=ClientIsolation.Prepare(isolatedPackage,appRoot,isoCfg,Path.Combine(home,"Private A"));
            var privateB=ClientIsolation.Prepare(isolatedPackage,appRoot,isoCfg,Path.Combine(home,"Private B"));
            Check(privateA!=privateB && File.Exists(Path.Combine(privateA,"Resources","test.txt")) &&
                File.Exists(Path.Combine(privateB,"Resources","test.txt")),"Two simulated clients use separate game executable caches");
            File.WriteAllText(Path.Combine(privateA,"Resources","test.txt"),"private-client-a");
            Check(File.ReadAllText(Path.Combine(privateB,"Resources","test.txt"))=="synthetic payload",
                "Client A modifications cannot affect client B");
            Check(File.ReadAllText(Path.Combine(appRoot,"Resources","test.txt"))=="synthetic payload",
                "Client modifications do not affect shared package");
            var corrupt=Path.Combine(home,"Private C");
            File.WriteAllText(Path.Combine(appRoot,"Resources","test.txt"),"corrupt package resource");
            var detected=false;
            try { ClientIsolation.Prepare(isolatedPackage,appRoot,isoCfg,corrupt); }
            catch(IOException){detected=true;}
            Check(detected,"Manifest hash mismatch rejects modified source");
            Check(Directory.GetDirectories(Path.Combine(corrupt,"AppCache"),"staging-*").Length==0,
                "Failed local mirror cleanup removes staging");
            var robloxRoot=Path.Combine(home,"Roblox");
            Directory.CreateDirectory(robloxRoot);
            var mockRoblox=Path.Combine(robloxRoot,"RobloxPlayerBeta.exe");
            File.Copy(args[0],mockRoblox);
            var mockResources=Path.Combine(robloxRoot,"Resources");Directory.CreateDirectory(mockResources);
            File.WriteAllText(Path.Combine(mockResources,"test.txt"),"synthetic payload");
            var rb=Analyzer.Analyze(mockRoblox);
            Check(rb.Classification!=CompatibilityLevel.Unsupported,"Roblox candidate remains available with an isolation warning");
            var robloxPackage=Path.Combine(home,"Roblox Station Package");
            var robloxLaunch=await PackageBuilder.BuildAsync(new ConversionOptions{
                SourceExecutable=mockRoblox,Destination=robloxPackage,Arguments="--synthetic-argument",
                DataMode=DataMode.PerClientWritable,IsolateExecutablePerClient=true
            },args[1]);
            var robloxConfig=PortableConfig.Load(Path.Combine(robloxPackage,"PortableConfig.json"));
            Check(robloxConfig.IsolateExecutablePerClient,"Roblox package forces client-local application files");
            Check(robloxConfig.RedirectEnvironmentFolders,"Roblox package forces private app-data environment roots");
            File.Delete(Path.Combine(robloxPackage,"FileManifest.json"));
            var robloxData=DisklessSafety.ClientDataRoot(robloxConfig);
            var robloxExit=Run(robloxLaunch);
            if(robloxExit!=0) {
                var diagnostic=Path.Combine(robloxData,"Logs","launcher.log");
                if(File.Exists(diagnostic))Console.WriteLine("Roblox isolation fixture launcher log:\n"+File.ReadAllText(diagnostic));
            }
            Check(robloxExit==0,"Roblox-named legacy package starts from a station-local snapshot without a product block");
            var profileRoots=File.ReadAllLines(Path.Combine(robloxData,"profile-roots.txt"));
            Check(profileRoots.Length==2 &&
                Path.GetFullPath(profileRoots[0])==Path.GetFullPath(DisklessSafety.ProfileAppData(robloxData,"Roaming")) &&
                Path.GetFullPath(profileRoots[1])==Path.GetFullPath(DisklessSafety.ProfileAppData(robloxData,"Local")),
                "Roblox client receives station-private APPDATA and LOCALAPPDATA");
            var stationA=DisklessSafety.ClientDataRoot(robloxConfig,"PISONET-PC-01",Path.Combine(home,"Station A LocalAppData"));
            var stationB=DisklessSafety.ClientDataRoot(robloxConfig,"PISONET-PC-02",Path.Combine(home,"Station B LocalAppData"));
            Check(stationA!=stationB &&
                DisklessSafety.ProfileAppData(stationA,"Local")!=DisklessSafety.ProfileAppData(stationB,"Local"),
                "Distinct station identities produce separate persistent profile roots");
            using(var stationOne=Start(robloxLaunch,null,"PISONET-PC-01"))
            using(var stationTwo=Start(robloxLaunch,null,"PISONET-PC-02")) {
                if(!stationOne.WaitForExit(60000)){stationOne.Kill(true);throw new TimeoutException("Station one timed out");}
                if(!stationTwo.WaitForExit(60000)){stationTwo.Kill(true);throw new TimeoutException("Station two timed out");}
                Check(stationOne.ExitCode==0 && stationTwo.ExitCode==0,"Two Roblox-named station clients launch simultaneously");
            }
            var runnerLocalAppData=Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            var stationOneData=DisklessSafety.ClientDataRoot(robloxConfig,"PISONET-PC-01",runnerLocalAppData);
            var stationTwoData=DisklessSafety.ClientDataRoot(robloxConfig,"PISONET-PC-02",runnerLocalAppData);
            Check(File.Exists(Path.Combine(stationOneData,"profile-roots.txt")) &&
                File.Exists(Path.Combine(stationTwoData,"profile-roots.txt")) &&
                !File.ReadAllText(Path.Combine(stationOneData,"profile-roots.txt")).Equals(
                    File.ReadAllText(Path.Combine(stationTwoData,"profile-roots.txt")),StringComparison.Ordinal),
                "Concurrent station clients write separate app-data profiles");
            Check(File.Exists(mockRoblox),"Packaging retains the original Roblox client source");
            Console.WriteLine("ALL "+successes+" CHECKS PASSED");
        } finally {try{Directory.Delete(home,true);}catch(IOException){}}
    }
}

