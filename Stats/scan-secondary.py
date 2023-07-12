import os
import json

if (__name__ == '__main__'):
    tlmc_root = input("TLMC root: ") or "/ext_data_b/torrent/TLMC v3/"

    groups = {}
    for circle in os.listdir(tlmc_root):
        circle_path = os.path.join(tlmc_root, circle)
        if (not os.path.isdir(circle_path)):
            continue

        for album in os.listdir(circle_path):
            album_path = os.path.join(circle_path, album)
            if (not os.path.isdir(album_path)):
                continue

            for filename in os.listdir(album_path):
                file_path = os.path.join(album_path, filename)
                if (not os.path.isfile(file_path)):
                    continue

                groups.setdefault(album_path, []).append(filename)


    with open("scan-secondary.json", "w", encoding="utf-8") as f:
        json.dump(groups, f, indent=4, ensure_ascii=False)
