using System.Text.Json.Serialization;

namespace BlazePisonet.SoftTimer;

public enum TimerSourceMode
{
    InternalPcTimer,
    ExternalTimerBoard,
    BlazePisonetTimer
}

public enum CoinTopologyMode
{
    StandardOneToOne,
    CentralizedCoordinator,
    CentralizedStation
}

public enum SerialSelectionMode
{
    ExactDevice,
    DeviceFamily,
    ManualPort,
    AutoCompatible,
    AnyAvailable,
    LegacyCom1
}

public enum ModemSignal
{
    Dsr,
    Cts,
    CarrierDetect,
    RingIndicator
}

public sealed class AppConfig
{
    public string Version { get; set; } = "0.4.0";
    public bool Enabled { get; set; }
    public string ShopName { get; set; } = "BlazePisonet";
    public string PcName { get; set; } = Environment.MachineName;
    public string Banner1 { get; set; } = "INSERT COIN TO CONTINUE";
    public string Banner2 { get; set; } = "Powered by BlazePisonet SoftTimer";
    public string AccentHex { get; set; } = "#7C5CFF";
    public string Accent2Hex { get; set; } = "#22D3EE";
    public string BackgroundHex { get; set; } = "#07111F";
    public string? WallpaperPath { get; set; }

    public TimerSourceMode TimerSource { get; set; } = TimerSourceMode.InternalPcTimer;
    public CoinTopologyMode CoinTopology { get; set; } = CoinTopologyMode.StandardOneToOne;
    public int SecondsPerCoin { get; set; } = 300;
    public int WarningSeconds { get; set; } = 60;
    public bool WarningSoundEnabled { get; set; } = true;
    public string WarningSoundPath { get; set; } = string.Empty;
    public int ShutdownGraceSeconds { get; set; } = 30;
    public bool AutoShutdownAtZero { get; set; }
    public bool AutoMuteWhenLocked { get; set; }
    public bool ShowActiveTimerOverlay { get; set; } = true;
    public bool AllowMemberBankFromOverlay { get; set; } = true;

    public SerialSelectionMode SerialSelection { get; set; } = SerialSelectionMode.AutoCompatible;
    public string ManualComPort { get; set; } = "COM1";
    public string PreferredPnpDeviceId { get; set; } = string.Empty;
    public string PreferredVid { get; set; } = string.Empty;
    public string PreferredPid { get; set; } = string.Empty;
    public string PreferredUsbSerial { get; set; } = string.Empty;
    public string PreferredFriendlyName { get; set; } = string.Empty;
    public string LastKnownComPort { get; set; } = string.Empty;
    public ModemSignal CoinInputSignal { get; set; } = ModemSignal.Dsr;
    public bool CoinInputActiveHigh { get; set; } = true;
    public ModemSignal TimerActiveSignal { get; set; } = ModemSignal.Dsr;
    public bool TimerActiveHigh { get; set; } = true;
    public bool DtrEnabled { get; set; } = true;
    public bool RtsEnabled { get; set; } = true;
    public int DebounceMs { get; set; } = 80;
    public int MinimumPulseMs { get; set; } = 20;
    public int MaximumPulseMs { get; set; } = 1000;
    public int SerialBaudRate { get; set; } = 9600;

    public string BlazeTimerAddress { get; set; } = "http://192.168.4.1/";
    public string BlazeTimerMac { get; set; } = string.Empty;
    public string BlazeTimerName { get; set; } = string.Empty;
    public int BlazeTimerPollMs { get; set; } = 1000;

    public string CentralStationId { get; set; } = Environment.MachineName;
    public string CentralCoordinatorUrl { get; set; } = "http://192.168.1.2:8765/";
    public int CentralListenPort { get; set; } = 8765;
    public int CentralCoinWindowSeconds { get; set; } = 90;
    public string CentralSharedKey { get; set; } = string.Empty;

    public bool BlazePwifiEnabled { get; set; }
    public string BlazePwifiVendoUrl { get; set; } = "http://192.168.1.1:4455/cgi-bin/vendo";
    public string BlazePwifiControllerId { get; set; } = string.Empty;
    public string BlazePwifiVendoKey { get; set; } = string.Empty;
    public bool MirrorLocalCoinsToBlazePwifi { get; set; }
    public bool BlazePwifiMemberAuthorityEnabled { get; set; }
    public bool BlazePwifiAllowCachedMemberLogin { get; set; } = false;
    public int BlazePwifiMemberSyncSeconds { get; set; } = 15;

    public bool BlockTaskManager { get; set; } = true;
    public bool BlockRegistryTools { get; set; } = true;
    public bool DisableLogoff { get; set; } = true;
    public bool DisablePowerOptions { get; set; } = true;
    public bool BlockWindowsKeys { get; set; } = true;
    public bool LockMouseToScreen { get; set; } = true;
    public bool RunWatchdog { get; set; } = true;
    public bool RunAtStartup { get; set; } = true;
    public int AdminSecretWindowSeconds { get; set; } = 12;
    public int AdminLoginTimeoutSeconds { get; set; } = 30;
    public string AdminPasswordSalt { get; set; } = string.Empty;
    public string AdminPasswordHash { get; set; } = string.Empty;
    public int AdminPasswordIterations { get; set; } = 150000;

    public bool IdleShutdownEnabled { get; set; }
    public int IdleShutdownMinutes { get; set; } = 30;
    public bool UnusualInputShutdownEnabled { get; set; }
    public int UnusualInputWindowSeconds { get; set; } = 300;
    public int UnusualInputThreshold { get; set; } = 1500;

    public List<string> BlockedProcesses { get; set; } = new()
    {
        "taskmgr", "regedit", "procexp", "processhacker"
    };

    public List<string> BlockedWebsites { get; set; } = new();
    public List<NotificationSchedule> NotificationSchedules { get; set; } = new()
    {
        new() { Name = "Schedule 1" },
        new() { Name = "Schedule 2" },
        new() { Name = "Schedule 3" }
    };

    [JsonIgnore]
    public bool HasAdminPassword => !string.IsNullOrWhiteSpace(AdminPasswordHash) && !string.IsNullOrWhiteSpace(AdminPasswordSalt);
}

public sealed class NotificationSchedule
{
    public bool Enabled { get; set; }
    public string Name { get; set; } = "Schedule";
    public TimeSpan Start { get; set; } = new(22, 0, 0);
    public TimeSpan End { get; set; } = new(7, 0, 0);
    public bool LockDuringWindow { get; set; }
    public bool ShutdownDuringWindow { get; set; }
    public string Message { get; set; } = "Shop is currently closed.";
    public HashSet<DayOfWeek> Days { get; set; } = Enum.GetValues<DayOfWeek>().ToHashSet();
}
