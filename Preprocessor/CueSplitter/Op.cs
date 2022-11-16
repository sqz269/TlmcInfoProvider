using CueSplitter.DirectoryWalk;
using System.Diagnostics;

namespace CueSplitter;


public static class Op
{
    public static void WriteLog(string filename, string message, ReaderWriterLock rwLock)
    {
        try
        {
            rwLock.AcquireWriterLock(100);
            File.AppendAllText(filename, message);
        }
        finally
        {
            rwLock.ReleaseWriterLock();
        }
    }

    public static void NormalizeOp(string root)
    {
        var log = Path.Combine(root, "normalize-log.log");

        var argumentProcessors = AudioNormalize.Normalize(root);
        Console.WriteLine($"Queued {argumentProcessors.Count}");

        ThreadPool.SetMaxThreads(Environment.ProcessorCount, Environment.ProcessorCount);

        using var countdownEvent = new CountdownEvent(argumentProcessors.Count);

        var rwLock = new ReaderWriterLock();

        foreach (var normalInfo in argumentProcessors)
        {
            ThreadPool.QueueUserWorkItem((o) =>
            {
                Console.WriteLine($"[{normalInfo.OutFile.GetSha1Sig()}] Processing: {normalInfo.OutFile}");

                try
                {
                    rwLock.AcquireWriterLock(100);
                    File.AppendAllText(log, $"[{DateTimeOffset.Now.ToUnixTimeSeconds()}] [{normalInfo.OriginalFile.GetSha1Sig()}] Processing: {normalInfo.OriginalFile}\n");
                }
                finally
                {
                    rwLock.ReleaseWriterLock();
                }

                Stopwatch sw = Stopwatch.StartNew();
                normalInfo.Processor.ProcessSynchronously();

                Console.WriteLine($"[{normalInfo.OriginalFile.GetSha1Sig()}] Overwriting: {normalInfo.OriginalFile}");
                try
                {
                    rwLock.AcquireWriterLock(100);
                    File.AppendAllText(log, $"[{DateTimeOffset.Now.ToUnixTimeSeconds()}] [{normalInfo.OriginalFile.GetSha1Sig()}] Overwriting: {normalInfo.OriginalFile}\n");
                }
                finally
                {
                    rwLock.ReleaseWriterLock();
                }
                File.Copy(normalInfo.OutFile, normalInfo.OriginalFile, true);
                File.Delete(normalInfo.OutFile);

                sw.Stop();
                Console.WriteLine($"[{normalInfo.OutFile.GetSha1Sig()}] Process completed (in {sw.Elapsed})");

                try
                {
                    rwLock.AcquireWriterLock(100);
                    File.AppendAllText(log, $"[{DateTimeOffset.Now.ToUnixTimeSeconds()}] [{normalInfo.OriginalFile.GetSha1Sig()}] Process completed {normalInfo.OriginalFile}\n");
                }
                finally
                {
                    rwLock.ReleaseWriterLock();
                }
                
                countdownEvent.Signal();
            });
        }

        countdownEvent.Wait();
    }

    public static void SplitOp(string root)
    {
        var log = Path.Combine(root, "split-log.log");

        var argumentProcessors = new Queue<CueProcessInfo>();

        var directoryTree = new DirectoryTree();
        foreach (var (path, dirs, files) in directoryTree.WalkSilently(root).WhereFiles("\\.cue"))
        {
            foreach (var file in files)
            {
                var fullPath = Path.Combine(path, file);
                CueSplit.SplitCue(path, fullPath).ForEach(i => argumentProcessors.Enqueue(i));
            }
        }

        Console.WriteLine($"Queued {argumentProcessors.Count} Operations");

        ThreadPool.SetMaxThreads(Environment.ProcessorCount, Environment.ProcessorCount);

        using var countdownEvent = new CountdownEvent(argumentProcessors.Count);

        var rwLock = new ReaderWriterLock();

        foreach (var processInfo in argumentProcessors)
        {
            ThreadPool.QueueUserWorkItem((o) =>
            {

                Console.WriteLine($"[{processInfo.OutFilePath.GetSha1Sig()}] Processing: {processInfo.FileName}");

                try
                {
                    rwLock.AcquireWriterLock(100);
                    File.AppendAllText(log, $"[{DateTimeOffset.Now.ToUnixTimeSeconds()}] [{processInfo.OutFilePath.GetSha1Sig()}] Processing: {processInfo.OutFilePath}\n");
                }
                finally
                {
                    rwLock.ReleaseWriterLock();
                }

                Stopwatch sw = Stopwatch.StartNew();
                processInfo.Processor.ProcessSynchronously();
                sw.Stop();
                Console.WriteLine($"[{processInfo.OutFilePath.GetSha1Sig()}] Process completed (in {sw.Elapsed})");

                try
                {
                    rwLock.AcquireWriterLock(100);
                    File.AppendAllText(log, $"[{DateTimeOffset.Now.ToUnixTimeSeconds()}] [{processInfo.OutFilePath.GetSha1Sig()}] Process completed {processInfo.OutFilePath}\n");
                }
                finally
                {
                    rwLock.ReleaseWriterLock();
                }

                countdownEvent.Signal();
            });
        }

        countdownEvent.Wait();
    }
    

}