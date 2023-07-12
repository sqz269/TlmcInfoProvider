import os
import re
import subprocess
import sys
import shlex
import json
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import threading
import time

# Coefficient to Estimates the size of the transcoded file
# When using VBR 3 parameter for transcoding from FLAC to AAC
# On average the file size is 1/8 of the original file size
# and the bitrate usually goes down to 128kbps
# This coefficient need to be adjusted if the transcoding parameters are changed
# Currently valid for -c:a aac -vbr 3
EST_SIZE_COEFF = 0.125

FILELIST_NAME = "transcode_fl.json"
ERRORS = "error.json"
print_logs = {}
filelist = {}

dry_run = False
cmd_exec = []

def mk_ffmpeg_cmd(path, out_path, use_libfdk_aac):
    # ffmpeg -i 'ShibayanRecords - Solar.flac' -c:a libfdk_aac -vbr 3 output.ts  -y -v quiet -stats
    lib = "libfdk_aac" if use_libfdk_aac else "aac"
    path = shlex.quote(path)
    out_path = shlex.quote(out_path)
    # return ["-i", f"{path}", "-map", "0:a", "-map", "0:v?", "-c:a", lib, "-vbr", "3", "-c:v", "copy", f"{out_path}", "-y"]
    return ["-i", f"{path}", ]

def calc_total_size(path_list):
    sz = 0
    for path, metadata in path_list.items():
        # Convert bytes to GB
        sz += metadata["size"] / 1024 / 1024 / 1024
    return sz

def process_one(filelist, key, ffmpeg_path, use_libfdk_aac):
    cap_time = re.compile(r"time=(\d{2}:\d{2}:\d{2}.\d{2})")
    cap_spd = re.compile(r"speed=\s{0,}(\d+\.?\d{0,})x")
    fn = os.path.basename(key)
    global print_logs
    try:
        ident = threading.get_ident()
        item = filelist["queued"][key]
        if (dry_run):
            dst = "/dev/null"
        else:
            dst = item["dst"]
        cmd = mk_ffmpeg_cmd(item["src"], dst, use_libfdk_aac)
        cmd.insert(0, ffmpeg_path)
        proc = subprocess.Popen(" ".join(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True, encoding="utf-8")

        for line in proc.stdout:
            progress_time = cap_time.search(line)
            progress_speed = cap_spd.search(line)
            time_str = progress_time.group(1) if progress_time else "XX:XX:XX.XX"
            spd_str = f" {progress_speed.group(1)}x" if progress_speed else "XX.x"
            stats_pad = f"[{time_str} ({spd_str})]".ljust(25)
            print_logs[ident] = f"{stats_pad} {fn}"

        # for line in proc.stderr:
        #     print_logs[ident] = f"\n\n[ERROR] {line}\n\n"

        proc.wait()
        if (proc.returncode != 0):
            raise Exception(f"ffmpeg exited with code {proc.returncode}. CMD: {' '.join(cmd)}")

        if (not os.path.isfile(dst) or os.path.getsize(dst) < 1):
            raise Exception(f"Result file is empty. CMD: {' '.join(cmd)}, CODE: {proc.returncode}")

        stats_pad = "[DONE]".ljust(25)
        print_logs[ident] = f"{stats_pad} {fn}"
        if (dry_run):
            return
        os.unlink(item["src"])
        time.sleep(0.6)
        item["processed"] = True
        filelist["processed"].update({key: item})
        del filelist["queued"][key]

        # os.rename(item["out"], item["src"])
    except Exception as e:
        # if user interrupted running (SIGINT to ffmpeg subprocess), their fault
        # don't interrupt
        if isinstance(e, KeyboardInterrupt) or "exited with code -2" in str(e.args[0]):
            print("\n\n---------INTERRUPT DATA MAY BE LOST----------\n\n")
            raise e

        while True:
            try:
                with open(ERRORS, "a", encoding="utf-8") as f:
                    f.write(f"{key}: {str(e)} | CMD: {' '.join(cmd)}\n")
                break
            except Exception as e:
                time.sleep(0.1)

        filelist["failed"].update({key: item})
        item["error"] = str(e)
        del filelist["queued"][key]

def generate_file_list(root, file_list_path):
    filelist = {"processed": {}, "failed": {}, "queued": {}}
    print("Generating file list...")
    for root, dirs, files in os.walk(root):
        for file in files:
            if file.endswith(".flac"):
                path = os.path.join(root, file)

                out_name = os.path.basename(path).replace(".flac", ".m4a")
                out_path = os.path.join(root, out_name)
                filelist["queued"].update({path: {
                    "src": path,
                    "dst": out_path,
                    "size": os.path.getsize(path),
                    "processed": False,
                    "error": None
                }})
    print(f"Found {len(filelist['queued'])} files")
    with open(file_list_path, "w", encoding="utf-8") as f:
        json.dump(filelist, f, indent=4, ensure_ascii=False)

def load_file_list(file_list_path):
    with open(file_list_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    global filelist
    global dry_run
    global print_logs
    global FILELIST_NAME

    ffmpeg_path = input("Enter path to ffmpeg: ") or "ffmpeg"
    file_list_path = input("Enter path to file list: ")
    FILELIST_NAME = file_list_path
    libfdk_aac_enable = (input("Use libfdk_aac? [Y/n]: ") or "y").lower() == "y"

    if (not os.path.isfile(file_list_path)):
        root = input("Enter path to TLMC root: ")
        generate_file_list(root, file_list_path)
        
    filelist = load_file_list(file_list_path)

    is_dry = input("Dry run? [y/N]: ")
    if (is_dry.lower() == "y"):
        dry_run = True
        print_logs["DRY"] = "TRUE"

    queued = 0
    processes = []
    print("Starting transcoding...")
    try:
        with ThreadPoolExecutor(max_workers=os.cpu_count() // 2) as executor:
            for file in list(filelist["queued"].keys()).copy():
                queued += 1
                processes.append(executor.submit(process_one, filelist, file, ffmpeg_path, use_libfdk_aac=libfdk_aac_enable))
                print(f"Queued {queued} files")

            time.sleep(1)
            try:
                key = print_logs.keys()
                while any([p.running() for p in processes]):
                    if (print_logs.keys() != key):
                        key = print_logs.keys()

                    print("PROGRESS [{}/{} | {}]".format(len(filelist["processed"]) , len(filelist["queued"]) + len(filelist["processed"]), len(filelist["failed"])))
                    for ident in key:
                        print(print_logs[ident], end="\n")

                    wait(processes, timeout=0.5, return_when=ALL_COMPLETED)

                    os.system("cls" if os.name == "nt" else "clear")
            except Exception as e:
                print("Error:", e)
                if (isinstance(e, KeyboardInterrupt)):
                    print("Interrupted by user.")
                    executor.shutdown(wait=False)
                with open(file_list_path, "w", encoding="utf-8") as f:
                    json.dump(filelist, f, indent=4, ensure_ascii=False)
        
        print("Done!")
        with open(file_list_path, "w", encoding="utf-8") as f:
            json.dump(filelist, f, indent=4, ensure_ascii=False)

    except Exception as e:
        print("Error:", e)
        if (isinstance(e, KeyboardInterrupt)):
            print("Interrupted by user.")
            executor.shutdown(wait=False)
        with open(file_list_path, "w", encoding="utf-8") as f:
            json.dump(filelist, f, indent=4, ensure_ascii=False)

def global_exc_hook(exctype, value, traceback):
    with open(FILELIST_NAME, "w", encoding="utf-8") as f:
        json.dump(filelist, f, indent=4, ensure_ascii=False)

    if exctype == KeyboardInterrupt:
        sys.__excepthook__(exctype, value, traceback)
        return

    print("Error:", exctype, value)
    sys.exit(1)

sys.excepthook = global_exc_hook

if __name__ == "__main__":
    main()
