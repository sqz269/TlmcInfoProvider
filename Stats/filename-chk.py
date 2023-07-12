import json

data = json.loads(open("Stats\scan-secondary.json", "r", encoding="utf-8").read())

for dir, files in data.items():
    for file in files:
        if ("'" in file):
            print("Found single quote in: " + file)
