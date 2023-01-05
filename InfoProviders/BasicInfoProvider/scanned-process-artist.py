import json
import re
from pprint import pprint
from uuid import uuid4
from typing import Any, Dict, List
import unicodedata
from InfoProviders.BasicInfoProvider.Model.BasicInfoModel import BasicCircle, BasicCircleUnparsedMap

def normalize_obj(obj: Dict[str, Any]):
    for key, item in obj.items():
        if isinstance(item, list):
            obj[key] = json.dumps(item)
        elif isinstance(item, dict):
            obj[key] = json.dumps(item)
        elif isinstance(item, str):
            obj[key] = item.strip()

with open(r"InfoProviders\BasicInfoProvider\data.json", "r", encoding="utf-8") as file:
    src_data = json.load(file)

with open(r"InfoProviders\BasicInfoProvider\artist_info\artist_combo_map.json", "r", encoding="utf-8") as file:
    circle_override_map = json.load(file)

with open(r"InfoProviders\BasicInfoProvider\artist_info\artist_alt_map.json", "r", encoding="utf-8") as file:
    artist_alt_map = json.load(file)

CIRCLE_INFO_EXTRACTOR = re.compile(r'\[(.+)\]')

def nfkc_norm(s: str):
    return unicodedata.normalize('NFKC', s)

def mk_circle_set():
    # loop over the circles
    raw_circle_map = {}
    for raw_circle in src_data.keys():
        if (raw_circle in circle_override_map):
            raw_circle_map[raw_circle] = [nfkc_norm(i) for i in circle_override_map[raw_circle]]
            continue

        circle_info = CIRCLE_INFO_EXTRACTOR.search(raw_circle)
        if circle_info is None:
            print(f"Circle {raw_circle} has no circle info")
            input()
            continue

        circle_info = nfkc_norm(circle_info.group(1).strip())

        raw_circle_map[raw_circle] = [circle_info]

    circle_join = { i for j in raw_circle_map.values() for i in j }

    circle_map = {}
    for circle in circle_join:
        circle_init = {
            "id": str(uuid4()),
            "name": circle,
            "alias": []
        }

        circle_map[circle] = circle_init


    for circle in list(artist_alt_map.keys()):
        val = artist_alt_map[circle]
        actual_name, alias = nfkc_norm(val[0]), [nfkc_norm(i) for i in val[1:]]
        circle_map[actual_name]["alias"] += (alias)
        del artist_alt_map[circle]

    if (len(artist_alt_map) != 0):
        print("Unmapped artist alt")
        pprint(artist_alt_map)
        input()

    return (raw_circle_map, circle_map)
    

if (__name__ == '__main__'):
    raw_map, circle_map = mk_circle_set()

    # Create circle instances
    count = 0
    for circle_name, init_value in circle_map.items():
        normalize_obj(init_value)

        count += 1
        print(f"({count}/{len(circle_map)}) Creating circle {circle_name}", end='\r')

        BasicCircle.create(**init_value)

    # Add Unparsed Circles
    raw_circle_instance = []
    count = 0
    for raw_circle, circles in raw_map.items():
        count += 1
        print(f"({count}/{len(raw_map)}) Creating unparsed circle {raw_circle}", end='\r')
        for circle in circles:
            c = BasicCircle.select().where(BasicCircle.name == circle).get()
            init = {
                "id": str(uuid4()),
                "unparsed_name": raw_circle,
                "circle_id": c
            }

            normalize_obj(init)

            BasicCircleUnparsedMap.create(**init)
