from base64 import encode
from datetime import datetime
import json
from unittest.loader import VALID_MODULE_NAME
from uuid import uuid4
from InfoProviders.BasicInfoProvider.Model.BasicInfoModel import BasicAlbum, BasicTrack, BasicAlbumPerformer, BasicCircle
import requests
import os

from pathlib import Path

HOST = "http://localhost:5217"
ADD_ASSET_ENDPOINT = HOST + "/api/internal/asset/add"
ADD_ALBUM_ENDPOINT = HOST + "/api/internal/album/add/{albumId}"
ADD_TRACK_ENDPOINT = HOST + "/api/internal/album/{albumId}/track/add/{trackId}"

# some of the albums have bad dates like 
# Breath - ブレス - which has a release date of 2017-12-39

replace_date = {
    "2017.12.39": "2017.12.31",
}

# replace . with - in the date
replace_date = {
    k.replace(".", "-"): v.replace(".", "-") for k, v in replace_date.items()
}

def mk_localized_field(value: str, normalize: bool=True):
    if (normalize):
        value = value.replace('\u200c', '').strip()
    
    if (value.isascii()):
        return {
            "default": value,
            "jp": value,
            "en": value
        }

    return {
        "default": value,
        "jp": value,
    }

def push_asset(path: str) -> str:
    p = Path(path)
    ext = p.suffix.lower()

    ext_to_mime = {
        ".jpg": "image/jpeg", 
        ".tif": "image/tiff", 
        ".png": "image/png",
        ".flac": "audio/flac"
    }

    assetObj = {
        "assetId": str(uuid4()),
        "assetName": p.name,
        "assetPath": path,
        "assetMime": ext_to_mime.get(ext, None),
        "large": ext==".flac"
    }

    result = requests.post(ADD_ASSET_ENDPOINT, json=assetObj)
    if (result.status_code == 200):
        return result.json()["assetId"]
    else:
        raise Exception("FAILED TO ADD NEW ASSET. SERVER RETURNED CODE {}".format(result.status_code))

def push_album(album: BasicAlbum) -> str:
    release_date = album.release_date.replace(".", "-") if album.release_date else None # datetime.strptime(album.release_date, "%Y.%m.%d")

    album_img_id = push_asset(album.album_img) if album.album_img else None

    other_img = json.loads(album.other_img) if album.other_img else []
    other_img = [push_asset(img) for img in other_img]

    # Handle cases where release date is not exact
    # so the ones ends with xx.
    # for example 2019.xx.xx or 2008.05.xx
    if release_date and release_date[-2:] == "xx":
        # Replace xx with 01
        release_date = release_date.replace("xx", "01")
        time = "23:59:59.999"
        release_date = f"{release_date}T{time}Z"

    # Get album artist
    artists = []
    for jointable in BasicAlbumPerformer.select().where(BasicAlbumPerformer.album_id == album.album_id):
        # print(jointable.performer_id.id)
        artists.append(jointable.performer_id.id)

    if (release_date in replace_date):
        release_date = replace_date[release_date]

    album_to_add = {
        "albumName": mk_localized_field(album.album_name),
        "releaseDate": release_date,
        "releaseConvention": album.release_convention,
        "catalogNumber": album.catalog_number,
        "albumArtist": artists,
        "numberOfDiscs": 1
    }

    if (album_img_id):
        album_to_add["albumImage"] = album_img_id

    if (other_img):
        album_to_add["otherImages"] = other_img

    result = requests.post(ADD_ALBUM_ENDPOINT.format(albumId=album.album_id), json=album_to_add)
    if (result.status_code == 201 or result.status_code == 200):
        return result.json()["id"]
    else:
        print("\n\nERROR: SERVER RETURNED CODE {}".format(result.status_code))
        print(result.text)
        print(album_to_add)
        raise Exception("FAILED TO ADD NEW ALBUM. SERVER RETURNED CODE {}".format(result.status_code))

def push_track(album_id, track: BasicTrack) -> str:
    if (not track.flac):
        raise Exception("TRACK {} HAS NO FLAC FILE".format(track.track_id))
    track_file = push_asset(track.flac)

    track_to_add = {
        "name": mk_localized_field(track.title, True),
        "index": int(track.index) if track.index else 0,
        "disc": 1,
        "staff": [track.performer],
        "originalNonTouhou": False,
        "trackFile": track_file
    }

    result = requests.post(ADD_TRACK_ENDPOINT.format(albumId=album_id, trackId=track.track_id), json=track_to_add)
    if (result.status_code == 201 or result.status_code == 200):
        return result.json()["id"]
    else:
        print("\n\nERROR: SERVER RETURNED CODE {}".format(result.status_code))
        print(result.text)
        print(track_to_add)
        raise Exception("FAILED TO ADD NEW TRACK. SERVER RETURNED CODE {}".format(result.status_code))

def push():
    album: BasicAlbum = None

    album_total = BasicAlbum.select().count()
    track_total = BasicTrack.select().count()

    alb_count = 0
    trk_count = 0
    for album in BasicAlbum.select().iterator():
        alb_count += 1
        album_id = push_album(album)
        track: BasicTrack
        for track in BasicTrack.select().where(BasicTrack.album == album.album_id).iterator():
            trk_count += 1
            print(f"[{alb_count}/{album_total}({round(alb_count/album_total * 100, 2)}%)] [{trk_count}/{track_total}({round(trk_count/track_total * 100, 2)})%)] Pushing track {track.track_id} for {album.album_id}", end="\r")
            track_id = push_track(album.album_id, track)
        
album_count = BasicAlbum.select().count()
track_count = BasicTrack.select().count()

print(f"Total albums: {album_count} Total tracks: {track_count}")
print("Push to DB? (y/n) **THIS OPERATION MAY NOT BE INTERRUPTED**")
if input() == "y":
    print("Pushing to DB...")
    push()
else:
    print("Aborted.")
