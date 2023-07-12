using System.Text.Json.Serialization;
using HlsAssetPush.Model;

namespace HlsAssetPush.JsonModel;

public class Media
{
    [JsonPropertyName("media_playlist")]
    public string MediaPlaylist { get; set; }
    [JsonPropertyName("track_id")]
    public Guid TrackId { get; set; }
    [JsonPropertyName("asset_id")]
    public Guid AssetId { get; set; }
    [JsonPropertyName("segments")]
    public List<string> Segments { get; set; }
}
