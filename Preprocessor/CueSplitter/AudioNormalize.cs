using CueSplitter.DirectoryWalk;
using FFMpegCore;

namespace CueSplitter;

public struct NormalizeProcessInfo
{
    public string OriginalFile { get; set; }
    public string OutFile { get; set; }
    public FFMpegArgumentProcessor Processor { get; set; }
}

public static class AudioNormalize
{
    private static FFMpegArgumentProcessor MkNormalizeArgs(string input, string output)
    {
        return FFMpegArguments
            .FromFileInput(input)
            .OutputToFile(output, true, opt =>
            {
                opt.WithCustomArgument("-af loudnorm");
                opt.WithFastStart();
            })
            .NotifyOnError((error) =>
            {
                Console.WriteLine($"ERRROR >>> {error}");
            })
            .NotifyOnOutput((output) =>
            {
                Console.WriteLine($"OUTPUT >>> {output}");
            })
            .NotifyOnProgress((progress) =>
            {
                Console.WriteLine($"PROGRESS >>> {progress}");
            });
    }

    public static List<string> AudioExt = new()
    {
        ".flac",
        ".mp3",
        ".wav",
        ".m4a",
        ".aac"
    };

    public static Queue<NormalizeProcessInfo> Normalize(string root)
    {
        var argumentProcessors = new Queue<NormalizeProcessInfo>();

        var directoryTree = new DirectoryTree();
        foreach (var (path, dirs, files) in directoryTree.WalkSilently(root))
        {
            foreach (var file in files)
            {
                bool haveValidExtension = AudioExt.Any(ext => file.EndsWith(ext));

                if (!haveValidExtension)
                {
                    continue;
                }

                var fullPath = Path.Combine(path, file);
                var outPath = Path.Combine(path, $"LNORM__{file}");
                argumentProcessors.Enqueue(new NormalizeProcessInfo()
                {
                    OriginalFile = fullPath,
                    OutFile = outPath,
                    Processor = MkNormalizeArgs(fullPath, outPath)
                });
                Console.WriteLine($"Cue Executor Cmd: {argumentProcessors.Last().Processor.Arguments}");
            }
        }

        return argumentProcessors;
    }
}