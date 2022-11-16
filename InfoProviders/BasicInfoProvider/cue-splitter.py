import os
import chardet
from InfoProviders.BasicInfoProvider.Lib.cueparser import CueSheet, CueTrack

cp = r'E:\cue'

def read_with_encoding(path):
    with open(path, "rb") as fp:
        data = fp.read()
        encoding = chardet.detect(data)["encoding"]
        return data.decode(encoding, errors="ignore")

def san_chk(cp):
    ok, fail = 0, 0
    for path, dirs, files in os.walk(cp):
        for f in files:
            cue = CueSheet()
            print(f"[{fail} {ok} {fail + ok}] Checking: ", os.path.join(path, f))
            
            cue.setData(read_with_encoding(os.path.join(path, f)))
            cue.setOutputFormat("%performer% - %title%\n%file%\n%tracks%", "%performer% - %title%")
            cue.parse()
            track: CueTrack
            for track in cue.tracks:    
                if (not track.title):
                    print(f"Track {track.index} has no title")
                    fail += 1
                elif (not track.index):
                    print(f"Track {track.index} has no index")
                    fail += 1
                elif (not track.offset):
                    print(f"Track {track.index} has no offset")
                    fail += 1
                elif (not track.duration):
                    print(f"Track {track.index} has no duration. Offset {track.offset}")
                    fail += 1
                elif (not track.performer):
                    print(f"Track {track.index} has no performer")
                    fail += 1
                else:
                    ok += 1

san_chk(cp)
