namespace BlazeGen2;
public static class Paths {
    public static bool IsWithin(string child, string parent) {
        var c=Path.GetFullPath(child).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
        var p=Path.GetFullPath(parent).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
        return c.StartsWith(p,StringComparison.OrdinalIgnoreCase);
    }
    public static string Inside(string baseDir,string relative) {
        if(string.IsNullOrWhiteSpace(relative)||Path.IsPathRooted(relative)||relative.Contains(':')||relative.Contains('\0'))
            throw new InvalidDataException("Expected a safe relative path.");
        var result=Path.GetFullPath(Path.Combine(baseDir,relative.Replace('/',Path.DirectorySeparatorChar)));
        if(!IsWithin(result,baseDir))throw new InvalidDataException("Path escapes package directory: "+relative);
        return result;
    }
    public static bool IsLink(string path) {
        var attr=File.GetAttributes(path);
        return (attr & FileAttributes.ReparsePoint)!=0;
    }
}

