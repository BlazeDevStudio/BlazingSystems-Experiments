// TEST ONLY: referenced exclusively by disposable generated C# source.
namespace BlazePisonet.SoftTimer;
public static class TestOnlyHooks
{
    public static Action<bool, bool>? AfterRead;
    public static void ObserveSample(bool ok, bool active)
    {
        System.Threading.Volatile.Read(ref AfterRead)?.Invoke(ok, active);
    }
}
