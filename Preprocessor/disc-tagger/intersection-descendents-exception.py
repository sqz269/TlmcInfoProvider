import json
from pprint import pprint

descendents = json.load(open(r"Preprocessor/disc-tagger/dir_descendants.json", "r", encoding="utf-8"))
exceptions = set(json.load(open(r"Preprocessor/disc-tagger/disc-exception-nc.json", "r", encoding="utf-8")))

abc = open(r"Preprocessor/disc-tagger/f.txt", "r", encoding="utf-8").read()

found = []
not_found = []
for i in exceptions:
    if (i in abc):
        found.append(i)
    else:
        not_found.append(i)

print("Found: ")
pprint(found)

print("Not found: ")
pprint(not_found)
