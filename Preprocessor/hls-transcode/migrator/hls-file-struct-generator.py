import os
import json
import re

filelist_fp = input("Enter the filelist path: ")

BITRATE_DIR_REGEX = r"^(\d+)k$"

with open(filelist_fp, "r", encoding="utf-8") as f:
    filelist = json.load(f)

st = {}
mp, sg = (0, 0)
for i, (key, entry) in enumerate(filelist["processed"].items()):
    master_playlist = entry["master_playlist"]

    parent = os.path.dirname(master_playlist)

    hls_dir = os.path.join(parent, "hls")

    bitrate_map = {}
    dirs = [d for d in os.listdir(hls_dir) if os.path.isdir(os.path.join(hls_dir, d))]
    for dir in dirs:
        m = re.match(BITRATE_DIR_REGEX, dir)
        if m:
            bitrate_map[int(m.group(1))] = dir

    bitrate_dir_map = {}
    for bitrate, dir in bitrate_map.items():
        bitrate_dir = os.path.join(hls_dir, dir)
        media_playlist = os.path.join(bitrate_dir, "playlist.m3u8")

        if not os.path.isfile(media_playlist):
            input(f"INVALID RECONSTRUCT MEDIA PLAYLIST: {media_playlist}")

        segments = []
        for item in os.listdir(bitrate_dir):
            abs_path = os.path.join(bitrate_dir, item)
            if os.path.isfile(abs_path):
                if abs_path != media_playlist:
                    segments.append(abs_path)

        bitrate_dir_map[bitrate] = {
            "media_playlist": media_playlist,
            "trackId": entry["TrackId"],
            "assetId": entry["AssetId"],
            "segments": segments,
        }

    st[master_playlist] = bitrate_dir_map

    print(f"{i} Processed: {master_playlist}")

with open("mig.json", "w", encoding="utf-8") as f:
    json.dump(st, f, indent=4, ensure_ascii=False)
