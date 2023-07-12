import os
import json

disc_numbered = json.load(open(r'Preprocessor/disc-tagger/disc_numbered.json', 'r', encoding='utf-8'))

for i in disc_numbered:
    key = list(i.keys())[0]
    
    if (os.path.isdir(key) == False):
        print("NOT DIR")
        print(key, '\n')
        continue

    files = os.listdir(key)
    for file in files:
        if (file.lower().endswith('.flac')):
            print(key)
            break
