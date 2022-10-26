using System.Diagnostics.CodeAnalysis;

namespace CueSplitter.DirectoryWalk;

public static class DirectoryTreeNodeExtensions
{
    public static void Deconstruct(
        this IDirectoryTreeNode directoryTreeNode,
        out string directoryName,
        out IEnumerable<string> directoryNames,
        out IEnumerable<string> fileNames)
    {
        directoryName = directoryTreeNode?.DirectoryName;
        directoryNames = directoryTreeNode?.DirectoryNames;
        fileNames = directoryTreeNode?.FileNames;
    }
    public static bool Exists(
        this IDirectoryTreeNode directoryTreeNode)
    {
        // Empty string does not exist and it'll return false.
        return Directory.Exists(directoryTreeNode?.DirectoryName ?? string.Empty);
    }
}