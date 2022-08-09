import json
import re
from InfoProviders.ThcInfoProvider.ThcOriginalTrackMapper.SongQuery import SongQuery
from InfoProviders.ThcInfoProvider.ThcOriginalTrackMapper.Model.OriginalTrackMapModel import OriginalTrack, TrackSource
from InfoProviders.ThcInfoProvider.ThcSongInfoProvider.Model.ThcSongInfoModel import Track, ProcessStatus

param_extr = re.compile("\{\{(.+)\|\d+\|(.+)\}\}")

def bracket_split(str, fail_on_char=True, brackets={"(": ")", "{": "}", "[": "]"}):
    stack = []
    splitted = []
    current = ""
    for c in str.strip():
        if brackets.get(c, None):
            if (current and len(stack) == 0):
                splitted.append(current)
                current = ""
            stack.append(c)
            current += c
            continue
        if len(stack) > 0 and c == brackets[stack[-1]]:
            stack.pop()
            current += c
            continue

        if fail_on_char and len(stack) == 0 and c.strip():
            raise Exception("Invalid string")
        
        current += c.strip()

    if current:
        splitted.append(current)
    return splitted

def discover():

    print("Discovering original album and tracks...")
    track: Track = None
    count = 0
    original_songs = 0
    for track in Track.select():
        if (not track.original):
            continue

        parse = json.loads(track.original)

        cq = 0
        query_params = []
        for i in parse:
            if "原曲段落" in i:
                continue

            i = bracket_split(i.strip().replace("\n", ""))
            for k in i:
                cq += 1
                original_songs += 1
                param = param_extr.match(k)
                query_params.append(param.groups())

        for q in query_params:
            count += 1
            print(f"Queried {count} tracks, {original_songs} Original songs [{cq}]", end="\r")
            q = list(q)
            q[0] = q[0].strip().replace("花映冢", "花映塚")
            SongQuery.query(q[0], q[1].strip("0|"), autofail={"地灵殿PH音乐名"}, default="<ERROR>").title_en

def load_existing(path):
    print("Loading existing...")
    with open(path, "r", encoding="utf-8") as f:
        # skip header
        f.readline()
        existing = {}
        for line in f:
            line = line.strip()
            if (not line):
                continue
            data = line.split(",")
            id = data[0]
            existing[id] = data
    return existing

def create_blank_sheet(existing):
    print("Creating blank sheet...")
    exist = load_existing(existing)
    col_names = "Id,Type,Abbriv,Full Name En,Full Name Zh,Full Name Jp,Short Name En,Short Name Zh,Short Name Jp"

    lines = []
    ids = set([source.id for source in TrackSource.select(TrackSource.id).distinct()])
    existing_ids = set(exist.keys())
    missing_ids = ids - existing_ids

    for id in missing_ids:
        lines.append(id + "," * col_names.count(","))

    for ex in exist.values():
        lines.append(",".join(ex))

    print("Created csv sheet at \"OriginalAlbums_Blank.csv\"")
    with open("OriginalAlbums_Blank.csv", "w", encoding="utf-8") as f:
        f.write(col_names + "\n")
        f.write("\n".join(lines))

if (__name__ == '__main__'):
    if (Track.select().count() == 0):
        print("No tracks found. Please run ThcSongInfoProvider first.")
        exit(0)

    if (OriginalTrack.select().count() == 0):
        discover()
    else:
        print("Original tracks found. Do you want to discover again? (y/n)")
        if (input() == "y"):
            discover()
    
    import_data = input("\nEnter Existing Csv Path (If needed): ")
    create_blank_sheet(import_data)
