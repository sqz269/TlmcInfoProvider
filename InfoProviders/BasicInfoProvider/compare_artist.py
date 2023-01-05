import json
from InfoProviders.BasicInfoProvider.Model.BasicInfoModel import BasicAlbum, BasicTrack, BasicAlbumPerformer, BasicCircle, BasicCircleUnparsedMap

if (__name__ == '__main__'):
    with open(r"InfoProviders\BasicInfoProvider\data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for circle_unparsed, v in data.items():
        c = BasicCircleUnparsedMap().select().where(BasicCircleUnparsedMap.unparsed_name == circle_unparsed).get_or_none()
        if (c is None):
            print("Circle not found: " + circle_unparsed)
            continue
