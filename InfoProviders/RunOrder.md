# Info Providers Run Order

# Section 0: Detaching Long Running Command

## 0.1 Installing tmux
- Run `sudo apt install tmux`

## 0.2 Opening a new session
- Run `tmux`
- Note if you receive the following error: `tmux: missing or unsuitable terminal:`
    - Run `export TERM=xterm` (or replace xterm with your terminal)
    - Then run `tmux`

## 0.3 Run your command after opening a new session

## 0.4 Detaching a session
- Press `Ctrl + b` then `d`

## 0.5 Reattaching a session
- Run `tmux at` to reattach the last session
- Run `tmux at -t <session-name>` to reattach a specific session
    - Hint: you can find the session name by running `tmux ls`

## 0.6 Terminating a session
- Run `tmux kill-session -t <session-name>`
- Or press `Ctrl + b` then `x` to kill the current session

# Section 1: Preprocessing

## 1.1 Archive Extraction
After downloading TLMC (Conner). You have to extract the archive.

### WARNING: this operation will take a long time. run in detached screen session

Open the script and change the path to error file

Move the script to the root of the TLMC directorry

Run: `Preprocessor/ext_del.py`

---

## 1.2 Cue Splitting
The script will split cues into tracks and save them as separate files, then it will delete the original cue and track files.

### This has to be done before any other processing

### WARNING: this operation will take a long time. run in detached screen session

Before running, Make sure you build the info provider first located at `Preprocessor/cue_split_info_provider`
- To build, cd to the directory and run
    - `dotnet restore`
    - then `dotnet publish -c Release`

After building the info provider, copy the output folder to `Preprocessor/cue_splitter/lib`
- after copying the dll should be under
    - `Preprocessor/cue_splitter/lib/CueSplitterInfoProvider.dll`

Run the script: `Preprocessor/cue_splitter/cue_splitter.py`
- File list is generated on the first run

---

## 1.3 Audio Normalization

Normalize audio files to a target volume. By default, the script uses EBU R128 loudness normalization profile on ffmpeg. 

### Note that this operation may decrease audio quality.

### this script can also be run as the last step of the pipeline (<- recommended)

### WARNING: this operation will take a long time. run in detached screen session

Run `Preprocessor/track_normalizer/normalize.py`

---

# Section 2: Info Providers

## 2.1 Scanning for TLMC Files

This script will generate a list of all TLMC files, and save it to a file. This file will be used by the other scripts to process the files without needing direct access to the TLMC folder.

Run `InfoProviders/BasicInfoProvider/flac-scanner.py`

### After running this script, a file named `data.json` will be generated

Copy the file to `InfoProviders/BasicInfoProvider/data.json`

---

## 2.2 Pushing the data to a temporary database

Run `InfoProviders/BasicInfoProvider/scanned-processor.py`

---

## 2.3 Process Album Artists

You might want to update the artist mapping located at `InfoProviders/BasicInfoProvider/artist_info`



Run `InfoProviders/BasicInfoProvider/scanned-process-artist.py`

---

## 2.4 Push data to website database

Run following scripts in order
1. `InfoProviders/BasicInfoProvider/push-scanned-artist.py`
2. `InfoProviders/BasicInfoProvider/flac-scanned-push-to-db.py`

# Section 3: ThWiki.cc Info Providers

Scripts must be run in order listed

## 3.1 Generating Query for Album Names

Run `InfoProviders/ThcInfoProvider/ThcQueryProvider/thc-scrape-query.py`

## 3.2 Scrape Album Metadata based on Query

Run `InfoProviders/ThcInfoProvider/ThcSongInfoProvider/thc-song-info-scraper.py`

## 3.3 Generate Original Track Names

This will generate a list of original tracks

Run `InfoProviders\ThcInfoProvider\ExternalData\get-original-alb-trk.py`

- After running the script, a CSV file will be generated containing the original track names and you need to manually fill in the missing data. 

## 3.4 Push Album Metadata to Database

Run `InfoProviders/ThcInfoProvider/ThcBasicDataCommit/commit-basic-data-to-db.py`
