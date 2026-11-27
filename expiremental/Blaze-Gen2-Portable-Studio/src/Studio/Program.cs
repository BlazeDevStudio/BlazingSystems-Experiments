using System.Windows;
namespace BlazeGen2Studio;
internal static class Program {
    [STAThread] public static void Main() {
        var app=new Application{ShutdownMode=ShutdownMode.OnMainWindowClose};
        app.Run(new StudioWindow());
    }
}

