
import json
import re


CIRCLE_INFO_EXTRACTOR = re.compile(r'\[(.+)\]')
ALBUM_INFO_EXTRACTOR = re.compile(r'(\d{4}(?:\.\d{2})?(?:\.\d{2})?)? ?(?:\[(.+\-.+)\])? ?(.+)')
TRACK_INFO_EXTRACTOR = re.compile(r'(?:(?:\{|\()(\d+)(?:\}|\)) )?(?:(?:\[|\{)(.+)(?:\]|\}) )?(.+)(?:(?:.mp3)|(?:.flac))')


with open(r"InfoProviders\BasicInfoProvider\data.json", "r", encoding="utf-8") as file:
    data = json.load(file)

    for circle, albums in data.items():

        for album in albums.keys():
            match = ALBUM_INFO_EXTRACTOR.match(album)
            grp = match.groups()
            print(grp)
            # input()
            if not any(grp):
                print(f"Failed to parse album: {album}")
                input()
                continue
