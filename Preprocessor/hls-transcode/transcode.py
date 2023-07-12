import os
import re
import subprocess
import argparse
import sys
import shlex
import mslex
import json
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import threading
import time

BITRATES = ["128k", "192k", "320k"]

FILELIST_NAME = "transcode_fl.json"
ERRORS = "error.json"
print_logs = {}
filelist = {}

dry_run = False
cmd_exec = []


def oslex_quote(path):
    if os.name == "nt":
        return mslex.quote(path)
    return shlex.quote(path)


def mk_ffmpeg_tc_cmd(src, root, bitrate):
    src = oslex_quote(src)
    seg_path = oslex_quote(os.path.join(root, "segment_%03d.m4s"))
    dst = oslex_quote(os.path.join(root, "playlist.m3u8"))
    return f"ffmpeg -i {src} -vn -b:a {bitrate} -f hls -hls_time 10 -hls_list_size 0 -hls_fmp4_init_filename init.mp4 -hls_segment_filename {seg_path} -hls_segment_type fmp4 -c:a aac {dst} -y -v quiet -stats"


def mk_ffmpeg_norm_cmd(path, out_path):
    path = oslex_quote(path)
    out_path = oslex_quote(out_path)
    return f"ffmpeg -i {path} -af loudnorm {out_path} -y -v quiet -stats"


def mk_master_playlist(bitrate_list):
    playlist = "#EXTM3U\n"
    for bitrate in bitrate_list:
        playlist += (
            f'#EXT-X-STREAM-INF:BANDWIDTH={bitrate},AUDIO="audio",CODECS="mp4a.40.2"\n'
        )
        playlist += f"hls/{bitrate}/playlist.m3u8\n"
    return playlist


def mk_output_dir_path(target):
    target_dir = os.path.dirname(target)
    target_name = os.path.basename(target)
    target_name = target_name[: target_name.rfind(".")]

    track_dir = os.path.join(target_dir, target_name)

    return track_dir


def execute_cmd_and_report_ffmpeg(cmd: str, cwd, filename, report_prefix):
    global print_logs
    ident = threading.get_ident()

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        shell=True,
        encoding="utf-8",
        cwd=cwd,
    )

    cap_time = re.compile(r"time=(\d{2}:\d{2}:\d{2}.\d{2})")
    cap_spd = re.compile(r"speed=\s{0,}(\d+\.?\d{0,})x")
    for line in proc.stdout:
        progress_time = cap_time.search(line)
        progress_speed = cap_spd.search(line)
        time_str = progress_time.group(1) if progress_time else "XX:XX:XX.XX"
        spd_str = f" {progress_speed.group(1)}x" if progress_speed else "XX"
        stats_pad = f"[{time_str} ({spd_str})]".ljust(25)
        if report_prefix:
            print_logs[ident] = f"{stats_pad}"
        print_logs[ident] = f"{stats_pad} {report_prefix} {filename}"

    proc.wait()
    return proc.returncode


def process_one(filelist, key):
    global print_logs
    try:
        ident = threading.get_ident()

        item = filelist["queued"][key]

        src_path = item["src"]
        src_filename = os.path.basename(src_path)
        src_root = os.path.dirname(src_path)
        """
        Steps:
            1. Create output directory (dirname of target + filename without ext)
            2. Normalize file, output to output directory with same filename
            3. # DIRECTORY CHANGE: All following commands will be executed in the output directory
            4. Transcode file, output to output directory + hls bitrate directory
            5. Move init.mp4 to the specific hls bitrate directory
            6. Create master playlist, output to output directory
        """
        # 1. Create output directory
        outdir = mk_output_dir_path(src_path)
        os.makedirs(outdir, exist_ok=True)

        # 2. Normalize file
        norm_dst = os.path.join(outdir, src_filename)
        norm_cmd = mk_ffmpeg_norm_cmd(src_path, norm_dst)
        retcode = execute_cmd_and_report_ffmpeg(
            norm_cmd, src_root, src_filename, "[NORM]"
        )

        if retcode != 0:
            raise Exception(
                f"Failed to normalize. FFMPEG return code: {retcode}, CMD: {norm_cmd}"
            )

        if not os.path.isfile(norm_dst) or os.path.getsize(norm_dst) < 1:
            raise Exception(f"Result file is empty. CMD: {norm_cmd}, CODE: {retcode}")

        for bitrate in BITRATES:
            "./hls/128k"
            bitrate_root = os.path.join(outdir, "hls", bitrate)

            "./hls/128k/playlist.m3u8"
            playlist = os.path.join(bitrate_root, "playlist.m3u8")
            init = os.path.join(bitrate_root, "init.mp4")
            os.makedirs(bitrate_root, exist_ok=True)

            # 4. Transcode file
            tc_cmd = mk_ffmpeg_tc_cmd(norm_dst, bitrate_root, bitrate)
            retcode = execute_cmd_and_report_ffmpeg(
                tc_cmd, outdir, src_filename, f"[{bitrate}]"
            )

            if retcode != 0:
                raise Exception(
                    f"Failed to transcode. FFMPEG return code: {retcode} CMD: {tc_cmd}"
                )

            if not os.path.isfile(playlist) or os.path.getsize(playlist) < 1:
                raise Exception(f"Result file is empty. CMD: {tc_cmd}, CODE: {retcode}")

            # 5. Move init.mp4 to the specific hls bitrate directory
            # if the ffmpeg command did not generate init in the bitrate_root already (behavior in older ffmpeg version)
            if not os.path.isfile(os.path.join(outdir, "init.mp4")) and (
                os.path.isfile(os.path.join(bitrate_root, "init.mp4"))
            ):
                pass
            else:
                os.replace(os.path.join(outdir, "init.mp4"), init)

        # 6. Create master playlist
        master_playlist = mk_master_playlist(BITRATES)
        with open(os.path.join(outdir, "playlist.m3u8"), "w", encoding="utf-8") as f:
            f.write(master_playlist)

        stats_pad = "[DONE]".ljust(25)
        print_logs[ident] = f"{stats_pad} {src_filename}"

        item["master_playlist"] = os.path.join(outdir, "playlist.m3u8")
        filelist["processed"].update({key: item})
        item["processed"] = True
        del filelist["queued"][key]

        os.remove(norm_dst)
        os.remove(src_path)

    except Exception as e:
        # if user interrupted running (SIGINT to ffmpeg subprocess), their fault
        # don't interrupt
        if isinstance(e, KeyboardInterrupt) or "exited with code -2" in str(e.args[0]):
            print("\n\n---------INTERRUPT DATA MAY BE LOST----------\n\n")
            raise e
        while True:
            try:
                with open(ERRORS, "a", encoding="utf-8") as f:
                    f.write(f"{key}: {str(e)}\n")
                break
            except Exception as e:
                time.sleep(0.1)

        filelist["failed"].update({key: item})
        item["error"] = str(e)
        del filelist["queued"][key]


def load_file_list(file_list_path):
    with open(file_list_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_file_list(root, file_list_path):
    filelist = {"processed": {}, "failed": {}, "queued": {}}
    print("Generating file list...")
    for root, dirs, files in os.walk(root):
        for file in files:
            if file.endswith(".flac"):
                path = os.path.join(root, file)

                out_name = os.path.basename(path).replace(".flac", ".m4a")
                out_path = os.path.join(root, out_name)
                filelist["queued"].update(
                    {
                        path: {
                            "src": path,
                            "dst": out_path,
                            "size": os.path.getsize(path),
                            "processed": False,
                            "error": None,
                        }
                    }
                )
    print(f"Found {len(filelist['queued'])} files")
    with open(file_list_path, "w", encoding="utf-8") as f:
        json.dump(filelist, f, indent=4, ensure_ascii=False)


def main():
    global filelist
    global dry_run
    global print_logs
    global FILELIST_NAME

    file_list_path = input(
        "Enter path to file list (Generated by reverse-list-gen.py): "
    )
    FILELIST_NAME = file_list_path
    filelist = load_file_list(file_list_path)

    queued = 0
    processes = []
    print("Starting transcoding...")
    try:
        with ThreadPoolExecutor(max_workers=os.cpu_count() // 2) as executor:
            for file in list(filelist["queued"].keys()).copy():
                queued += 1
                processes.append(executor.submit(process_one, filelist, file))
                print(f"Queued {queued} files", end="\r")

            time.sleep(1)
            try:
                key = print_logs.keys()
                while any([p.running() for p in processes]):
                    if print_logs.keys() != key:
                        key = print_logs.keys()

                    print(
                        "PROGRESS [{}/{} | {}]".format(
                            len(filelist["processed"]),
                            len(filelist["queued"]) + len(filelist["processed"]),
                            len(filelist["failed"]),
                        )
                    )
                    for ident in key:
                        print(print_logs[ident], end="\n")

                    wait(processes, timeout=0.5, return_when=ALL_COMPLETED)

                    os.system("cls" if os.name == "nt" else "clear")
            except Exception as e:
                print("Error:", e)
                if isinstance(e, KeyboardInterrupt):
                    print("Interrupted by user.")
                    executor.shutdown(wait=False)
                with open(file_list_path, "w", encoding="utf-8") as f:
                    json.dump(filelist, f, indent=4, ensure_ascii=False)

        print("Done!")
        with open(file_list_path, "w", encoding="utf-8") as f:
            json.dump(filelist, f, indent=4, ensure_ascii=False)

    except Exception as e:
        print("Error:", e)
        if isinstance(e, KeyboardInterrupt):
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
    # generator args
    # if ran with -g flag, generate file list, then exit, else, start transcoding
    parser = argparse.ArgumentParser(
        description="Generate ffmpeg command for transcoding"
    )
    parser.add_argument(
        "-g", "--generate", help="Generate file list, then exit", action="store_true"
    )

    args = parser.parse_args()

    if args.generate:
        root = input("Enter path to root directory: ")
        file_list_path = input("Enter path to file list: ")
        generate_file_list(root, file_list_path)
        sys.exit(0)

    main()
