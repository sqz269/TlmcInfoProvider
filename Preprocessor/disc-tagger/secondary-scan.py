import os
import json

if (__name__ == '__main__'):
    tlmc_root = input('Enter the root directory of the TLMC: ')

    dir_descendants = {}

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

    with open('dir_descendants.json', 'w', encoding='utf-8') as f:
        json.dump(dir_descendants, f, ensure_ascii=False, indent=4, sort_keys=True)
