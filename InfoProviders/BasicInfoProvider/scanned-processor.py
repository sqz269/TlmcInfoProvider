from fileinput import filename
import json
import re
from typing import Any, Dict, List
from uuid import uuid4
from InfoProviders.BasicInfoProvider.Model.BasicInfoModel import BasicAlbum, BasicTrack

"""
TODO: FLAG CERTAIN ALBUMS FOR CUE SPLITTING.
SOME OF THE ALBUMS HAVE MERGED TRACKS AND NEED TO BE SPLIT.
THIS SPECIAL STATUS SHOULD BE MARKED WHEN INSERTING INTO THE DATABASE.
BY CHECKING IF A TRACK HAS A CUE FILE ASSOCIATED WITH IT AND ONLY HAVE ONE FILE

[INSTANCE: [Solar]]

Potential ways to handle splitting:
1. split before committing into production database
    - Advantages:
        - no need to change database schema
2. pass the cue file to the production server and let it handle the splitting
    - Advantages:
        - Allow for more flexibility in splitting, and allows future upload to be splitted without
            the need to reinitialize the database
    - Disadvantages:
        - Requires more work on the production server
        - Special Rest Endpoint needed for splitting. More database fields needed
"""

CIRCLE_INFO_EXTRACTOR = re.compile(r'\[(.+)\]')
ALBUM_INFO_EXTRACTOR = re.compile(r'(\d{4}(?:\.\d{2})?(?:\.\d{2})?)? ?(?:\[(.+\-.+)\])? ?(.+)')
TRACK_INFO_EXTRACTOR = re.compile(r'(?:\((\d+)\) )?(?:\[(.+)\] )?(.+)(?:(?:.mp3)|(?:.flac))')

IMAGE_FILE_SUFFIX = (".jpg", "tif", "png")

exclusive = {"2011.05.08 [S] [例大祭8]":
                ("刻刻音樂館", None, "2011.05.08", None, "[S]", "例大祭8"),
            "2009.12.30 [ECPR-0002] [Eclat：] [C77]": 
                ("＜echo＞PROJECT", None, "2009.12.30", "ECPR-0002", "Eclat：", "C77"),
            "2009.03.08 [ECPR-0001] [neutrino＊] [例大祭6]": 
                ("＜echo＞PROJECT", None, "2009.03.08", "ECPR-0001", "neutrino＊", "例大祭6"),
            "2011.05.08 [N] [例大祭8]": 
                ("生パン庫", None, "2011.05.08", None, "N", "例大祭8"),
            "2008.11.02 [BLCD-11] 東方音伽盤[改] [東方紅楼夢4]": 
                ("Black Label Records", None, "2008.11.02", "BLCD-11", "東方音伽盤[改]", "東方紅楼夢4"),
            "2009.09.27 [SICD-047] Tri1-Obedience Love[MxA] [サンクリ45]": 
                ("Iemitsu.／A", None, "2009.09.27", "SICD-047", "Tri1-Obedience Love[MxA]", "サンクリ45"),
            "2014.08.16 [maboroshinthe] [C86]" :
                ("モジャン棒", None, "2014.08.16", None, "maboroshinthe", "C86"),
            "2012.08.11 [STCD-0041] シエステールの再放送[darkside] [C82]": 
                ("SiesTail", None, "2012.08.11", "STCD-0041", "シエステールの再放送[darkside]", "C82"),
            "2012.08.11 [STCD-0040] シエステールの再放送[Starred] [C82]":
                ("SiesTail", None, "2012.08.11", "STCD-0040", "シエステールの再放送[Starred]", "C82"),
            "2009.03.22 [DACD-001] [東方祀花謠 ～Les Illusions des Cent Fleurs] [上海TH01]": 
                ("Dandelion Trio", None, "2009.03.22", "DACD-001", "東方祀花謠 ～Les Illusions des Cent Fleurs", "上海TH01"),
            "2012.05.27 [nd-003] 宵闇の楽園[→side：R→] [例大祭9]": 
                ("宵闇の楽園[→side：R→]", None, "2012.05.27", "nd-003", "宵闇の楽園[→side：R→]", "例大祭9"),
            "2015.12.30 [LLAC-0022] Nature2 [LiLA'c Records Best 2008-2015] [C89]": 
                ("LiLA'c Records", None, "2015.12.30", "LLAC-0022", "Nature2 [LiLA'c Records Best 2008-2015]", "C89"),
            "2017.05.07 [LLAC-0026] TOHO SPEED BEST TRAX [2013-2017] [例大祭14]": 
                ("LiLA'c Records", None, "2017.05.07", "LLAC-0026", "TOHO SPEED BEST TRAX [2013-2017]", "例大祭14"),
            "2013.10.27 [MTCD-0010] 艦これオーケストラ! [M3-32][分轨]": 
                ("Melodic Taste", None, "2013.10.27", "MTCD-0010", "艦これオーケストラ!", "M3-32"),
            }

def handle_exclusive(ex):
    return exclusive[ex]

def parse_title(title: str):
    if title[-1] != "]":
        return title, None
    for i in range(len(title) - 1, 0, -1):
        if title[i] == "[":
            title_actual = title[:i - 1]
            convention = title[i+1:len(title)-1]
            return title_actual, convention

def gen_td(fn, fp):
    track_info = TRACK_INFO_EXTRACTOR.match(fn)
    try:
        index = track_info.group(1)
        performer = track_info.group(2)
        title = track_info.group(3)
    except:
        return None

    return {
        "track_id": str(uuid4()),
        "index": index,
        "performer": performer,
        "title": title,
        "flac": fp
    }

def process(data):
    album_count = 0
    track_count = 0
    result = []
    for circle in data:
        for album in data[circle]:
            album_count += 1
            if album in exclusive:
                album_artist, album_info, release_date, catalog, title, convention = handle_exclusive(album)
            else:
                print(f"[{album_count}] {album}")
                album_artist = CIRCLE_INFO_EXTRACTOR.match(circle).group(1)
                album_info = ALBUM_INFO_EXTRACTOR.match(album)
                release_date = album_info.group(1)
                catalog = album_info.group(2)
                title, convention = parse_title(album_info.group(3))
            album_data = {}
            album_data["album_id"] = str(uuid4())
            album_data["album_name"] = title
            album_data["release_date"] = release_date
            album_data["catalog_number"] = catalog
            album_data["release_convention"] = convention
            album_data["performer"] = album_artist
            album_data["album_img"] = None
            album_data["other_img"] = []
            album_data["other_files"] = []
            album_data["tracks"] = []

            # check if album contains cue file
            cue_file = None
            for file_name, file_path in data[circle][album].items():
                if (file_name.lower().endswith(IMAGE_FILE_SUFFIX)):
                    if (file_name == "folder.jpg"):
                        album_data["album_img"] = file_path
                    else:
                        album_data["other_img"].append(file_path)
                    continue
                if (file_name.lower().endswith((".flac", ".mp3"))):
                    track_count += len(album_data["tracks"])
                    trk = gen_td(file_name, file_path)
                    if (trk is not None):
                        album_data["tracks"].append(trk)
                else:
                    album_data["other_files"].append(file_path)
                
                if (file_name.lower().endswith(".cue")):
                    cue_file = file_path
            
            # if cue file exists, we need to flag the album
            if cue_file:
                album_data["need_cue_split"] = True
                album_data["target_cue_path"] = cue_file
                if (len(album_data["tracks"]) != 1):
                    # print(album_data["tracks"])
                    print("Cue file found but more than 1 track found. Ignoring cue file.")
                album_data["target_audio"] = album_data["tracks"]
            result.append(album_data)
        
    return result

def normalize_obj(obj: Dict[str, Any]):
    for key, item in obj.items():
        if isinstance(item, list):
            obj[key] = json.dumps(item)
        elif isinstance(item, dict):
            obj[key] = json.dumps(item)
        elif isinstance(item, str):
            obj[key] = item.strip()


def push(result):
    album_obj = []
    track_obj = []
    alb_count = 0
    trk_count = 0
    for album in result:
        alb_tmp = album.copy()
        del alb_tmp["tracks"]

        normalize_obj(alb_tmp)

        t = BasicAlbum(**alb_tmp)

        tracks = album["tracks"]

        alb_count += 1

        for track in tracks:
            trk_count += 1
            normalize_obj(track)
            track.update({"album": alb_tmp["album_id"]})
            print(f"[{alb_count}] Initializing Track #{trk_count}", end="\r")
        trk = [BasicTrack(**track) for track in tracks]

        album_obj.append(t)
        track_obj.extend(trk)

    print()
    BULK_SIZE = 1000
    for i in range(0, len(album_obj), BULK_SIZE):
        print("Inserting album {} to {}".format(i, i + BULK_SIZE))
        BasicAlbum.bulk_create(album_obj[i:i+BULK_SIZE])
    for i in range(0, len(track_obj), BULK_SIZE):
        print("Inserting track {} to {}".format(i, i + BULK_SIZE))
        BasicTrack.bulk_create(track_obj[i:i+BULK_SIZE])

if (__name__ == '__main__'):
    with open(r"data.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    results = process(data)   
    push(results) 
