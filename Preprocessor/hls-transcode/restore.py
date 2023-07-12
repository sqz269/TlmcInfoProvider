import os
import json

def mk_master_playlist_path(target):
    parent = os.path.dirname(target)
    filename = os.path.basename(target)
    filename = filename[:filename.rfind(".")]
    return os.path.join(parent, filename, "playlist.m3u8")

if __name__=="__main__":
    filelist_path = input("Enter filelist path (Original): ")

    with open(filelist_path, 'r', encoding="utf-8") as f:
        data = json.load(f)

    for target_path, target_info in data["queued"].items():
        master_playlist_fp = mk_master_playlist_path(target_path)
        if ((not os.path.isfile(target_info["src"])) and
            (os.path.isfile(master_playlist_fp))):
            print("Found processed master playlist: {}".format(master_playlist_fp))

            target_info["processed"] = True
            data["processed"].update({target_path: target_info})
            del data["queued"][target_path]

            target_info["master_playlist"] = master_playlist_fp

    print("Writing filelist...")
    with open(f"rest_{filelist_path}", 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
