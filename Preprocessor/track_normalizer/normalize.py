import re
import os
import sys
import json
import time
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

from typing import Dict

NORM_EXT = (
    ".mp4",
    ".mkv",
    ".mp3",
    ".m4a",
    ".flac",
    ".wav",
    ".ogg"
)

def mk_ffmpeg_cmd(src, dst) -> str:
    return f' -i "{src}" -af loudnorm -movflags faststart "{dst}" -y -v quiet -stats'

def mk_out_filename(orgname):
    return "audio.norm." + orgname

def generate_filelist(root, list_file): 
    output = {"processed": {}, "queued": {}, "failed": {}}

    count = 0
    for fp, dirs, files in os.walk(root):
        for file in files:
            if file.endswith(tuple(NORM_EXT)):
                output["queued"].update({ os.path.join(fp, file): {
                    "src": os.path.join(fp, file),
                    "dst": os.path.join(fp, mk_out_filename(file)),
                    "processed": False,
                    "error": None
                } })
                count += 1
                print(f"Found {count} files", end="\r")

    with open(list_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

def load_filelist(file_list):
    with open(file_list, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

print_logs = {}

def process_file(file_list, file: str, ffmpeg_path):
    cap_time = re.compile(r"time=(\d{2}:\d{2}:\d{2}.\d{2})")
    global print_logs
    try:
        ident = threading.get_ident()
        item = file_list["queued"][file]
        cmd = mk_ffmpeg_cmd(item["src"], item["dst"])
        proc = subprocess.Popen(ffmpeg_path + cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

        for line in proc.stdout:
            progress_time = cap_time.search(line)
            print_logs[ident] = f"[{progress_time.group(1) if progress_time else 'NO_INFO'}] {file}"

        proc.wait()
        print_logs[ident] = f"[DONE] {file}"
        time.sleep(0.6)
        item["processed"] = True
        file_list["processed"].update({file: item})
        del file_list["queued"][file]
        os.unlink(item["src"])
        os.rename(item["dst"], item["src"])
    except Exception as e:
        file_list["failed"].update({file: item})
        item["error"] = str(e)
        del file_list["queued"][file]

if (__name__ == '__main__'):
    ffmpeg_path = input("Enter path to ffmpeg: ") or "ffmpeg"
    file_list = input("Enter path to file list: ")
    if (not os.path.exists(file_list)):
        file_root = input("Enter path to file root: ")
        if (os.path.isdir(file_root) == False):
            print("Invalid path to file root.")
            sys.exit(1)
        generate_filelist(file_root, file_list)

    loaded_list = load_filelist(file_list)

    def global_exc_hook(exctype, value, traceback):
        with open(file_list, "w", encoding="utf-8") as f:
            json.dump(loaded_list, f, indent=4, ensure_ascii=False)
        if exctype == KeyboardInterrupt:
            print("KeyboardInterrupt")
            sys.exit(0)
        else:
            sys.__excepthook__(exctype, value, traceback)

    sys.excepthook = global_exc_hook

    queued = 0
    processes = []
    try:
        with ThreadPoolExecutor(max_workers=os.cpu_count() // 2) as executor:
            for file in list(loaded_list["queued"].keys()).copy():
                queued += 1
                processes.append(executor.submit(process_file, loaded_list, file, ffmpeg_path))

            try:
                key = print_logs.keys()
                while any([p.running() for p in processes]):
                    if (print_logs.keys() != key):
                        key = print_logs.keys()

                    print("PROGRESS [{}/{} | {}]".format(len(loaded_list["processed"]) , len(loaded_list["queued"]) + len(loaded_list["processed"]), len(loaded_list["failed"])))
                    for ident in key:
                        print(print_logs[ident], end="\n")

                    print("\n\n")
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
