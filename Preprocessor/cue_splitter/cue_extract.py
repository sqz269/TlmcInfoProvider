import os
import json
import shlex
import subprocess

def mk_ffprobe_cmd(flac_path):
    exec = 'ffprobe'
    args = ['-show_format', '-of', 'json', '-i', shlex.quote(flac_path), '-hide_banner', '-v', 'quiet']
    cmd = [exec] + args
    p = subprocess.Popen(" ".join(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True, encoding="utf-8")

    out, err = p.communicate()
    if err:

        print(f"\n{err}\n")

        return None
    return out


def ext_cuesheet_param(flac_path):
    out = mk_ffprobe_cmd(flac_path)
    if not out:
        return None

    result = json.loads(out)
    result = result.get('format', {}).get('tags', {}).get('cuesheet', None)
    if not result:
        return None
    
    return result

def main():
    while True:
        flac_path = input("Enter flac path: ")
        dirname = os.path.dirname(flac_path)
        cue_name = os.path.splitext(os.path.basename(flac_path))[0] + ".cue"
        if not os.path.exists(flac_path):
            print("File not found")
            continue
        
        result = ext_cuesheet_param(flac_path)
        if not result:
            print("Cuesheet not found")
            continue

        cue_path = os.path.join(dirname, cue_name)
        with open(cue_path, 'w') as f:
            f.write(result)

        print(f"Cuesheet saved to {cue_path}")

if __name__ == "__main__":
    main()
