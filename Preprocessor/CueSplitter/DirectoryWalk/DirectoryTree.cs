using CueSplitter.DirectoryWalk;

public interface IDirectoryTree
{
    IEnumerable<IDirectoryTreeNode> Walk(string path, Action<Exception> onException);
}

public class DirectoryTree : IDirectoryTree
{
    public IEnumerable<IDirectoryTreeNode> Walk(string path, Action<Exception> onException)
    {
        if (path == null) throw new ArgumentNullException(nameof(path));
        if (onException == null) throw new ArgumentNullException(nameof(onException));

        var nodes = new Queue<DirectoryTreeNode>()
        {
            new DirectoryTreeNode(path)
        };

        while (nodes.Any())
        {
            var current = nodes.Dequeue();
            yield return current;

            try
            {
                foreach (var directory in current.DirectoryNames)
                {
                    nodes.Enqueue(new DirectoryTreeNode(Path.Combine(current.DirectoryName, directory)));
                }
            }
            catch (Exception inner)
            {
                onException(inner);
            }
        }
    }
}

public interface IDirectoryTreeNode
{
    string DirectoryName { get; }

    IEnumerable<string> DirectoryNames { get; }

    IEnumerable<string> FileNames { get; }
}

internal class DirectoryTreeNode : IDirectoryTreeNode
{
    internal DirectoryTreeNode(string path)
    {
        DirectoryName = path;
    }

    public string DirectoryName { get; }

    public IEnumerable<string> DirectoryNames => Directory.EnumerateDirectories(DirectoryName).Select(Path.GetFileName);

    public IEnumerable<string> FileNames => Directory.EnumerateFiles(DirectoryName).Select(Path.GetFileName);
}