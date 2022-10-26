using System.Runtime.CompilerServices;

namespace CueSplitter;

public static class IndexExtensions
{
    public static TimeSpan ToTimeSpan(this Index index)
    {
        return new TimeSpan(0, index.Minutes, index.Seconds);
    }

    public static TimeSpan Duration(this Index index, Index comp)
    {
        return (index.ToTimeSpan() - comp.ToTimeSpan()).Duration();
    }
}