import json
import re

combo_map_json = r"InfoProviders\BasicInfoProvider\artist_info\artist_combo_map.json"
data_json = r"InfoProviders\BasicInfoProvider\data.json"

with open(combo_map_json, "r", encoding="utf-8") as file:
    combo_map = json.load(file)

with open(data_json, "r", encoding="utf-8") as file:
    data = json.load(file)

artist = list(data.keys())

artist_ext_regex = re.compile(r'\[(.+)\]')

artist_actual = {}

for i in artist:
    if (i in combo_map):
        for j in combo_map[i]:
            artist_actual[j] = artist_actual.get(j, 0) + 1
        continue

    artist = artist_ext_regex.search(i)
    if (artist):
        artist = artist.group(1)
        artist_actual[artist] = artist_actual.get(artist, 0) + 1
        continue

def max_common_prefix(str1, str2):
    i = 0
    str1 = str1.lower()
    str2 = str2.lower()
    while (i < len(str1) and i < len(str2) and str1[i] == str2[i]):
        i += 1
    return i

kv_sorted = sorted(artist_actual.items(), key=lambda x: x[0].lower(), reverse=True)

csv_line = "Artist,Count,Max Common Prefix\n"
prev = ""
for k, v in kv_sorted:
    csv_line += f"{k.replace(',', '，')},{v},{max_common_prefix(k, prev)}\n"
    prev = k

with open(r"InfoProviders\BasicInfoProvider\artist_info\artist_count.csv", "w", encoding="utf-8") as file:
    file.write(csv_line)

# As／Hi Soundworks (As／Hi)
# VAGUEDGE (VAGUEDGE DIES FOR DIES IRAE)
# "Star Servant＊" aka "Orpheus＊" but not "orpheus" (Without *)
# Check Liz Triangle (Lower T)
# Check FALSE&TRUES (All Caps)
# "KRASTERII" aka "Kraster"

# Artist mixed with Circle: CUBETYPE feat. AVSS
