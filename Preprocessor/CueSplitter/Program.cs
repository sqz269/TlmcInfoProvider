
using System.Diagnostics;
using System.Text;
using CueSplitter.DirectoryWalk;
using FFMpegCore;
using CueSplitter;

Console.OutputEncoding = System.Text.Encoding.UTF8;

var log = @"E:\sg\log.log";
var root = @"E:\solar";

var ffmpegDir = "";
if (string.IsNullOrWhiteSpace(ffmpegDir))
{
    ffmpegDir = "D:\\Tools\\ffmpeg-master-latest-win64-gpl\\bin";
}

GlobalFFOptions.Configure(opt => opt.BinaryFolder = ffmpegDir);

var argumentProcessors = new Queue<CueProcessInfo>();

var directoryTree = new DirectoryTree();
foreach (var (path, dirs, files) in directoryTree.WalkSilently(root).WhereFiles("\\.cue"))
{
    foreach (var file in files)
    {
        var fullPath = Path.Join(path, file);
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
            Console.WriteLine("Lock Acquired");
            rwLock.AcquireWriterLock(100);
            File.AppendAllText(log, $"[{DateTimeOffset.Now.ToUnixTimeSeconds()}] [{processInfo.OutFilePath.GetSha1Sig()}] Processing: {processInfo.OutFilePath}\n");
        }
        finally
        {
            Console.WriteLine("Lock Released");
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

Console.WriteLine("Completed");
Console.ReadKey();
