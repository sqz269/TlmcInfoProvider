import os
import json

ASSET_JSON_PATH = 'Preprocessor/Transcode/postgres_public_Assets.json'
TRACK_JSON_PATH = 'Preprocessor/Transcode/postgres_public_Tracks.json'

def make_output_path(og_path):
    dir = os.path.dirname(og_path)
    filename = os.path.basename(og_path)
    filename = filename.split('.')[0]
    filename = filename + '.m4a'
    return "/".join([dir, filename])

def main():
    with open(ASSET_JSON_PATH, 'r', encoding="utf-8") as f:
        assets = json.load(f)
    with open(TRACK_JSON_PATH, 'r', encoding="utf-8") as f:
        tracks = json.load(f)

    asset_id_mapped = {}
    for asset in assets:
        asset_id_mapped[asset['AssetId']] = asset

    trackid_assetid_maps = {}
    for track in tracks:
        trackid_assetid_maps[track['Id']] = track['TrackFileAssetId']

    q_result = {}
    for trackid, assetid in trackid_assetid_maps.items():
        asset = asset_id_mapped[assetid]
        struct = {
            'TrackId': trackid,
            'AssetId': assetid,

            'size': asset['Size'],

            'src': asset['AssetPath'],
            'dst': make_output_path(asset['AssetPath']),

            "processed": False,
            "error": None
        }

        q_result[asset["AssetPath"]] = struct
    
    complete_struct = {
        "processed": {},
        "failed": {},
        "queued": q_result
    }

    with open('Preprocessor/Transcode/queue.json', 'w', encoding="utf-8") as f:
        json.dump(complete_struct, f, indent=4)

if __name__ == '__main__':
    main()
