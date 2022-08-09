from typing import Dict
from InfoProviders.ThcInfoProvider.ThcOriginalTrackMapper.SongQuery import SongQuery
from InfoProviders.ThcInfoProvider.ThcSongInfoProvider.Model.ThcSongInfoModel import Track, Album, ProcessStatus
from InfoProviders.ThcInfoProvider.ThcSongInfoFomatter.Model.InfoFormattedModel import AlbumFormatted, TrackFormatted

def map_title(album) -> Dict:
    pass

def import_data():
    album: Album = None
    for album in Album.select():
        tracks = Track.select().where(Track.album == album)
        if (len(tracks) > 50):
            print(f"{album.album_id}: {len(tracks)} tracks [{album.data_source}]")

if (__name__ == '__main__'):
    album_count = AlbumFormatted.select().count()
    track_count = TrackFormatted.select().count()
    if (album_count == 0):
        import_data()
    else:
        print(f"There are already {album_count} albums and {track_count} tracks in the database")
        print("Do you want to re-import the data? (y/n)")
        if (input() == 'y'):
            # Delete all data
            AlbumFormatted.delete().execute()
            TrackFormatted.delete().execute()
            import_data()
        else:
            print("Exiting...")
            exit()
