import os
import json

dir_descendants = {}

with open(r'Preprocessor/disc-tagger/dir_descendants.json', 'r', encoding='utf-8') as f:
    dir_descendants = json.load(f)

ADD_PATH = r'Preprocessor/disc-tagger/man_add.json'
man_add = []
if (os.path.exists(ADD_PATH)):
    with open(ADD_PATH, "r", encoding="utf-8") as f:
        man_add = json.load(f)


IGNORE_PATH = r"Preprocessor/disc-tagger/man_ignore.json"
man_ignore = []
if (os.path.exists(IGNORE_PATH)):
    with open(IGNORE_PATH, "r", encoding="utf-8") as f:
        man_ignore = json.load(f)

AMBIGUOUS_PATH = r"Preprocessor/disc-tagger/man_ambig.json"
man_ambig = []
if (os.path.exists(AMBIGUOUS_PATH)):
    with open(AMBIGUOUS_PATH, "r", encoding="utf-8") as f:
        man_ambig = json.load(f)

NEW_ADD_PATH = r'Preprocessor/disc-tagger/man_new_add.json'
new_add = []
if (os.path.exists(NEW_ADD_PATH)):
    with open(NEW_ADD_PATH, "r", encoding="utf-8") as f:
        new_add = json.load(f)

def ls(root, inc_dir=False):
    print("Listing all files in ", root)
    for file in os.listdir(root):
        if (not inc_dir):
            if (os.path.isfile(os.path.join(root, file))):
                print("\t", file)
        else:
            print("\t", file)
        
def man(dir_descendants, path):
    """
    return 1 - rerun the function with same params
    return 0 - continue
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Root directory: ", path)
    subdirs = dir_descendants[path]
    print("Subdirectories: ")
    for idx, i in enumerate(subdirs):
        print(f"[{idx}] {i}")
    
    print()

    while True:
        disc = input('Is this a disc? (y/N): ') or 'n'
        if (disc.lower() == 'n'):
            man_ignore.append(path)
            with open(IGNORE_PATH, "w", encoding="utf-8") as f:
                json.dump(man_ignore, f, ensure_ascii=False, indent=4, sort_keys=True)

            return 0
        
        if (disc.lower() == 'a'):
            man_ambig.append(path)
            with open(AMBIGUOUS_PATH, "w", encoding="utf-8") as f:
                json.dump(man_ambig, f, ensure_ascii=False, indent=4, sort_keys=True)

            return 0

        if (disc.lower() == 'y'):
            break

        if (disc.lower().startswith('lsr')):
            if (len(disc.split(' ')) == 1):
                ls(path, inc_dir=True)
                continue
            else:
                lsr_idx = int(disc.split(' ')[1].strip())
                ls(os.path.join(path, subdirs[lsr_idx]), inc_dir=True)
                continue

        if (disc.lower().startswith('ls')):
            if (len(disc.split(' ')) == 1):
                ls(path)
                continue
            else:
                lsr_idx = int(disc.split(' ')[1].strip())
                ls(os.path.join(path, subdirs[lsr_idx]))
                continue

    exclude_directory = input(f'Enter indicies of excluded directory (0 - {len(subdirs) - 1}): ')
    if (exclude_directory == ''):
        exclude_directory = []
    
    else:
        exclude_directory = [int(i.strip()) for i in exclude_directory.split(' ')]

    parent = input('Is the parent directory also a disc? (y/N): ')
    useParent = False
    if (parent.lower() == 'y'):
        useParent = True

    for i in [subdirs[idx] for idx in exclude_directory]:
        subdirs.remove(i)
    

    l = []
    for dir in subdirs:
        l.append({
            "path": os.path.join(path, dir),
            "disc_number": 0,
            "name": ''
        })

    if (useParent):
        l.append({
            "path": path,
            "disc_number": 0,
            "name": ''
        })

    print("Result: ")
    print(json.dumps(l, ensure_ascii=False, indent=4, sort_keys=True))

    if (input("Is this correct? (y/N): ") != 'y'):
        return 1

    new_add.append({
        path: l,
    })

    with open(NEW_ADD_PATH, "w", encoding="utf-8") as f:
        json.dump(new_add, f, ensure_ascii=False, indent=4, sort_keys=True)

    return 0

if (__name__ == '__main__'):
    added_paths = [list(i.keys())[0] for i in (man_add.extend(new_add) or man_add)]
    for path in list(dir_descendants.keys()).copy():
        if (path in added_paths):
            print(f"Skipping [EXIST] {path}")
            continue
        if (path in man_ignore):
            print(f"Skipping [IGNORE] {path}")
            continue
        if (path in man_ambig):
            print(f"Skipping [AMBIG] {path}")
            continue
        input(f"Press enter to continue view next")
        while True:
            ret = man(dir_descendants, path)
            if (ret == 0):
                break
            elif (ret == 1):
                continue
            else:
                raise Exception("Invalid return value")
