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
    out = os.path.join(info["Root"], track["TrackName"])
    if (not track["Duration"]):
        return f'-i "{info["AudioFilePath"]}" -ss {track["Begin"]} -movflags faststart "{out}" -y -stats -v quiet'

    return f'-i "{info["AudioFilePath"]}" -ss {track["Begin"]} -t {track["Duration"]} -movflags faststart "{out}" -y -stats -v quiet'

def generate_file_list(root, list_file):
    print("Generating file list...")
    output = {"processed": {}, "queued": {}, "failed": {}, "parse_fail": []}

    cue_to_parse = {}
    scan_failed = []
    count = 0
    for fp, dirs, files in os.walk(root):
        for file in files:
            if file.endswith(".cue"):
                cue_to_parse.update({ fp: os.path.join(fp, file) })
                count += 1
                print(f"Found {count} files", end="\r")

    if (count == 0):
        print("No cue files found at: " + root)
        input("Press any key to exit...")
        sys.exit(0)

    print("Parsing Found Cue Files")

    for root, cue_file in cue_to_parse.items():
        print(f"Parsing {cue_file}")
        
        out = CueSplit.SplitCue(root, cue_file)
        out = json.loads(out)

        if (out["Invalid"]):
            print(Fore.RED + f"Invalid Audio Path {cue_file}")
            output["parse_fail"].append(out)
            continue

        if (out["AudioFilePathGuessed"]):
            print(Fore.YELLOW + f"Guessed Audio File Path: {out['AudioFilePath']}")
        out["processed"] = False
        output["queued"].update({cue_file: out})

    output["parse_fail"] = scan_failed
    with open(list_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

def load_file_list(file_list):
    with open(file_list, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

print_logs = {}

def process_item(file_list, file: str, ffmpeg_path):
    cap_time = re.compile(r"time=(\d{2}:\d{2}:\d{2}.\d{2})")
    global print_logs
    try:
        ident = threading.get_ident()
        item = file_list["queued"][file]

        for idx, track in enumerate(item["Tracks"]):
            cmd = mk_ffmpeg_cmd(track, item)
            proc = subprocess.Popen(ffmpeg_path + " " + cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True, encoding="utf-8")

            for line in proc.stdout:
                progress_time = cap_time.search(line)
                print_logs[ident] = f"[{idx + 1}/{len(item['Tracks'])}] {file}"

            proc.wait()
            time.sleep(0.6)

        item["processed"] = True
        file_list["processed"].update({file: item})
        del file_list["queued"][file]
        # os.unlink(item["src"])
        # os.rename(item["dst"], item["src"])
    except Exception as e:
        print(Fore.RED + f"Failed to process {file}")
        traceback.print_exc()

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
        with ThreadPoolExecutor(max_workers=1) as executor:
            for file in list(loaded_list["queued"].keys()).copy():
                processes.append(executor.submit(process_item, loaded_list, file, ffmpeg_path))
                queued += 1
                print(f"Queued {queued} processes", end="\r")
            print("ABCD")
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
                    os.system("cls")
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
