using System.Security.Principal;

namespace BlazePisonet.SoftTimer;

internal static class SystemIntegration
{
    private const int TaskCreateOrUpdate = 6;
    private const int TaskLogonInteractiveToken = 3;
    private const int TaskRunLevelHighest = 1;
    private const int TaskTriggerLogon = 9;
    private const int TaskActionExec = 0;
    private const int TaskInstancesIgnoreNew = 2;

    public const string AppTaskName = "BlazePisonet SoftTimer";
    public const string WatchdogTaskName = "BlazePisonet SoftTimer Watchdog";

    public static int Install()
    {
        try
        {
            if (!OperatingSystem.IsWindows())
                throw new PlatformNotSupportedException("Windows Task Scheduler is required.");

            var account = WindowsIdentity.GetCurrent().Name;
            if (string.IsNullOrWhiteSpace(account))
                throw new InvalidOperationException("Could not resolve the current Windows account.");

            var appPath = Environment.ProcessPath
                ?? Path.Combine(AppContext.BaseDirectory, "BlazePisonet.SoftTimer.exe");
            var watchdogPath = Path.Combine(AppContext.BaseDirectory, "BlazePisonet.SoftTimer.Watchdog.exe");

            if (!File.Exists(appPath))
                throw new FileNotFoundException("SoftTimer executable was not found.", appPath);
            if (!File.Exists(watchdogPath))
                throw new FileNotFoundException("SoftTimer watchdog executable was not found.", watchdogPath);

            dynamic service = CreateSchedulerService();
            service.Connect();
            dynamic root = service.GetFolder("\\");

            RegisterLogonTask(
                service,
                root,
                account,
                AppTaskName,
                "Starts BlazePisonet SoftTimer in the interactive Pisonet Windows session.",
                appPath);

            RegisterLogonTask(
                service,
                root,
                account,
                WatchdogTaskName,
                "Keeps BlazePisonet SoftTimer available after an unexpected process exit.",
                watchdogPath);

            _ = root.GetTask(AppTaskName);
            _ = root.GetTask(WatchdogTaskName);

            Storage.Log($"System integration installed for {account}. Tasks: {AppTaskName}; {WatchdogTaskName}");
            return 0;
        }
        catch (Exception ex)
        {
            Storage.Log("System integration install failed: " + ex);
            TryDeleteTasks();
            return 31;
        }
    }

    public static int Uninstall()
    {
        try
        {
            Directory.CreateDirectory(Storage.RootDirectory);
            File.WriteAllText(Storage.MaintenancePath, "4102444800");
            TryDeleteTasks();
            Storage.Log("System integration removed.");
            return 0;
        }
        catch (Exception ex)
        {
            Storage.Log("System integration removal failed: " + ex);
            return 32;
        }
    }

    public static int Verify()
    {
        try
        {
            dynamic service = CreateSchedulerService();
            service.Connect();
            dynamic root = service.GetFolder("\\");
            _ = root.GetTask(AppTaskName);
            _ = root.GetTask(WatchdogTaskName);
            return 0;
        }
        catch
        {
            return 33;
        }
    }

    private static dynamic CreateSchedulerService()
    {
        var type = Type.GetTypeFromProgID("Schedule.Service", throwOnError: true)
            ?? throw new InvalidOperationException("Windows Task Scheduler COM service is unavailable.");
        return Activator.CreateInstance(type)
            ?? throw new InvalidOperationException("Could not create the Windows Task Scheduler service.");
    }

    private static void RegisterLogonTask(
        dynamic service,
        dynamic root,
        string account,
        string taskName,
        string description,
        string executablePath)
    {
        TryDeleteTask(root, taskName);

        dynamic definition = service.NewTask(0);
        definition.RegistrationInfo.Description = description;

        definition.Settings.Enabled = true;
        definition.Settings.StartWhenAvailable = true;
        definition.Settings.DisallowStartIfOnBatteries = false;
        definition.Settings.StopIfGoingOnBatteries = false;
        definition.Settings.ExecutionTimeLimit = "PT0S";
        definition.Settings.MultipleInstances = TaskInstancesIgnoreNew;

        dynamic principal = definition.Principal;
        principal.UserId = account;
        principal.LogonType = TaskLogonInteractiveToken;
        principal.RunLevel = TaskRunLevelHighest;

        dynamic trigger = definition.Triggers.Create(TaskTriggerLogon);
        trigger.Enabled = true;
        trigger.UserId = account;

        dynamic action = definition.Actions.Create(TaskActionExec);
        action.Path = executablePath;
        action.WorkingDirectory = Path.GetDirectoryName(executablePath) ?? AppContext.BaseDirectory;

        root.RegisterTaskDefinition(
            taskName,
            definition,
            TaskCreateOrUpdate,
            account,
            null,
            TaskLogonInteractiveToken,
            null);
    }

    private static void TryDeleteTasks()
    {
        if (!OperatingSystem.IsWindows()) return;
        try
        {
            dynamic service = CreateSchedulerService();
            service.Connect();
            dynamic root = service.GetFolder("\\");
            TryDeleteTask(root, AppTaskName);
            TryDeleteTask(root, WatchdogTaskName);
        }
        catch (Exception ex)
        {
            Storage.Log("Task cleanup warning: " + ex.Message);
        }
    }

    private static void TryDeleteTask(dynamic root, string taskName)
    {
        try { root.DeleteTask(taskName, 0); }
        catch { }
    }
}
