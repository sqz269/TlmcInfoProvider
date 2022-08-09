import os
from typing import List, Tuple
import uuid
try:
    from BasicInfoProvider.Model.BasicInfoModel import BasicAlbum, BasicTrack, BasicInfoDb
    from BasicInfoProvider.Lib.cueparser import CueSheet
except:
    from Model.BasicInfoModel import BasicAlbum, BasicTrack, BasicInfoDb
    from Lib.cueparser import CueSheet


def parse_cue_file(path) -> Tuple[BasicAlbum, List[BasicTrack]]:
    cuesheet = None
    with open(path, "r", encoding="utf-8") as file:
        cuesheet = CueSheet()
        cuesheet.setOutputFormat("%performer% - %title%\n%file%\n%tracks%", "%offset%, %index% - %title%")
        cuesheet.setData(file.read())
        cuesheet.parse()

    album_init = {
        "album_id": str(uuid.uuid4()),
        "album_name": cuesheet.title or "",
        "performer": cuesheet.performer or "",
        "cue_path": path,
        "error_status": None if cuesheet.title else "[CUE-NT] Title is not set"
    }

    album = BasicAlbum(**album_init)

    tracks = []
    for track in cuesheet.tracks:

        e_status = None if track.index else "[CUE-NI] Index is not set"
        if not track.title:
            e_status = "[CUE-NT] Title is not set"

        track_init = {
            "track_id": str(uuid.uuid4()),
            "album": album,
            "index": track.index or -1,
            "title": track.title or "",
            "offset": track.offset,
            "flac": None,
            "error_status": e_status 
        }

        track = BasicTrack(**track_init)

        tracks.append(track)
    
    return (album, tracks)

def main():
    cue_root = input("Enter cue root: ")

    all_tracks = []
    all_albums = []

    processed = 0
    for path, _, files in os.walk(cue_root):
        for file in files:
            if (file.endswith(".cue")):
                processed += 1
                print(f"Processing [{processed}]: {file}")
                cue_path = os.path.join(path, file)
                album, tracks = parse_cue_file(cue_path)
                all_tracks.extend(tracks)
                all_albums.append(album)

    BATCH_SIZE = 2000
    for i in range(0, len(all_tracks), BATCH_SIZE):
        print(f"Saving Track {i + BATCH_SIZE}/{len(all_tracks)}")
        BasicTrack.bulk_create(all_tracks[i:i+BATCH_SIZE])

    for i in range(0, len(all_albums), BATCH_SIZE):
        print(f"Saving Album {i + BATCH_SIZE}/{len(all_albums)}")
        BasicAlbum.bulk_create(all_albums[i:i+BATCH_SIZE])

if __name__ == "__main__":
    if ((count := BasicAlbum.select().count()) != 0):
        print(f"There are existing data ({count} records) in the database. Proceeding will delete all existing data.")
        if (input("Proceed? (y/n) ") == "y"):
            print("Deleting existing data")
            BasicAlbum.delete().execute()
            BasicTrack.delete().execute()
        else:
            print("Aborting")
            exit()

    main()
