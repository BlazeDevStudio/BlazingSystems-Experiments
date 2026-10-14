using System.Diagnostics;
static class Program {
    static int Main(string[] args) {
        try{
            if(args.Contains("--child")) {
                File.WriteAllText(Path.Combine(Environment.GetEnvironmentVariable("BLAZE_PORTABLE_DATA")!,"child.txt"),"ok");return 0;
            }
            if(args.Contains("--hold")) {
                var holdData=Environment.GetEnvironmentVariable("BLAZE_PORTABLE_DATA");
                if(string.IsNullOrWhiteSpace(holdData))return 11;
                var running=Path.Combine(holdData,"Concurrent");Directory.CreateDirectory(running);
                var station=Environment.GetEnvironmentVariable("BLAZE_STATION_ID")??"unknown";
                var ready=Path.Combine(running,station+"-"+Environment.ProcessId+".ready");
                File.WriteAllText(ready,Environment.GetEnvironmentVariable("APPDATA")+"\n"+Environment.GetEnvironmentVariable("LOCALAPPDATA"));
                Thread.Sleep(4000);
                File.Delete(ready);
                return 0;
            }
            var data=Environment.GetEnvironmentVariable("BLAZE_PORTABLE_DATA");
            if(string.IsNullOrWhiteSpace(data))return 11;
            if(!File.Exists(Path.Combine(AppContext.BaseDirectory,"Resources","test.txt")))return 10;
            if(!args.Contains("--synthetic-argument"))return 12;
            Directory.CreateDirectory(data);
            File.WriteAllText(Path.Combine(data,"test-result.txt"),File.ReadAllText(Path.Combine(AppContext.BaseDirectory,"Resources","test.txt")));
            using var child=Process.Start(new ProcessStartInfo(Environment.ProcessPath!,"--child"){UseShellExecute=false});
            if(child==null)return 14;
            child.WaitForExit();if(child.ExitCode!=0)return 15;
            return 0;
        }catch(Exception e){Console.Error.WriteLine(e);return 13;}
    }
}

