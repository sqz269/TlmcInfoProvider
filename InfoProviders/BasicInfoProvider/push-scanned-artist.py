from InfoProviders.BasicInfoProvider.Model.BasicInfoModel import BasicCircle, BasicCircleUnparsedMap
from typing import Tuple
import requests
import json

HOST = "http://localhost:5217"
CIRCLE_ADD_ENDPOINT = HOST + "/api/internal/circle/add/{id}"

def basic_circle_to_request(bc: BasicCircle) -> Tuple[str, dict]:
    url = CIRCLE_ADD_ENDPOINT.format(id=bc.id)
    req = {
        "name": bc.name,
        "alias": json.loads(bc.alias)
    }

    return (url, req)

if (__name__ == '__main__'):
    total = BasicCircle.select().count()
    for idx, circle in enumerate(BasicCircle.select()):
        url, req = basic_circle_to_request(circle)
        print("({}/{}) Pushing circle {}".format(idx, total, circle.name), end="\r")
        result = requests.put(url, json=req)
        if (result.status_code != 200):
            print("Failed to push circle {} with status {}".format(circle.id, result.status_code))
