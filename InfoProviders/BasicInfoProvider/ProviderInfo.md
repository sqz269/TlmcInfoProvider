# Expected format

This Provider Should format the data from file names or Cue sheets into a readily queried format

## Destnation Format

Each album should have a unique AlbumId, TrackId (UUID) and that ID should be kept the same throughout the pipeline

Each Entry should also have a record to the path of original files (Cue or Flac).

The process should keep as much metadata as possible

The post transform format shoud be something resembling this. The final format may or may not be denormalized

```json
{
    "albumId": "<AlbumId>",
    "albumName": "<AlbumName>",
    "__performer": "<Performer>",
    "phyiscal_path": "<Cue File>",
    "tracks": {
        "trackId": "<TrackId>",
        "trackName": "<TrackName>",
        "trackIndex": "<TrackIndex>",
        "trackOffset": "<Cue Offset>", // If processing cues
        "trackPath": "<Track Path>"
    }
}
```
