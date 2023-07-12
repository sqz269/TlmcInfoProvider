import os
import json
import shutil

def main():
    worker_b_worklist = input("Enter worker B's worklist path: ")
    with open(worker_b_worklist, "r", encoding="utf-8") as f:
        data = json.load(f)

    for index, (key, entry) in enumerate(data["queued"].items()):
        # key is our original file path
        # src is where we want to copy the file from

        # we want to copy the file from the original path
        # to the new path

        if (os.path.isfile(key)):
            dirname = os.path.dirname(entry["src"])
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            shutil.copyfile(key, entry["src"])
            print("[{}] Copied file: {}".format(index, key))
        else:
            print("File not found: {}".format(key))
            continue

if __name__=="__main__":
    main()
