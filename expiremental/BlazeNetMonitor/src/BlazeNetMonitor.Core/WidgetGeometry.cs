using System.Drawing;

namespace BlazeNetMonitor.Core;

/// <summary>
/// Pure placement logic: the user must always be able to reach the resize handles.
/// Work area comes from the monitor containing the drag pointer, not the taskbar overlay.
/// </summary>
public static class WidgetGeometry
{
    public static Rectangle Constrain(Rectangle proposed, Rectangle workingArea, int minWidth = 210, int minHeight = 52)
    {
        if (workingArea.Width <= 0 || workingArea.Height <= 0)
            return proposed;

        // Leave a small reveal strip on auto-hidden taskbars and room for touch targets.
        var safe = Rectangle.Inflate(workingArea, -Math.Min(6, Math.Max(0, workingArea.Width / 20)),
            -Math.Min(6, Math.Max(0, workingArea.Height / 20)));
        if (safe.Width <= 0 || safe.Height <= 0) safe = workingArea;
        int width = Math.Clamp(proposed.Width, Math.Min(minWidth, safe.Width), safe.Width);
        int height = Math.Clamp(proposed.Height, Math.Min(minHeight, safe.Height), safe.Height);
        int x = Math.Clamp(proposed.Left, safe.Left, safe.Right - width);
        int y = Math.Clamp(proposed.Top, safe.Top, safe.Bottom - height);
        return new Rectangle(x, y, width, height);
    }
}
