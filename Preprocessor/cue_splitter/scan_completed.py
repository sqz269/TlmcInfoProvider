import os
import json

def load_file_list(file_list):
    with open(file_list, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def check_completed(file_list):
    out_data = {"exists": [], "no_size": [], "no_exists": []}
    for items in file_list["processed"].values():
        for track in items["Tracks"]:
            track_path = os.path.join(items["Root"], track["TrackName"])
            try:
                os.unlink(track_path)
            except FileNotFoundError:
                print(f"\n\nFile not found: {track_path}\n\n")
            print(f"Removed {track_path}", end="\r")
            # if os.path.exists(track_path):
            #     if os.path.getsize(track_path) > 0:
            #         out_data["exists"].append({track_path: os.path.getsize(track_path)})
            #     else:
            #         out_data["no_size"].append(track_path)
            # else:
            #     out_data["no_exists"].append(track_path)

    return out_data

if (__name__ == '__main__'):
    file_list = load_file_list(input("File list: "))
    out_data = check_completed(file_list)
    with open("out_data.json", "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=4)
