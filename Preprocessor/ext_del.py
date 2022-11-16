import sys
import os
import subprocess

err_log = open("/home/sqz269/err_log.log", "a", encoding="utf-8");

for fp, dirs, files in os.walk("."):
    files = [f for f in files if f.endswith(".rar")]
    input("Found {} files. Press Enter to continue...".format(len(files)))
    total = len(files)
    for idx, file in enumerate(files):
        try:
            # cp = os.path.join(fp, file)
            print(f"[{idx + 1}/{total}] Extracting: {file}")
            cmd = f"7z x {file}"
            result = subprocess.run(["7z", "x", file])
            if (result.returncode != 0):
                err_log.write(f"7Z CMD ERROR [{file}] RETURNED FAILURE STATUS {result.returncode}\n")
                err_log.flush()
                continue
            print(f"Deleting: {file}")
            os.unlink(os.path.join(fp, file))
        except Exception as e:
            err_log.write(f"ERROR [{file}] {str(e)}\n")
            err_log.flush()

err_log.close()