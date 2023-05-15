import os

if (__name__ == '__main__'):
    tlmc_root = input('Enter the root directory of the TLMC: ')

    flacs = 0
    empty_flacs = 0
    for root, dirs, files in os.walk(tlmc_root):
        for file in files:
            if (file.lower().endswith('.flac')):
                path = os.path.join(root, file)
                if (os.path.getsize(path) == 0):
                    print(f'File {path} is empty')
                    empty_flacs += 1
                else:
                    flacs += 1
    print(f'Found {flacs} FLAC files, {empty_flacs} of which are empty')

