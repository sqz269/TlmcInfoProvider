import json
import os
from pprint import pprint
import re
# from InfoProviders.BasicInfoProvider.Model.BasicInfoModel import BasicAlbum, BasicTrack

CIRCLE_INFO_EXTRACTOR = re.compile(r'\[(.+)\]')
ALBUM_INFO_EXTRACTOR = re.compile(r'(\d{4}(?:\.\d{2})?(?:\.\d{2})?)? ?(?:\[(.+\-.+)\])? ?(.+)')
TRACK_INFO_EXTRACTOR = re.compile(r'(?:\((\d+)\) )?(?:\[(.+)\] )?(.+)(?:(?:.mp3)|(?:.flac))')

def walk_root(root="."):
    circles = os.listdir(root)
    for circle in circles:
        path = os.path.join(root, circle)
        if not os.path.isdir(path):
            continue
        albums = [fo for fo in os.listdir(path) if os.path.isdir(os.path.join(path, fo))]
        for album in albums:
            album_path = os.path.join(path, album)
            fp_map = {}
            for ap, _, f in os.walk(album_path):
                for file in f:
                    # file_names.append(file)
                    # file_paths.append(os.path.join(ap, file))
                    fp_map[file] = os.path.join(ap, file)

            # fn = [f for f in files if os.path.isfile(os.path.join(album_path, f))]
            # fp = [os.path.join(album_path, f) for f in files if os.path.isfile(os.path.join(album_path, f))]
            yield (circle, album, fp_map)

if (__name__ == '__main__'):
    data = {}
    i = 0
    root = input("Enter TLMC root directory")
    for circle, album, fp_map in walk_root(root):
        print(f"Scanning {i}", end='\r')
        i += 1
        if data.get(circle) is None:
            data[circle] = {
                album: fp_map
            }
        else:
            data[circle][album] = fp_map
    serialized = json.dumps(data, indent=4, ensure_ascii=False)
    with open("data.json", "w") as file:
        file.write(serialized)

# with open("E:\data.json", "r", encoding="utf-8") as file:
#     data = json.load(file)

#     for circle, albums in data.items():

#         for album in albums.keys():
#             match = ALBUM_INFO_EXTRACTOR.match(album)
#             grp = match.groups()
#             print(grp)
#             # input()
#             if not any(grp):
#                 print(f"Failed to parse album: {album}")
#                 input()
#                 continue
