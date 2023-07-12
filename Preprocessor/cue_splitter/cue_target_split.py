from colorama import init, Fore

init(True)

from pythonnet import load

load("coreclr")

import re
import os
import clr
import sys
import json
import time
import shlex
import traceback

import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

# WARN: THERE ARE CASES WHERE THE SPLIT OPERATION WILL FAIL,
# RESULTING IN A 0 BYTE FILE. NEED TO ADD CHECK FOR THIS AND
# RE-TRY THE SPLIT OPERATION.

# ALSO FFMPEG COMMAND NEEDS TO BE VALIDATED

# sys.path.append(r"C:\PROG\TlmcTagger\InfoProviderV3Pipeline\Preprocessor\cue_split_info_provider\CueSplitInfoProvider\CueSplitInfoProvider\bin\Debug\net6.0")

print(os.path.join(os.getcwd(), r"Preprocessor/cue_splitter/lib/CueSplitInfoProvider.dll"))

venv_target = os.path.join(os.getcwd(), r"Preprocessor/cue_splitter/lib/CueSplitInfoProvider.dll")
exec_target = os.path.join(os.getcwd(), r"lib/CueSplitInfoProvider.dll")
if (os.path.exists(exec_target)):
    print("Loading DLL from: " + exec_target)
    clr.AddReference(exec_target)
else:
    # probably running in venv at root
    print("Loading DLL from: " + venv_target)
    clr.AddReference(venv_target)

from CueSplitter import CueSplit
from System.IO import *

def mk_ffmpeg_cmd(track, info):
    """
    root: the root path of the file we are processing
    track: the track we are processing, should be a dict
    info: the album info of the track, should be a dict
    """
    audio_path = info["AudioFilePath"]
    if (info["AudioFilePathGuessed"]):
        audio_path = info["AudioFilePathGuessed"]

    out = os.path.join(info["Root"], track["TrackName"])

    audio_path = shlex.quote(audio_path)
    out = shlex.quote(out)
    if (not track["Duration"]):
        return ['-i', f'{audio_path}', '-ss', track["Begin"], '-movflags', 'faststart', f'{out}', '-y', '-stats', '-v', 'quiet']
    else:
        return ['-i', f'{audio_path}', '-ss', track["Begin"], '-t', track["Duration"], '-movflags', 'faststart', f'{out}', '-y', '-stats', '-v', 'quiet']

def main():
    split_data = []
    if (os.path.exists("split_data.json")):
        with open("split_data.json", "r", encoding="utf-8") as f:
            split_data = json.loads(f.read())

    while True:
        cue_path = input("Enter cue file path: ")
        root = os.path.dirname(cue_path)

        if (not os.path.exists(cue_path)):
            print("Invalid path")
            continue
        result = json.loads(CueSplit.SplitCue(root, cue_path))
        if (result["Invalid"]):
            print("Failed to parse cue file. Invalid")
            continue

        relocate = (input("Do you want to relocate the files? (Y/n): ").lower() or 'y') == "y"
        if (relocate):
            subdir_name = input("Enter directory name: ")
            subdir_path = os.path.join(root, subdir_name)
            print("Will move files to: " + subdir_path)

            cue_name = os.path.basename(cue_path)
            new_cue_path = os.path.join(subdir_path, cue_name)
            audio_path = result["AudioFilePath"]
            audio_name = os.path.basename(audio_path)
            new_audio_path = os.path.join(subdir_path, audio_name)

            print("Cue mv Target: " + new_cue_path)
            print("Audio mv Target: " + new_audio_path)

            confirm = input("Confirm? (Y/n): ").lower() == "y"
            if (not confirm):
                print("Aborting...")
                continue

            if (not os.path.exists(subdir_path)):
                os.mkdir(subdir_path)
            
            os.rename(cue_path, new_cue_path)
            os.rename(audio_path, new_audio_path)

            # calculate new root
            root = subdir_path

            # rerun split
            result = json.loads(CueSplit.SplitCue(root, new_cue_path))
            if (result["Invalid"]):
                print("Failed to parse cue file. Invalid (After relocate)")
                continue

        print("Parsed cue file successfully")
        print("Result structure:")
        print(json.dumps(result, indent=4, ensure_ascii=False))

        if (result["AudioFilePathGuessed"]):
            print('\n', "WARNING: Audio file path guessed", '\n')

        input("Press enter to continue...")

        print("Generating ffmpeg commands...")
        ffmpeg_cmds = []
        for track in result["Tracks"]:
            ffmpeg_cmds.append(mk_ffmpeg_cmd(track, result))

        print("Generated ffmpeg commands:")
        print(json.dumps(ffmpeg_cmds, indent=4, ensure_ascii=False))

        input("Press enter to start processing...")

        for tracks in result["Tracks"]:
            print("Processing track: " + tracks["TrackName"])
            cmd = mk_ffmpeg_cmd(tracks, result)
            proc = subprocess.Popen("ffmpeg " + " ".join(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True, encoding="utf-8")

            for line in proc.stdout:
                print(line, end='')

            proc.wait()

            print(f'CODE: {proc.returncode}\n\n')

            if (proc.returncode != 0):
                print("Failed to split track: " + tracks["TrackName"], "Return code: " + str(proc.returncode))
                continue

        failed = []
        for idx, track in enumerate(result["Tracks"]):
            print("Testing track: " + track["TrackName"])
            path = os.path.join(result["Root"], track["TrackName"])
            if (not os.path.exists(path)):
                print("Failed to split track: " + track["TrackName"])
                failed.append(idx)
                continue

            if (os.path.getsize(path) == 0):
                print("Failed to split track: " + track["TrackName"] + " (0 byte file)")
                failed.append(idx)
                continue

            print("OK\n")

        if (len(failed) == 0):
            print("All tracks split successfully")
            rm = (input("Do you want to remove the cue and flc file? (Y/n): ").lower() or 'y') == "y"
            if (rm):
                os.remove(result["CueFilePath"])
                audio_path = result["AudioFilePath"]
                if (result["AudioFilePathGuessed"]):
                    audio_path = result["AudioFilePathGuessed"]

                os.remove(audio_path)
                print("Removed cue and flc file")

        split_data.append(result)

        with open("split_data.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(split_data, indent=4, ensure_ascii=False))

        input("Press enter to continue...")

        os.system("cls" if os.name == "nt" else "clear")

if __name__ == "__main__":
    main()
