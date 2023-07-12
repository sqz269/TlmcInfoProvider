using System.IO;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Xml;
using HlsAssetPush;
using HlsAssetPush.JsonModel;
using HlsAssetPush.Model;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Query;

const string CONNECTION_STRING = "Host=localhost;Port=30003;Username=postgres;Password=postgrespw";

Regex SEGMENT_INDEX_REGEX = new Regex(@"segment_(\d{3})\.m4s", RegexOptions.IgnoreCase | RegexOptions.Compiled);

Console.WriteLine("Initializing DbContext");
// Initialize AppDbContext
var dbContextOptions = new DbContextOptionsBuilder<AppDbContext>()
    .UseNpgsql(CONNECTION_STRING)
    .LogTo(Console.WriteLine);

var dbContext = new AppDbContext(dbContextOptions.Options);
Console.WriteLine("DbContext Initialized");

Console.Write("Enter File Struct Path: ");
var fileStructPath = Console.ReadLine();
if (string.IsNullOrEmpty(fileStructPath))
{
    fileStructPath = @"D:\PROG\TlmcTagger\InfoProviderV3Pipeline\Preprocessor\hls-transcode\migrator\mig.json";
}

Console.Write("Enter File Struct ID Bank Path: ");
var fileStructIdBankPath = Console.ReadLine();
if (string.IsNullOrEmpty(fileStructIdBankPath))
{
    fileStructIdBankPath =
        @"D:\PROG\TlmcTagger\InfoProviderV3Pipeline\Preprocessor\hls-transcode\migrator\file-id-bank.json";
}

Console.WriteLine("Loading File Struct");
using var fileStructStream = File.OpenRead(fileStructPath);
var masterStruct = await JsonSerializer.DeserializeAsync<Dictionary<string, Dictionary<string, Media>>>(fileStructStream);
Console.WriteLine("File Struct Loaded");


Console.WriteLine("Loading File Id Bank");
using var fileIdBankStream = File.OpenRead(fileStructIdBankPath);
var idBankStruct = await JsonSerializer.DeserializeAsync<Dictionary<string, Guid>>(fileIdBankStream);
Console.WriteLine("File Id Bank Loaded");

Console.WriteLine("Opening Log Files");
var parentDir = Path.GetDirectoryName(fileStructPath);
var writeOkLog = Path.Join(parentDir, "completed.txt");
var writeFailLog = Path.Join(parentDir, "fail.txt");

var writeOkFile = new StreamWriter(writeOkLog);
var writeFailFile = new StreamWriter(writeFailLog);
Console.WriteLine($"Log file Ready: {parentDir}");

HlsPlaylist PathToHlsPlaylist(string path, int? bitrate)
{
    var id = idBankStruct[path];

    HlsPlaylistType type;
    type = bitrate.HasValue ? HlsPlaylistType.Media : HlsPlaylistType.Master;
    return new HlsPlaylist
    {
        Id = id,
        Bitrate = bitrate,
        HlsPlaylistPath = path,
        Type = type,
        Segments = new List<HlsSegment>()
    };
}

HlsPlaylist MediaToHlsPlaylist(Media media, int? bitrate)
{
    var id = idBankStruct[media.MediaPlaylist];

    HlsPlaylistType type;
    type = bitrate.HasValue ? HlsPlaylistType.Media : HlsPlaylistType.Master;
    return new HlsPlaylist
    {
        Id = id,
        Bitrate = bitrate,
        HlsPlaylistPath = media.MediaPlaylist,
        Type = type,
        Segments = new List<HlsSegment>(),
        TrackId = media.TrackId
    };
}

HlsSegment PathToHlsSegment(string path, HlsPlaylist parentPlaylist)
{
    var id = idBankStruct[path];
    var filename = Path.GetFileName(path);

    var index = -1;
    if (filename != "init.mp4")
    {
        index = int.Parse(SEGMENT_INDEX_REGEX.Match(filename).Groups[1].Value);
    }

    var segment = new HlsSegment
    {
        Id = id,
        Name = filename,
        HlsSegmentPath = path,
        Index = index,
        HlsPlaylist = parentPlaylist
    };

    parentPlaylist.Segments.Add(segment);
    return segment;
}

var i = 0;
var trackingObj = 0;
foreach (var (master, bitrateEntry) in masterStruct)
{
    i++;
    var masterKey = idBankStruct[master];
    if (await dbContext.HlsPlaylist.FirstOrDefaultAsync(p => p.Id == masterKey) != null)
    {
        Console.Write($"[{i}] Bypassed\r");
        continue;
    }
    var masterPlaylist = PathToHlsPlaylist(master, null);

    var allPlaylists = new List<HlsPlaylist>()
    {
        masterPlaylist
    };
    var segments = new List<HlsSegment>();

    var trackGuid = Guid.Empty;
    foreach (var (bitrate, media) in bitrateEntry)
    {
        //Console.WriteLine($"Processing Bitrate: {bitrate}");
        var bitrateParsed = int.Parse(bitrate);

        var mediaPlaylist = MediaToHlsPlaylist(media, bitrateParsed);

        allPlaylists.Add(mediaPlaylist);

        foreach (var segmentPath in media.Segments)
        {
            var hlsSegment = PathToHlsSegment(segmentPath, mediaPlaylist);
            segments.Add(hlsSegment);
        }

        if (trackGuid == Guid.Empty)
        {
            trackGuid = media.TrackId;
        }
    }

    masterPlaylist.TrackId = trackGuid;
    var target = (allPlaylists.Count + segments.Count);

    var t = dbContext.Tracks.FirstOrDefault(t => t.Id == allPlaylists[0].TrackId);

    trackingObj += target;
    Console.WriteLine($"[{i}] Queued {target} Entry");
    // commit changes
    dbContext.HlsPlaylist.AddRange(allPlaylists);
    dbContext.HlsSegment.AddRange(segments);

    if (trackingObj > 5000)
    {
        Console.WriteLine("Committing");
        var saved = await dbContext.SaveChangesAsync();
        if (saved != trackingObj)
        {
            Console.WriteLine($"SAVECHANGESASYNC DID NOT SAVE ALL PLAYLIST/SEGMENTS. WANT: {target}. ACTUAL: {saved}");
            continue;
        }
        Console.WriteLine($"INSERTED [{saved}]");
        trackingObj = 0;
    }
}

if (trackingObj != 0)
{
    var saved = await dbContext.SaveChangesAsync();
    Console.WriteLine($"INSERTED [{saved}]");
}