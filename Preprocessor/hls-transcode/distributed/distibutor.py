import os
import json
import random

RANDOM_DISTRIBUTION_RATIO = 0.7

WORKER_B_MAX_ACCUMULATED_SIZE = 751000000000


def main():
    filelist_fp = input("Enter filelist path: ")

    fp_root = os.path.dirname(filelist_fp)

    worker_a_list_fp = os.path.join(fp_root, "worker_a_list.json")
    worker_b_list_fp = os.path.join(fp_root, "worker_b_list.json")

    tlmc_root = input("Enter TLMC root: ")

    worker_a_mv_target = input(
        "Enter worker B's target path (Files working on will be mved here): "
    )
    print("Worker A will operate on default path")

    # distribute work
    with open(filelist_fp, "r", encoding="utf-8") as f:
        filelist = json.load(f)

    worker_a_lists = {"queued": {}, "processed": {}, "failed": {}}
    worker_b_lists = {"queued": {}, "processed": {}, "failed": {}}
    b_size_accumulated = 0
    exceed_hit_count = 0
    for key, entry in filelist["queued"].items():
        if RANDOM_DISTRIBUTION_RATIO > random.random():
            worker_a_lists["queued"].update({key: entry})
        else:
            b_size_accumulated += entry["size"]
            if b_size_accumulated > WORKER_B_MAX_ACCUMULATED_SIZE:
                exceed_hit_count += 1
                print(
                    "Worker B's accumulated size exceeded limit, distributing to worker A (Hit count: {})".format(
                        exceed_hit_count
                    ),
                    end="\r",
                )
                worker_a_lists["queued"].update({key: entry})
            worker_b_lists["queued"].update({key: entry})

    # rewrite src path using mv target and root
    for key, entry in worker_b_lists["queued"].items():
        if os.path.commonprefix([entry["src"], tlmc_root]) != tlmc_root:
            raise Exception("TLMC ROOT IS NOT A PREFIX OF ENTRY'S SRC PATH")
        else:
            entry["src"] = os.path.join(
                worker_a_mv_target, os.path.relpath(entry["src"], tlmc_root)
            )
            worker_b_lists["queued"][key] = entry

    # write to file
    with open(worker_a_list_fp, "w", encoding="utf-8") as f:
        json.dump(worker_a_lists, f, indent=4, ensure_ascii=False)
    with open(worker_b_list_fp, "w", encoding="utf-8") as f:
        json.dump(worker_b_lists, f, indent=4, ensure_ascii=False)

    print(
        f"Worker A received {len(worker_a_lists['queued'])} files (Ratio: {len(worker_a_lists['queued']) / len(filelist['queued'])})"
    )
    print(
        f"Worker B received {len(worker_b_lists['queued'])} files (Ratio: {len(worker_b_lists['queued']) / len(filelist['queued'])})"
    )


if __name__ == "__main__":
    main()
