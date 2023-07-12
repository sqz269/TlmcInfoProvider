import json

scan_path = "Stats/scan-secondary.json"

with open(scan_path, "r", encoding="utf-8") as f:
    scan = json.load(f)

if (__name__ == '__main__'):
    count = {}
    for dir, files in scan.items():
        for file in files:
            ext = file.split(".")[-1]
            count[ext.lower()] = count.get(ext.lower(), 0) + 1
            # if (ext.lower() == "zip"):
            #     print(dir, "/", file)


    print(count)

    # image_ext = { "jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "ico", "tif" }
    # count = {}
    # # count all file names (not extensions) that end with the extension in image_ext
    # for dir, files in scan.items():
    #     for file in files:
    #         ext = file.split(".")[-1]
    #         if (ext.lower() in image_ext):
    #             count[file] = count.get(file, 0) + 1

    # print(count)
    # filter out all files that only appear once
    # count = { file: c for file, c in count.items() if c > 1 }

    # # print them in order of most common to least common, 10 items at once then press enter to see the next 10
    # i = 0
    # for file, c in sorted(count.items(), key=lambda x: x[1], reverse=True):
    #     print(file, c)
    #     i += 1
    #     if (i >= 10):
    #         i = 0
    #         print()
    #         input()
