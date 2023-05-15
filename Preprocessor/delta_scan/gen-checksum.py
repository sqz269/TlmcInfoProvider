import xxhash
import json
import os

tlmc_root = input("Enter the path to the root of the TLMC: ")
tlmc_ver = input("Enter the version of the TLMC: ")

# Generate checksums for all files in the TLMC directory
checksums = {}

print("Generating checksums...")
i = 0
for root, dirs, files in os.walk(tlmc_root):
    for file in files:
        path = os.path.join(root, file)
        with open(path, 'rb') as f:
            print(f"Generating hash {i}", end='\r')
            checksums[path.replace(tlmc_root, "")] = {
                "xx3_64": xxhash.xxh3_64_hexdigest(f.read()),
                "size": os.path.getsize(path)
            }
        i += 1

# Write checksums to file
with open(os.path.join(tlmc_root, f"checksums_{tlmc_ver}.json"), 'w') as f:
    json.dump(checksums, f, indent=4, ensure_ascii=False, sort_keys=True)
