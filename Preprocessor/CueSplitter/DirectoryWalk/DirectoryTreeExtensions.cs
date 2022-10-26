using System.Diagnostics.CodeAnalysis;
using System.Text.RegularExpressions;

namespace CueSplitter.DirectoryWalk;

internal class DirectoryTreeNodeFilter : IDirectoryTreeNode
{
    internal DirectoryTreeNodeFilter(string path, IEnumerable<string> directoryNames, IEnumerable<string> fileNames)
    {
        DirectoryName = path;
        DirectoryNames = directoryNames;
        FileNames = fileNames;
    }

    public string DirectoryName { get; }

    public IEnumerable<string> DirectoryNames { get; }

    public IEnumerable<string> FileNames { get; }
}

public static class DirectoryTreeExtensions
{
    public static IEnumerable<IDirectoryTreeNode> WalkSilently(this IDirectoryTree directoryTree, string path)
    {
        if (directoryTree == null) throw new ArgumentNullException(nameof(directoryTree));
        if (path == null) throw new ArgumentNullException(nameof(path));

        return directoryTree.Walk(path, _ => { });
    }

    public static IEnumerable<IDirectoryTreeNode> SkipDirectories(this IEnumerable<IDirectoryTreeNode> nodes, string directoryNamePattern)
    {
        if (nodes == null) throw new ArgumentNullException(nameof(nodes));
        if (directoryNamePattern == null) throw new ArgumentNullException(nameof(directoryNamePattern));

        return
            from node in nodes
            where !node.DirectoryName.Matches(directoryNamePattern)
            select new DirectoryTreeNodeFilter
            (
                node.DirectoryName,
                from dirname in node.DirectoryNames where !dirname.Matches(directoryNamePattern) select dirname,
                node.FileNames
            );
    }

    public static IEnumerable<IDirectoryTreeNode> SkipFiles(this IEnumerable<IDirectoryTreeNode> nodes, string fileNamePattern)
    {
        if (nodes == null) throw new ArgumentNullException(nameof(nodes));
        if (fileNamePattern == null) throw new ArgumentNullException(nameof(fileNamePattern));

        return
            from node in nodes
            select new DirectoryTreeNodeFilter
            (
                node.DirectoryName,
                node.DirectoryNames,
                from fileName in node.FileNames where !fileName.Matches(fileNamePattern) select fileName
            );
    }

    public static IEnumerable<IDirectoryTreeNode> WhereDirectories(this IEnumerable<IDirectoryTreeNode> nodes, string directoryNamePattern)
    {
        if (nodes == null) throw new ArgumentNullException(nameof(nodes));
        if (directoryNamePattern == null) throw new ArgumentNullException(nameof(directoryNamePattern));

        return
            from node in nodes
            where node.DirectoryName.Matches(directoryNamePattern)
            select new DirectoryTreeNodeFilter
            (
                node.DirectoryName,
                from dirname in node.DirectoryNames where dirname.Matches(directoryNamePattern) select dirname,
                node.FileNames
            );
    }

    public static IEnumerable<IDirectoryTreeNode> WhereFiles(this IEnumerable<IDirectoryTreeNode> nodes, string fileNamePattern)
    {
        if (nodes == null) throw new ArgumentNullException(nameof(nodes));
        if (fileNamePattern == null) throw new ArgumentNullException(nameof(fileNamePattern));

        return
            from node in nodes
            select new DirectoryTreeNodeFilter
            (
                node.DirectoryName,
                node.DirectoryNames,
                from fileName in node.FileNames
                where fileName.Matches(fileNamePattern)
                select fileName
            );
    }

    private static bool Matches(this string name, string pattern)
    {
        return Regex.IsMatch(name, pattern, RegexOptions.IgnoreCase);
    }
}