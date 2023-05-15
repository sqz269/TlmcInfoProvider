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

MANUAL_EXCLUDE = [
    "2015.12.30 [MKAC-1502] 記憶 [C89]",
    "2017.12.29 Counsel of three Sessions [C93]"
]

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
    if (not track["Duration"]):
        return f'-i \'{audio_path}\' -ss {track["Begin"]} -movflags faststart \'{out}\' -y -stats -v quiet'

    return f'-i \'{audio_path}\' -ss {track["Begin"]} -t {track["Duration"]} -movflags faststart \'{out}\' -y -stats -v quiet'

def generate_file_list(root, list_file):
    print("Generating file list...")
    output = {"processed": {}, "queued": {}, "failed": {}, "parse_fail": [], "ignore": []}
    
    TRACK_INFO_EXTRACTOR = re.compile(r'(?:\((\d+)\) )?(?:\[(.+)\] )?(.+)(?:(?:.mp3)|(?:.flac))')

    cue_to_parse = {}
    count = 0
    skipped = 0
    for fp, dirs, files in os.walk(root):
        skip = False
        for exclude in MANUAL_EXCLUDE:
            if (exclude in fp):
                print(f"Skipping {fp} due to manual exclude")
                # input()
                skipped += 1
                skip = True
        if (skip):
            continue

        to_add = None
        individual_flac = []
        for file in files:
            m = TRACK_INFO_EXTRACTOR.match(file)
            if (m != None and m.group(1) and os.path.getsize(os.path.join(fp, file)) > 0):
                individual_flac.append(file)
            if file.endswith(".cue"):
                to_add = { fp: os.path.join(fp, file) }

        if (not individual_flac and to_add):
            cue_to_parse.update(to_add)
            count += 1
            print(f"Found {count} files", end="\r")
        elif (to_add):
            skipped += 1
            individual_flac.append(to_add[list(to_add.keys())[0]])
            output["ignore"].append({fp: individual_flac})

    if (count == 0):
        print("No cue files found at: " + root)
        input("Press any key to exit...")
        sys.exit(0)

    print("Parsing Found Cue Files")

    direct = 0
    guessed = 0
    failed = 0
    for root, cue_file in cue_to_parse.items():
        print(f"Parsing {cue_file}")
        
        out = CueSplit.SplitCue(root, cue_file)
        out = json.loads(out)

        if (out["Invalid"]):
            failed += 1
            print(Fore.RED + f"Invalid Audio Path {cue_file}")
            output["parse_fail"].append(out)
            continue

        if (out["AudioFilePathGuessed"]):
            guessed += 1
            print(Fore.YELLOW + f"Guessed Audio File Path: {out['AudioFilePath']}")
        else:
            direct += 1
        out["processed"] = False
        output["queued"].update({cue_file: out})

    print(f"Found {direct + guessed + failed} audio paths, {guessed} guessed paths, {failed} failed paths, {skipped} ignored")

    with open(list_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

def load_file_list(file_list):
    with open(file_list, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

print_logs = {}
cmd_exec = []
"""
cmd_exec type
{
    "cmd": "<FFMPEG CMD>",
    "file": "<FILE NAME>",
    "status": "<STATUS>",
    "begin": "<BEGIN TIME>",
    "end": "<END TIME>"
}
"""

def process_item(file_list, file: str, ffmpeg_path, retry_failed=False):
    k = "queued"
    if (retry_failed):
        k = "failed"

    cap_time = re.compile(r"time=(\d{2}:\d{2}:\d{2}.\d{2})")
    global print_logs
    try:
        ident = threading.get_ident()
        item = file_list[k][file]

        # PROBE EACH OUTPUT FILE TO SEE IF IT EXISTS AND IS COMPLETE AFTER PROCESSING
        for idx, track in enumerate(item["Tracks"]):
            command_telementry = {

            }
            cmd = mk_ffmpeg_cmd(track, item)

            command_telementry["cmd"] = cmd

            st = time.time()
            command_telementry["begin"] = st

            proc = subprocess.Popen(ffmpeg_path + " " + cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True, encoding="utf-8")
            cmd_exec.append(command_telementry)

            for line in proc.stdout:
                progress_time = cap_time.search(line)
                print_logs[ident] = f"[{idx + 1}/{len(item['Tracks'])}] {file}"

            proc.wait()
            et = time.time()
            ec = proc.returncode

            command_telementry["file"] = track["TrackName"]
            command_telementry["status"] = ec
            command_telementry["end"] = et

            time.sleep(0.6)

        for idx, track, in enumerate(item["Tracks"]):
            # Perform a final check to make sure the file exists and is not empty
            out = os.path.join(item["Root"], track["TrackName"])
            if (not os.path.exists(out)):
                raise Exception(f"Track {track} does not exist after processing")

            if (os.path.getsize(out) == 0):
                raise Exception(f"Track {track} is empty after processing")

        item["processed"] = True
        file_list["processed"].update({file: item})
        del file_list[k][file]

        audio_track = item["AudioFilePath"] if not item["AudioFilePathGuessed"] else item["AudioFilePathGuessed"]

        os.unlink(item["CueFilePath"])
        os.unlink(audio_track)
    except Exception as e:
        print(Fore.RED + f"Failed to process {file}")
        traceback.print_exc()
        if (retry_failed):
            return

        file_list["failed"].update({file: item})
        item["error"] = str(e)
        del file_list["queued"][file]

if (__name__ == '__main__'):
    ffmpeg_path = input("Enter path to ffmpeg: ") or "ffmpeg"
    file_list = input("Enter path to file list: ")

    if not os.path.exists(file_list):
        root = input("Enter path to root folder: ")
        generate_file_list(root, file_list)
        
        if not os.path.exists(file_list):
            print("File list not found")
            exit(1)

    loaded_list = load_file_list(file_list)

    def global_exc_hook(exctype, value, traceback):
        with open(file_list, "w", encoding="utf-8") as f:
            json.dump(loaded_list, f, indent=4, ensure_ascii=False)
        if exctype == KeyboardInterrupt:
            print("KeyboardInterrupt")
            sys.exit(0)
        else:
            sys.__excepthook__(exctype, value, traceback)

    sys.excepthook = global_exc_hook

    print("Scan Complete")
    input("Press any key to start processing...")

    queued = 0
    processes = []
    try:
        with ThreadPoolExecutor(max_workers=os.cpu_count() / 2) as executor:
            process_list = None
            retry_failed = False
            if (len(loaded_list["queued"]) != 0):
                process_list = list(loaded_list["queued"].keys())
            elif (len(loaded_list["failed"]) != 0):
                print("Retrying failed processes")
                process_list = list(loaded_list["failed"].keys())
                retry_failed = True
            else:
                print("Nothing to process")
                exit(0)

            input("Press enter to continue...")

            for file in process_list:
                processes.append(executor.submit(process_item, loaded_list, file, ffmpeg_path, retry_failed))
                queued += 1
                print(f"Queued {queued} processes", end="\r")

            time.sleep(1)
            try:
                key = print_logs.keys()
                while any([p.running() for p in processes]):
                    if (key != print_logs.keys()):
                        key = print_logs.keys()
                    
                    print("PROGRESS [{}/{} | {}]".format(len(loaded_list["processed"]) , len(loaded_list["queued"]) + len(loaded_list["processed"]), len(loaded_list["failed"])))
                    for ident in key:
                        print(print_logs[ident], end="\n")

                    # print("\n\n")
                    wait(processes, timeout=0.5, return_when=ALL_COMPLETED)
                    os.system("cls" if os.name == "nt" else "clear")
            except Exception as e:
                if (isinstance(e, KeyboardInterrupt)):
                    print("Interrupted by user.")
                    executor.shutdown(wait=False)
                with open(file_list, "w", encoding="utf-8") as f:
                    json.dump(loaded_list, f, indent=4, ensure_ascii=False)

    except Exception as e:
        if (isinstance(e, KeyboardInterrupt)):
            print("Interrupted by user.")
            executor.shutdown(wait=False)
        with open(file_list, "w", encoding="utf-8") as f:
            json.dump(loaded_list, f, indent=4, ensure_ascii=False)

    finally:
        with open(file_list, "w", encoding="utf-8") as f:
            json.dump(loaded_list, f, indent=4, ensure_ascii=False)
        
        with open("ffmpeg_exec.txt", "w", encoding="utf-8") as f:
            f.write(json.dumps(cmd_exec, indent=4, ensure_ascii=False))
