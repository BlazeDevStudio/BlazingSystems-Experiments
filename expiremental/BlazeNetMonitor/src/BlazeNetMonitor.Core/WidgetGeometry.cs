using System.Drawing;

namespace BlazeNetMonitor.Core;

/// <summary>
/// Pure placement logic: the user must always be able to reach the resize handles.
/// Work area comes from the monitor containing the drag pointer, not the taskbar overlay.
/// </summary>
public static class WidgetGeometry
{
    public const int CompactMinimumWidth = 124;
    public const int CompactMinimumHeight = 24;
    // A micrograph remains visible in 24px taskbar-height layouts.
    public static int GraphHeight(int widgetHeight, bool enabled)
    {
        if (!enabled || widgetHeight < CompactMinimumHeight) return 0;
        return Math.Clamp(widgetHeight / 5, 4, 18);
    }
    public const string Floating = "Floating";
    public const string AboveTaskbar = "AboveTaskbar";
    public const string InsideTaskbar = "InsideTaskbar";

    public static string ResolvePlacement(AppSettings settings)
    {
        if (settings.PlacementMode is Floating or AboveTaskbar or InsideTaskbar)
            return settings.PlacementMode;
        return settings.FreeformPositioned ? Floating :
            settings.DockInsideTaskbar ? InsideTaskbar : AboveTaskbar;
    }

    /// <summary>Preserve exact monitor coordinates in overlay mode, and a safe
    /// inset in desktop mode. This is a topmost window, not an Explorer DeskBand.</summary>
    public static Rectangle ConstrainToMode(Rectangle rectangle,
        Rectangle screenBounds, Rectangle workArea, string mode)
    {
        var allowed = mode == AboveTaskbar ? workArea : screenBounds;
        return Constrain(rectangle, allowed,
            CompactMinimumWidth, CompactMinimumHeight,
            margin: mode == AboveTaskbar ? 6 : 0);
    }

    public static Rectangle DockPosition(Rectangle requested, Rectangle workArea,
        Rectangle taskbar, string mode, int rightOffset)
    {
        var anchor = mode == InsideTaskbar && taskbar.Width > 0 && taskbar.Height > 0
            ? taskbar : workArea;
        int x = anchor.Right - Math.Max(0, rightOffset) - requested.Width;
        int y;
        if (mode == InsideTaskbar && taskbar.Width > 0 && taskbar.Height > 0)
        {
            // Horizontal taskbar: vertical center in the actual bar.
            // Vertical taskbar: keep position inside its visible area.
            y = taskbar.Width >= taskbar.Height
                ? taskbar.Top + (taskbar.Height - requested.Height) / 2
                : taskbar.Bottom - requested.Height;
        }
        else y = workArea.Bottom - requested.Height - 6;
        return new Rectangle(x, y, requested.Width, requested.Height);
    }

    public static bool CoversScreen(Rectangle window, Rectangle screen, int tolerance = 3)
    {
        if (window.Width <= 0 || window.Height <= 0 ||
            screen.Width <= 0 || screen.Height <= 0) return false;
        return window.Left <= screen.Left + tolerance &&
               window.Top <= screen.Top + tolerance &&
               window.Right >= screen.Right - tolerance &&
               window.Bottom >= screen.Bottom - tolerance;
    }

    public static Rectangle Constrain(Rectangle proposed, Rectangle workingArea, int minWidth = CompactMinimumWidth, int minHeight = CompactMinimumHeight, int margin = 6)
    {
        if (workingArea.Width <= 0 || workingArea.Height <= 0)
            return proposed;

        // Leave a small reveal strip on auto-hidden taskbars and room for touch targets.
        int inset = Math.Max(0, Math.Min(margin, Math.Min(workingArea.Width, workingArea.Height) / 8));
        var safe = Rectangle.Inflate(workingArea, -inset, -inset);
        if (safe.Width <= 0 || safe.Height <= 0) safe = workingArea;
        int width = Math.Clamp(proposed.Width, Math.Min(minWidth, safe.Width), safe.Width);
        int height = Math.Clamp(proposed.Height, Math.Min(minHeight, safe.Height), safe.Height);
        int x = Math.Clamp(proposed.Left, safe.Left, safe.Right - width);
        int y = Math.Clamp(proposed.Top, safe.Top, safe.Bottom - height);
        return new Rectangle(x, y, width, height);
    }
}
