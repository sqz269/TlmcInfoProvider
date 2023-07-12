import os
import json
import shutil

def main():
    worker_b_path = input("Enter worker B path: ")
    filelist_path = input("Enter filelist path: ")

    with open(filelist_path, 'r', encoding="utf-8") as f:
        filelist = json.load(f)

    with open(worker_b_path, 'r', encoding="utf-8") as f:
        worker_b = json.load(f)

    worker_b_tlmc_root = input("Enter worker B root: ")
    original_tlmc_root = input("Enter original TLMC root: ")

    processed = worker_b['processed']

    for index, (key, entry) in enumerate(processed.items()):
        original = filelist["queued"][key]

        print("[{}] Testing: {}".format(index, original["src"]))
        
        if not os.path.exists(original["src"]):
            print("Original file not found: {}".format(original["src"]))
            input("Press enter to continue")
            continue

        # test master playlist from worker B exists
        if not os.path.exists(entry["master_playlist"]):
            print("Master playlist not found: {}".format(entry["master_playlist"]))
            input("Press enter to ABORT")
            exit(1)


    for key, entry in processed.items():
        original = filelist["queued"][key]
        
        # reconstruct the path to the hls root in the perspective of 
        # the original TLMC root
        base = os.path.dirname(entry["master_playlist"])
        hls_root = os.path.join(original_tlmc_root, base.replace(worker_b_tlmc_root, ""))
        
        input("Reconstruct path: {} (E2C)".format(hls_root))
        
        if not os.path.exists(hls_root):
            os.makedirs(hls_root)

        # copy the folder from worker B to the original TLMC root    
        shutil.copytree(base, hls_root)

        # delete the original flac file
        os.remove(original["src"])

        print("Processed: {}".format(original["src"]))

if __name__ == '__main__':
    main()
