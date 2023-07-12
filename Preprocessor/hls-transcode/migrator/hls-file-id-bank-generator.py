import json
import uuid

hls_file_struct_fp = input("Enter the hls file struct path: ") or "mig.json"

print("Loading hls file struct...")
with open(hls_file_struct_fp, "r", encoding="utf-8") as f:
    hls_file_struct = json.load(f)

print("Generating file id bank...")

id_map = {}
for indx, (master_playlist, bitrate_dir_map) in enumerate(hls_file_struct.items()):
    id_map[master_playlist] = str(uuid.uuid4())
    for bitrate, dir_map in bitrate_dir_map.items():
        media_playlist = dir_map["media_playlist"]
        id_map[media_playlist] = str(uuid.uuid4())
        segments = dir_map["segments"]
        for segment in segments:
            id_map[segment] = str(uuid.uuid4())
    print(f"{indx} Proc", end="\r")

print("Saving file id bank...")
with open("file-id-bank.json", "w", encoding="utf-8") as f:
    json.dump(id_map, f, indent=4, ensure_ascii=False)
