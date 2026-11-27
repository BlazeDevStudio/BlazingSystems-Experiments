using System.Security.Cryptography;
namespace BlazeGen2;
public static class PackageBuilder {
    public static async Task<string> BuildAsync(ConversionOptions options,string compiledLauncher,IProgress<int>? progress=null,CancellationToken ct=default) {
        var src=Path.GetFullPath(options.SourceExecutable);
        if(!File.Exists(src))throw new FileNotFoundException("Application EXE missing",src);
        var root=Path.GetDirectoryName(src)!;var destination=Path.GetFullPath(options.Destination);
        DisklessSafety.RejectUnverifiedRoblox(src);
        if(Directory.EnumerateFiles(root,"RobloxPlayer*.exe",SearchOption.AllDirectories).Any())
            throw new NotSupportedException("Roblox files detected. Portable Roblox multi-PC sessions are unverified and blocked.");
        if(options.DataMode==DataMode.FullyLocal && DisklessSafety.IsNetworkPath(destination))
            throw new InvalidOperationException("FullyLocal data mode cannot write directly into a shared network package.");
        if(options.DataMode==DataMode.PerClientWritable && !options.IsolateExecutablePerClient && DisklessSafety.IsNetworkPath(destination))
            throw new InvalidOperationException("Shared network execution requires the isolated per-client local application cache.");
        if(Paths.IsWithin(destination,root)||Paths.IsWithin(root,destination))
            throw new InvalidOperationException("Source and destination directories must not overlap.");
        if(File.Exists(destination)||Directory.Exists(destination))throw new IOException("Destination already exists. Choose an empty new package path.");
        if(!File.Exists(compiledLauncher))throw new FileNotFoundException("Compiled launcher template missing",compiledLauncher);
        Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
        var staging=destination+".staging-"+Guid.NewGuid().ToString("N");
        try {
            Directory.CreateDirectory(staging);
            var app=Path.Combine(staging,"App","Executables");Directory.CreateDirectory(app);
            var files=new List<(string path,string relative,long bytes)>();
            var dirs=new Stack<string>();dirs.Push(root);
            while(dirs.Count>0) {
                ct.ThrowIfCancellationRequested();
                var dir=dirs.Pop();if(Paths.IsLink(dir))throw new IOException("Source has linked directory: "+dir);
                foreach(var sub in Directory.EnumerateDirectories(dir))dirs.Push(sub);
                foreach(var file in Directory.EnumerateFiles(dir)) {
                    if(Paths.IsLink(file))throw new IOException("Source has linked file: "+file);
                    files.Add((file,Path.GetRelativePath(root,file),new FileInfo(file).Length));
                }
            }
            var manifest=new PackageManifest();
            long total=Math.Max(1,files.Sum(f=>f.bytes)),copied=0;
            foreach(var f in files) {
                ct.ThrowIfCancellationRequested();
                var target=Paths.Inside(app,f.relative);Directory.CreateDirectory(Path.GetDirectoryName(target)!);
                byte[] expectedHash;
                using(var input=new FileStream(f.path,FileMode.Open,FileAccess.Read,FileShare.Read,81920,true))
                using(var output=new FileStream(target,FileMode.CreateNew,FileAccess.Write,FileShare.None,81920,true)) {
                    using var srcHash=IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
                    var buffer=new byte[131072];int n;
                    while((n=await input.ReadAsync(buffer,ct))>0) {
                        ct.ThrowIfCancellationRequested();srcHash.AppendData(buffer,0,n);
                        await output.WriteAsync(buffer.AsMemory(0,n),ct);copied+=n;progress?.Report((int)Math.Min(98,copied*98/total));
                    }
                    await output.FlushAsync(ct);
                    expectedHash=srcHash.GetHashAndReset();
                }
                using(var diskFile=new FileStream(target,FileMode.Open,FileAccess.Read,FileShare.Read,81920,true)) {
                    var actualHash=await SHA256.HashDataAsync(diskFile,ct);
                    if(!expectedHash.SequenceEqual(actualHash))throw new IOException("On-disk SHA256 copy verification failed: "+f.relative);
                }
                manifest.Files.Add(new FileManifestEntry{
                    RelativePath=f.relative.Replace('\\','/'),Size=f.bytes,
                    Sha256=Convert.ToHexString(expectedHash).ToLowerInvariant()
                });
            }
            foreach(var dir in new[]{"Data/Roaming","Data/Local","Data/Config","Data/Saves","Runtime","Cache","Logs","Backups"})
                Directory.CreateDirectory(Path.Combine(staging,dir.Replace('/',Path.DirectorySeparatorChar)));
            var name=Path.GetFileName(destination);
            var launch=Path.Combine(staging,name+".exe");
            File.Copy(compiledLauncher,launch);
            var config=new PortableConfig{
                DisplayName=name,Executable=Path.GetRelativePath(root,src).Replace('\\','/'),
                Arguments=options.Arguments,DataMode=options.DataMode,RedirectEnvironmentFolders=options.RedirectEnvironmentFolders,
                WorkingDirectory=".",RequiredFiles=new(){Path.GetRelativePath(root,src).Replace('\\','/')}
            };
            config.IsolateExecutablePerClient=options.IsolateExecutablePerClient;
            config.Save(Path.Combine(staging,"PortableConfig.json"));
            manifest.Save(Path.Combine(staging,"FileManifest.json"));
            File.WriteAllText(Path.Combine(staging,"PACKAGE_INFO.txt"),"Created by Blaze Gen2 Portable Studio v1.1.0 (experimental). Portability not guaranteed.");
            ct.ThrowIfCancellationRequested();
            Directory.Move(staging,destination);
            progress?.Report(100);return Path.Combine(destination,name+".exe");
        } finally {
            if(Directory.Exists(staging))Directory.Delete(staging,true);
        }
    }
}

