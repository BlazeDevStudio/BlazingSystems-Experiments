using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Effects;
using Microsoft.Win32;
using BlazeGen2;
namespace BlazeGen2Studio;

public sealed class StudioWindow:Window {
    static readonly SolidColorBrush Back=Brush("#10141C"),Panel=Brush("#181F2C"),Panel2=Brush("#242E3E"),Ink=Brush("#E9EFFA"),Muted=Brush("#A1B0C7"),Accent=Brush("#59D7CA");
    readonly StackPanel _body=new(){Margin=new Thickness(26)};
    readonly TextBlock _status=new(){FontSize=12,Foreground=Muted,Margin=new Thickness(20,9,0,9),Text="Ready"};
    readonly CancellationTokenSource _lifetime=new();
    CancellationTokenSource? _job;
    string _source="",_destination="",_arguments="";
    AnalysisReport? _report;
    DataMode _mode=DataMode.PerClientWritable;
    bool _redirect=false;bool _isolate=true;
    public StudioWindow() {
        Title="Blaze Gen2 Portable Studio • 1.1.0 Experimental";Width=1150;Height=760;MinWidth=950;MinHeight=600;
        Background=Back;Foreground=Ink;WindowStartupLocation=WindowStartupLocation.CenterScreen;
        var root=new DockPanel();
        var status=new Border{Background=Panel,Child=_status};DockPanel.SetDock(status,Dock.Bottom);root.Children.Add(status);
        var sidebar=new StackPanel{Width=228,Background=Panel,Margin=new Thickness(0)};
        DockPanel.SetDock(sidebar,Dock.Left);root.Children.Add(sidebar);
        sidebar.Children.Add(T("BLAZE / GEN2",24,Accent,new Thickness(20,32,0,4)));
        sidebar.Children.Add(T("PORTABLE STUDIO",11,Muted,new Thickness(20,0,0,24)));
        foreach(var s in new[]{"DASHBOARD","APPLICATION DISCOVERY","APPLICATION ANALYZER","PORTABLE BUILDER","COMPATIBILITY PROFILES","PACKAGE MANAGER","SETTINGS","DIAGNOSTICS","DONATE","ABOUT"}) {
            var nav=B(s,()=>Navigate(s),false);nav.HorizontalContentAlignment=HorizontalAlignment.Left;
            nav.Margin=new Thickness(10,3,10,3);sidebar.Children.Add(nav);
        }
        var scroll=new ScrollViewer{VerticalScrollBarVisibility=ScrollBarVisibility.Auto,Content=_body};
        root.Children.Add(scroll);Content=root;Navigate("DASHBOARD");
    }
    static SolidColorBrush Brush(string hex)=>(SolidColorBrush)new BrushConverter().ConvertFromString(hex)!;
    static TextBlock T(string s,double size,Brush? color=null,Thickness? margin=null)=>new(){Text=s,FontSize=size,Foreground=color??Ink,Margin=margin??new Thickness(0,5,0,10),TextWrapping=TextWrapping.Wrap};
    static Button B(string s,Action action,bool primary=true) {
        var b=new Button{Content=s,Background=primary?Accent:Panel2,Foreground=primary?Back:Ink,FontSize=13,
            FontWeight=FontWeights.SemiBold,Padding=new Thickness(15,12,15,12),Margin=new Thickness(0,7,10,7),
            BorderThickness=new Thickness(0),Cursor=System.Windows.Input.Cursors.Hand};
        b.Click+=(_,_)=>action();return b;
    }
    static TextBox Input(string value) =>new(){Text=value,Background=Panel2,Foreground=Ink,CaretBrush=Accent,BorderThickness=new Thickness(0),Padding=new Thickness(13),Margin=new Thickness(0,5,0,10),FontSize=13,MinWidth=380};
    static Border Card(UIElement child)=>new(){Background=Panel,Padding=new Thickness(20),CornerRadius=new CornerRadius(12),Margin=new Thickness(0,8,0,12),Child=child};
    static StackPanel Box(params UIElement[] elements){var s=new StackPanel();foreach(var element in elements)s.Children.Add(element);return s;}
    void Buttons(params Button[] buttons){var r=new WrapPanel();foreach(var b in buttons)r.Children.Add(b);_body.Children.Add(r);}
    void Heading(string title,string description) {
        _body.Children.Clear();_body.Children.Add(T(title,29,Ink,new Thickness(0,0,0,7)));
        _body.Children.Add(T(description,14,Muted,new Thickness(0,0,0,17)));
    }
    void Status(string message)=>_status.Text=message;
    void Navigate(string page) {
        switch(page) {
            case "DASHBOARD":
                Heading("Make your applications mobile.","Build local, self-contained launchers for eligible Windows applications. Experimental assessments, never guarantees.");
                _body.Children.Add(Card(Box(T("01   DISCOVER",17,Accent),T("Select an installed application, extracted folder, or executable.",13,Muted),
                    B("Select application",()=>Navigate("APPLICATION DISCOVERY")))));
                _body.Children.Add(Card(Box(T("02   ANALYZE",17,Accent),T("Inventory files, review direct PE imports, and see limitations.",13,Muted),
                    B("Review compatibility",()=>Navigate("APPLICATION ANALYZER")))));
                _body.Children.Add(Card(Box(T("03   BUILD",17,Accent),T("Stage verified copies and a standalone Windows launcher.",13,Muted),
                    B("Open builder",()=>Navigate("PORTABLE BUILDER")))));
                _body.Children.Add(Card(Box(T("SUPPORT DEVELOPMENT",17,Accent),
                    T("Help keep Blaze projects freely accessible. Donate via PayPal QR if you wish.",13,Muted),
                    B("View PayPal donation QR",()=>Navigate("DONATE"),false))));
                break;
            case "DONATE":Donation();break;
            case "APPLICATION DISCOVERY":Discovery();break;
            case "APPLICATION ANALYZER":Analysis();break;
            case "PORTABLE BUILDER":Builder();break;
            case "COMPATIBILITY PROFILES":Profiles();break;
            case "PACKAGE MANAGER":Manager();break;
            case "SETTINGS":Settings();break;
            case "DIAGNOSTICS":Diagnostics();break;
            case "ABOUT":
                Heading("About Blaze Gen2","Blaze Gen2 Portable Studio / version 1.1.0 / experimental.");
                _body.Children.Add(Card(Box(T("Purpose",18,Accent),T("Convert applications you have permission to copy into best-effort portable packages. Created for legitimate diskless deployments.",14),
                    T("Static checks do not prove portability. Services, licensed products, drivers, anti-cheat, and machine-tied configuration may prevent relocation.",13,Muted))));break;
        }
    }
    void Source(string path) {
        if(!File.Exists(path)){MessageBox.Show("Selected executable does not exist.");return;}
        _source=path;_report=null;Status("Selected "+path);Navigate("APPLICATION ANALYZER");
    }
    void Discovery() {
        Heading("Application discovery","Choose your source. The selected application's entire containing directory is copied during build.");
        _body.Children.Add(Card(Box(T("Selected executable",15,Accent),T(string.IsNullOrWhiteSpace(_source)?"Not selected":_source,13,Muted))));
        Buttons(B("Choose executable",()=>{
            var d=new OpenFileDialog{Filter="Windows executable (*.exe)|*.exe",CheckFileExists=true};
            if(d.ShowDialog()==true)Source(d.FileName);
        }),B("Choose extracted folder",()=>{
            var d=new OpenFolderDialog{Title="Select application folder"};if(d.ShowDialog()!=true)return;
            try {
                var exes=Analyzer.DiscoverExecutables(d.FolderName);
                if(exes.Count==0){MessageBox.Show("No executable found in selected folder.");return;}
                var pick=new Window{Title="Choose entry point",Width=760,Height=460,WindowStartupLocation=WindowStartupLocation.CenterOwner,Owner=this,Background=Back};
                var box=new StackPanel{Margin=new Thickness(18)};var list=new ListBox{ItemsSource=exes,SelectedIndex=0,Background=Panel,Foreground=Ink,Height=320};
                box.Children.Add(list);box.Children.Add(B("Use selected executable",()=>{if(list.SelectedItem is string x){pick.DialogResult=true;Source(x);}}));pick.Content=box;pick.ShowDialog();
            }catch(Exception ex){MessageBox.Show(ex.Message,"Discovery error");}
        }),B("Find installed applications",async()=>await InstalledAsync(),false));
    }
    async Task InstalledAsync(){
        Heading("Installed applications","Registry uninstall entries in both 32-bit and 64-bit views are inspected. Coverage is incomplete.");
        Status("Scanning application registrations...");
        try {
            var found=await Task.Run(Analyzer.DiscoverInstalled,_lifetime.Token);
            var list=new ListBox{ItemsSource=found,Background=Panel,Foreground=Ink,MinHeight=350,MaxHeight=480,DisplayMemberPath="Name"};
            _body.Children.Add(Card(Box(T(found.Count+" application registrations with candidate EXEs",15,Accent),list,
                B("Select highlighted",()=>{if(list.SelectedItem is InstalledEntry selected)Source(selected.Executable);}))));
            Status("Installed application scan complete.");
        }catch(Exception e){Error(e);}
    }
    async void Analysis() {
        Heading("Compatibility analyzer","The assessment is static, read-only, and may overlook runtime behavior.");
        if(string.IsNullOrEmpty(_source)){Buttons(B("Select application",()=>Navigate("APPLICATION DISCOVERY")));return;}
        _body.Children.Add(T(_source,13,Muted));
        Buttons(B("Run analysis",async()=>await RunAnalysis()),B("Choose different source",()=>Navigate("APPLICATION DISCOVERY"),false));
        if(_report!=null)ShowReport();
    }
    async Task RunAnalysis() {
        _job?.Cancel();_job=new CancellationTokenSource();
        try {
            Status("Analyzing source (read-only)...");
            var r=await Analyzer.AnalyzeAsync(_source,_job.Token);_report=r;Status("Analysis completed: "+r.Classification);
            Navigate("APPLICATION ANALYZER");
        }catch(OperationCanceledException){Status("Analysis cancelled.");}catch(Exception e){Error(e);}
    }
    void ShowReport() {
        var r=_report!;var summary=Box(T("Assessment: "+r.Classification,19,Accent),
            T(r.Files.Count+" files • "+r.TotalBytes.ToString("N0")+" bytes • "+r.ImportedDlls.Count+" direct DLL imports",13),
            T("Evidence",15,Accent));
        foreach(var x in r.Evidence)summary.Children.Add(T("• "+x,12,Muted));
        summary.Children.Add(T("Warnings",15,Accent));
        foreach(var x in r.Warnings.Take(50))summary.Children.Add(T("⚠ "+x,12,Muted));
        if(r.Warnings.Count==0)summary.Children.Add(T("No specific warning found. Portability is still not guaranteed.",12,Muted));
        _body.Children.Add(Card(summary));Buttons(B("Continue to builder",()=>Navigate("PORTABLE BUILDER")));
    }
    void Builder() {
        Heading("Portable builder","Copy-first conversion. Source files are never moved, modified, or deleted.");
        if(string.IsNullOrEmpty(_source)){Buttons(B("Choose source",()=>Navigate("APPLICATION DISCOVERY")));return;}
        if(_report==null)_body.Children.Add(T("Analysis has not been run. Review compatibility before building.",13,Muted));
        else _body.Children.Add(Card(T("Compatibility: "+_report.Classification+". Check warnings before continuing.",15,Accent)));
        _body.Children.Add(T("Source: "+_source,13,Muted));
        _body.Children.Add(T("New destination folder (must not already exist)",14));
        var dest=Input(_destination);_body.Children.Add(dest);
        Buttons(B("Browse parent folder",()=>{
            var dlg=new OpenFolderDialog{Title="Choose parent folder for the new package"};
            if(dlg.ShowDialog()==true){var name=Path.GetFileNameWithoutExtension(_source)+"-Portable";dest.Text=Path.Combine(dlg.FolderName,name);}
        },false));
        _body.Children.Add(T("Arguments (optional)",14));var args=Input(_arguments);_body.Children.Add(args);
        _body.Children.Add(T("Writable data location",14));
        var mode=new ComboBox{Background=Panel2,Foreground=Ink,Padding=new Thickness(10),Margin=new Thickness(0,5,0,10),ItemsSource=Enum.GetValues<DataMode>(),SelectedItem=_mode};
        _body.Children.Add(mode);
        var redirect=new CheckBox{Foreground=Muted,Content="Opt-in APPDATA / LOCALAPPDATA environment overrides (not universal)",IsChecked=_redirect,Margin=new Thickness(0,8,0,12)};
        _body.Children.Add(redirect);
        var isolate=new CheckBox{Foreground=Muted,Content="Diskless safety: run copied application from this PC's local cache (recommended)",IsChecked=true,Margin=new Thickness(0,8,0,12)};
        _body.Children.Add(isolate);
        _body.Children.Add(T("Roblox is blocked in this experimental release. Official Roblox account sessions cannot be isolated by this generator.",12,Muted));
        Buttons(B("Generate portable package",async()=>{
            _destination=dest.Text.Trim();_arguments=args.Text;_mode=(DataMode)mode.SelectedItem;_redirect=redirect.IsChecked==true;_isolate=isolate.IsChecked==true;
            await BuildPackage();
        }),B("Cancel current job",()=>_job?.Cancel(),false));
    }
    async Task BuildPackage(){
        if(_report==null){MessageBox.Show("Run the application analyzer first.");return;}
        if(_report.Classification==CompatibilityLevel.HighRiskManualConfiguration||_report.Classification==CompatibilityLevel.Unsupported) {
            MessageBox.Show("This application has high-risk or unsupported dependencies. The automated builder is blocked.", "Compatibility warning");return;
        }
        if(MessageBox.Show("Copy the entire source application directory into a new package?\n\nCompatibility: "+_report.Classification+
            "\n\nThe source is never changed. Output is experimental.","Confirm conversion",MessageBoxButton.YesNo,MessageBoxImage.Warning)!=MessageBoxResult.Yes)return;
        _job?.Cancel();_job=new CancellationTokenSource();
        var bar=new ProgressBar{Minimum=0,Maximum=100,Height=22,Margin=new Thickness(0,8,0,12)};
        _body.Children.Add(bar);var progress=new Progress<int>(v=>{bar.Value=v;Status("Copying and verifying: "+v+"%");});
        try {
            var launcher=Path.Combine(AppContext.BaseDirectory,"BlazePortableLauncher.exe");
            var output=await Task.Run(()=>PackageBuilder.BuildAsync(
                new ConversionOptions{SourceExecutable=_source,Destination=_destination,Arguments=_arguments,DataMode=_mode,RedirectEnvironmentFolders=_redirect,IsolateExecutablePerClient=_isolate && _mode==DataMode.PerClientWritable},
                launcher,progress,_job.Token));
            Status("Complete: "+output);MessageBox.Show("Portable launcher created:\n"+output+"\n\nTest on a clean client before production use.","Build complete");
        }catch(OperationCanceledException){Status("Build cancelled; staging removed.");MessageBox.Show("Build cancelled safely.");}
        catch(Exception e){Error(e);}
    }
    void Profiles() {
        Heading("Compatibility profiles","JSON profiles define identification, required files, warnings, and optional launch metadata. Import/export only; automated profile application is future work.");
        var sample=new CompatibilityProfile();
        var json=System.Text.Json.JsonSerializer.Serialize(sample,PortableConfig.JsonOptions);
        var editor=new TextBox{Text=json,AcceptsReturn=true,TextWrapping=TextWrapping.NoWrap,VerticalScrollBarVisibility=ScrollBarVisibility.Auto,
            Height=300,FontFamily=new FontFamily("Consolas"),FontSize=12,Foreground=Ink,Background=Panel2,Padding=new Thickness(12)};
        _body.Children.Add(Card(editor));
        Buttons(B("Import profile",()=>{
            var d=new OpenFileDialog{Filter="JSON (*.json)|*.json"};if(d.ShowDialog()==true)editor.Text=File.ReadAllText(d.FileName);
        },false),B("Validate / export",()=>{
            try {
                if(System.Text.Json.JsonSerializer.Deserialize<CompatibilityProfile>(editor.Text,PortableConfig.JsonOptions)==null)throw new InvalidDataException("Profile must be an object.");
                var d=new SaveFileDialog{Filter="JSON (*.json)|*.json",FileName="profile.json"};if(d.ShowDialog()==true)File.WriteAllText(d.FileName,editor.Text);
            }catch(Exception e){Error(e);}
        }));
    }
    void Manager() {
        Heading("Package manager","Open a generated package folder to inspect its configuration. No automatic destructive operations.");
        Buttons(B("Open existing package",()=>{
            var d=new OpenFolderDialog{Title="Select generated package"};
            if(d.ShowDialog()==true){
                var cfg=Path.Combine(d.FolderName,"PortableConfig.json");
                try {var c=PortableConfig.Load(cfg);_body.Children.Add(Card(Box(T(c.DisplayName,18,Accent),T("Launch: "+c.Executable,13),T("Data mode: "+c.DataMode,13))));}
                catch(Exception e){Error(e);}
            }
        }));
    }
    void Donation(){
        Heading("Support Blaze development","Optional PayPal donation — no purchase or donation is required to use this software.");
        var qr=DonationQr.CreateImage();
        _body.Children.Add(Card(Box(T("Scan to support development",20,Accent),
            T("PayPal • Loumer Manreal",15,Muted),qr,
            T("For your security, review the PayPal recipient and amount before completing payment.",13,Muted),
            B("Open PayPal donation page",()=>{
                try {System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(DonationQr.PayPalUrl){UseShellExecute=true});}
                catch(Exception e){Error(e);}
            }))));
    }
    void Settings(){
        Heading("Settings","Conversion preferences are selected per package. Generated launchers contain independent config.");
        _body.Children.Add(Card(Box(T("Default safety posture",17,Accent),
            T("Read-only static analysis, copy-first staging, no implicit registry edits, no junction modifications, no licensing bypass.",13,Muted),
            T("Data mode: per-client writable on local disk by default; supports portable-local or temporary-session modes.",13,Muted))));
    }
    void Diagnostics(){
        Heading("Diagnostics","Application analysis and build errors appear in the status bar or message dialogs.");
        _body.Children.Add(Card(Box(T("Launcher diagnostics",16,Accent),
            T("Client logs: %LOCALAPPDATA%\\BlazeGen2\\Packages\\<PackageId>\\Logs\\launcher.log",13,Muted),
            T("Launcher failure log: %LOCALAPPDATA%\\BlazeGen2\\Errors\\launcher-errors.log",13,Muted))));
    }
    void Error(Exception e){Status("Error: "+e.Message);MessageBox.Show(e.ToString(),"Blaze Gen2 error",MessageBoxButton.OK,MessageBoxImage.Error);}
    protected override void OnClosed(EventArgs e){_job?.Cancel();_lifetime.Cancel();base.OnClosed(e);}
}

