import os
import json

worker_b_list = input("Enter worker B's worklist path: ")

with open(worker_b_list, "r", encoding="utf-8") as f:
    worker_b_data = json.load(f)

worker_a_list = input("Enter worker A's worklist path: ")

with open(worker_a_list, "r", encoding="utf-8") as f:
    worker_a_data = json.load(f)

master_list = input("Enter file list path: ")

with open(master_list, "r", encoding="utf-8") as f:
    master_data = json.load(f)


notfound = []
for key, entry in worker_b_data["queued"].items():
    if not os.path.isfile(entry["src"]):
        notfound.append(key)

print("Found {} missing files.".format(len(notfound)))

for key in notfound:
    del worker_b_data["queued"][key]

    entry_original = master_data["queued"][key]

    worker_a_data["queued"].update({key: entry_original})

    print("Moved (B->A) {}".format(key))

with open(worker_b_list, "w", encoding="utf-8") as f:
    json.dump(worker_b_data, f, indent=4, ensure_ascii=False)

with open(worker_a_list, "w", encoding="utf-8") as f:
    json.dump(worker_a_data, f, indent=4, ensure_ascii=False)

print("Done.")
