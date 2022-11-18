using System.Text;
using FFMpegCore;
using CueSplitter;

Console.OutputEncoding = Encoding.UTF8;

Console.WriteLine("Enter FFMPEG directory:");

var ffmpegDir = Console.ReadLine()?.Trim();
if (string.IsNullOrWhiteSpace(ffmpegDir))
{
    ffmpegDir = "D:\\Tools\\ffmpeg-master-latest-win64-gpl\\bin";
    Console.WriteLine($"Using default FFMPEG directory: {ffmpegDir}");
}

GlobalFFOptions.Configure(opt => opt.BinaryFolder = ffmpegDir);


Console.WriteLine("Choose Directory: ");

var dir = Console.ReadLine()?.Trim();
if (!(new DirectoryInfo(dir).Exists))
{
    Console.WriteLine("Directory does not exist");
    return;
}

Console.WriteLine("Choose Preprocessing: ");
Console.WriteLine("1. Split");
Console.WriteLine("2. Normalize Audio");
// (1) split or (2) normalize
var preprocessing = Console.ReadLine()?.Trim();

if (preprocessing == "1")
{
    // Split
    Op.SplitOp(dir);
}
else if (preprocessing == "2")
{
    Op.NormalizeOp(dir);
}
