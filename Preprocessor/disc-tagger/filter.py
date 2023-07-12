import os
import json

if (__name__ == '__main__'):
    tlmc_root = input('Enter the root directory of the TLMC: ')

    existing_dics = None
    existing_discs_path = input('Enter the path to existing discs.json: ')
    if (existing_discs_path != ''):
        with open(existing_discs_path, 'r', encoding='utf-8') as f:
            existing_dics = json.load(f)
        
        existing_dics = [list(k.keys())[0] for k in existing_dics]
        print(f'Loaded {len(existing_dics)} discs from {existing_discs_path}')

        print("Loaded existing discs: ")
        print(json.dumps(existing_dics, ensure_ascii=False, indent=4, sort_keys=True))
        input('Press enter to continue...')

    dir_descendants = {}

    # structure
    """
    {
        "path/to/album": [
            {
                "disc_number": 1,
                "path": "path/to/album/disc1"
                "name": "disc1"
            }
        ]
    }
    """
    discs = []

    i = 0
    for circle_dir in os.listdir(tlmc_root):
        circle_dir = os.path.join(tlmc_root, circle_dir)
        if (not os.path.isdir(circle_dir)):
            continue
        
        for album_dir in os.listdir(circle_dir):
            album_dir = os.path.join(circle_dir, album_dir)
            if (os.path.isdir(album_dir)):
                dirs = []
                for file in os.listdir(album_dir):
                    if (os.path.isdir(os.path.join(album_dir, file))):
                        dirs.append(file)
                
                if (len(dirs) > 0):
                    dir_descendants[album_dir] = dirs
            i += 1
            print(f'Processed {i} albums', end='\r')

    known_non_disc = [
        "scan",
        "bk",
        "lyric",
        "irc"
    ]

    existing_dics_skipped = 0
    for path in list(dir_descendants.keys()).copy():
        dirs = dir_descendants[path]


        non_disc_dir = [i for i in dirs if any([i for j in known_non_disc if i.lower().startswith(j)])]
        if (len(non_disc_dir) == len(dirs)):
            del dir_descendants[path]
            continue

        if (existing_dics and path in existing_dics):
            existing_dics_skipped += 1
            print(f'Found EXISTING discs in {path}. Skip Add ({existing_dics_skipped}))')
            del dir_descendants[path]
            continue

        # check disc
        disc_dir = [i for i in dirs if 'disc' in i.lower()]
        if (len(disc_dir) == len(dirs)):
            l = []
            for dir in dirs:
                l.append({
                    'path': os.path.join(path, dir),
                    'disc_number': -1,
                    'name': ''
                })
            print(f'Found {len(l)} discs in {path}')
            discs.append({ path: l })

            del dir_descendants[path]
            continue

        print(f'Manual check: {path}')

    with open('dir_descendants.json', 'w', encoding='utf-8') as f:
        json.dump(dir_descendants, f, ensure_ascii=False, indent=4, sort_keys=True)

    with open('discs.json', 'w', encoding='utf-8') as f:
        json.dump(discs, f, ensure_ascii=False, indent=4, sort_keys=True)
