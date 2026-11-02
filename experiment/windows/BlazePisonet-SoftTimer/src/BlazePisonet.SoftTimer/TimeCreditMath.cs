namespace BlazePisonet.SoftTimer;

// Single checked arithmetic rule for local prepaid time and member balances.
// This is a math-only helper: it does not authorize a coin, receipt, member
// credential, payment, or hardware state transition.
internal static class TimeCreditMath
{
    internal static bool TryAdd(long currentSeconds, long incomingSeconds, out long result)
    {
        result = 0;
        if (currentSeconds < 0 || incomingSeconds < 0 ||
            currentSeconds > long.MaxValue - incomingSeconds)
            return false;

        result = currentSeconds + incomingSeconds;
        return true;
    }
}
