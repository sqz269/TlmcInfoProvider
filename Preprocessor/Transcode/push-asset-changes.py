import requests

BASEURL = ""
ASSET_JSON_PATCH_ENDPOINT = BASEURL + "/api/asset/{}"

def generate_patch_document(conversion_entry):
    """
    Conversion entry example:
    {
        "TrackId": "508f8177-894d-435c-ab66-5eef8ebcd9cf",
        "AssetId": "98cb507b-a6fe-4f4a-b6b9-42daa97fe825",
        "size": 26146732,
        "src": "/ext_data_b/torrent/TLMC v3/[crescentia]/2018.12.29 Touhou Orchestral Suite III - Journey [C95]/(04) [crescentia] wretched abstractions ~ sorcery's end.flac",
        "dst": "/ext_data_b/torrent/TLMC v3/[crescentia]/2018.12.29 Touhou Orchestral Suite III - Journey [C95]/(04) [crescentia] wretched abstractions ~ sorcery's end.m4a",
        "size_dst": 0,
        "processed": false,
        "error": null
    }
    """
    # TODO: Generate size information

    json_patch = [
        {
            "op": "replace",
            "path": "/AssetPath",
            "value": conversion_entry["dst"]
        },
        {
            "op": "replace",
            "path": "/AssetMime",
            "value": "audio/mp4"
        },
        {
            "op": "replace",
            "path": "/Size",
            "value": conversion_entry["size_dst"]
        }
    ]

    return json_patch

def push_asset_changes(conversion_entry):
    patch_doc = generate_patch_document(conversion_entry)
    asset_id = conversion_entry["AssetId"]
    endpoint = ASSET_JSON_PATCH_ENDPOINT.format(asset_id)
    response = requests.patch(endpoint, json=patch_doc)

    if response.status_code != 200:
        print("Failed to update asset: {}".format(asset_id))
        print(response.text)
        return False

    return True

