using System.ComponentModel.DataAnnotations;

namespace HlsAssetPush.Model;

public class HlsSegment
{
    [Key]
    public Guid Id { get; set; }
    
    public int Index { get; set; }
    
    public string Name { get; set; }
    
    public string HlsSegmentPath { get; set; }

    public Guid HlsPlaylistId { get; set; }
    public HlsPlaylist HlsPlaylist { get; set; }
}