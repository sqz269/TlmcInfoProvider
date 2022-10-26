using System.Drawing;
using System.Runtime.CompilerServices;
using System.Text;
using System.Xml;
using FFMpegCore;
using FFMpegCore.Arguments;

namespace CueSplitter;

public struct CueProcessInfo
{
    public string Album { get; set; }
    public string FileName { get; set; }
    public string OutFilePath { get; set; }
    public FFMpegArgumentProcessor Processor { get; set; }
}

public static class CueSplit
{
    public static Dictionary<char, char> REPLACE_CHARS = new()
    {
        {'/', '／'},
        {'\\', '＼'},
        {':', '：'},
        {'*', '＊'},
        {'?', '？'},
        {'\"', '＂'},
        {'<', '＜'},
        {'>', '＞'},
        {'|', '｜'}
    };

    public static bool SanCheckCue(CueSheet sheet, out List<string> problems)
    {
        problems = new List<string>();
        foreach (var track in sheet.Tracks)
        {
            if (!track.Indices.Any())
            {
                problems.Add($"Track has no indices");
            }
            else 
            {
                Console.WriteLine(track);
                if (track.Indices.Length >= 2)
                {
                    if (track.Indices[1].Number != 1)
                    {
                        Console.ReadKey();
                    }
                }
            }
        }

        return problems.Count == 0;
    }

    private static string MkFileName(Track track, CueSheet origin)
    {
        var sb = new List<string>();
        
        sb.Add($"({track.TrackNumber})");

        if (string.IsNullOrWhiteSpace(track.Performer))
        {
            sb.Add($"[{track.Performer}]");
        }
        else
        {
            sb.Add($"[{origin.Performer}]");
        }

        sb.Add($"{track.Title}.flac");

        // The file names could contain / and \, which may cause issues
        // so we need to replace the / and \ characters to full width part to avoid path issues
        var str = string.Join(' ', sb);
        foreach (var (key, value) in REPLACE_CHARS)
        {
            str = str.Replace(key, value);
        }

        return str;
    }

    private static CueProcessInfo MkSplitArgs(Track track, CueSheet origin, Index begin, Index? end, string root)
    {
        // only the first file have data file prop
        var filePath = Path.Combine(root, origin.Tracks[0].DataFile.Filename);
        if (!File.Exists(filePath))
        {
            throw new FileNotFoundException($"Unable to find file specified by the cue file {filePath}");
        }

        var outpath = Path.Combine(root, MkFileName(track, origin));

        var processor = FFMpegArguments
            .FromFileInput(filePath)
            .OutputToFile(outpath, true, options =>
            {
                options.Seek(begin.ToTimeSpan());
                if (end != null)
                    options.WithDuration(begin.Duration(end.Value));
                options.WithFastStart();
            });

        return new CueProcessInfo
        {
            Album = origin.Title,
            OutFilePath = outpath,
            FileName = track.Title,
            Processor = processor
        };
    }

    private static List<CueProcessInfo> Split(CueSheet sheet, string root)
    {
        var list = new List<CueProcessInfo>(sheet.Tracks.Length);
        for (var i = 0; i < sheet.Tracks.Length; i++)
        {
            var track = sheet.Tracks[i];
            Index start;
            Index? end = null;
            // Always take the first index as the start
            // Same as MPV strategy:
            // https://github.com/mpv-player/mpv/blob/375076578f4c1c450ecf0b60de6290ad9942ddfc/demux/demux_mkv.c#L852
            start = track.Indices[0];

            // While we haven't reached end of tracks
            if (i + 1 < sheet.Tracks.Length)
            {
                var next = sheet.Tracks[i + 1];

                end = next.Indices[0];
            }

            list.Add(MkSplitArgs(track, sheet, start, end, root));
        }

        return list;
    }

    public static List<CueProcessInfo> SplitCue(string root, string cuePath)
    {
        var cueFile = FileUtils.ReadFileAutoEncoding(cuePath);
        var cue = new CueSheet(cueFile, new char[] { '\r', '\n' });

        return Split(cue, root);
    }
}