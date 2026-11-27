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
    static int Run(string path,string? args=null,int seconds=60) {
        using var p=Process.Start(new ProcessStartInfo(path,args??""){UseShellExecute=false})??throw new Exception("Cannot launch "+path);
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
            var rb=Analyzer.Analyze(mockRoblox);
            Check(rb.Classification==CompatibilityLevel.Unsupported,"Roblox candidate explicitly classified unsupported");
            var blocked=false;var shouldNotExist=Path.Combine(home,"Rejected Roblox Package");
            try {
                await PackageBuilder.BuildAsync(new ConversionOptions{SourceExecutable=mockRoblox,Destination=shouldNotExist},args[1]);
            }catch(NotSupportedException){blocked=true;}
            Check(blocked&&!Directory.Exists(shouldNotExist),"Roblox multi-PC portable packaging safely blocked");
            Check(File.Exists(mockRoblox),"Blocked Roblox source is never modified");
            Console.WriteLine("ALL "+successes+" CHECKS PASSED");
        } finally {try{Directory.Delete(home,true);}catch(IOException){}}
    }
}

