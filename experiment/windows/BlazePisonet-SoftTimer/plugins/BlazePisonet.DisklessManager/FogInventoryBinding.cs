namespace BlazePisonet.SoftTimer;

// A displayed inventory is valid only for the connection that fetched it.
// Refreshes can overlap, and a connection edit can happen while one awaits I/O.
public sealed class FogInventoryBinding
{
    private long _generation;
    private long _readyGeneration = -1;

    public long Generation => _generation;

    public void ConnectionEdited()
    {
        _generation++;
        _readyGeneration = -1;
    }

    public long BeginRefresh()
    {
        _generation++;
        _readyGeneration = -1;
        return _generation;
    }

    public bool CompleteRefresh(long generation)
    {
        if (generation != _generation) return false;
        _readyGeneration = generation;
        return true;
    }

    public bool ReadyFor(long generation) =>
        generation == _generation && _readyGeneration == generation;
}
