import os
import sys
import mslex
import argparse

# BITRATES = ["64k", "96k", "128k", "192k", "256k", "320k"]
BITRATES = ["128k", "192k", "320k"]

def mk_ffmpeg_cvt_cmd(src, root, bitrate):
    src = mslex.quote(src)
    seg_path = mslex.quote(os.path.join(root, "segment_%03d.m4s"))
    # init_path = mslex.quote(os.path.join(root, "init.mp4"))
    dst = mslex.quote(os.path.join(root, "playlist.m3u8"))
    return f"ffmpeg -i {src} -vn -b:a {bitrate} -f hls -hls_time 10 -hls_list_size 0 -hls_fmp4_init_filename init.mp4 -hls_segment_filename {seg_path} -hls_segment_type fmp4 -c:a aac {dst} -y -v quiet -stats"
            # 'ffmpeg -i input.aac -vn -b:a 128k -f hls -hls_time 10 -hls_list_size 0 -hls_segment_type fmp4 -c:a aac -hls_segment_filename "hls/128k/segment_%03d.m4s" -hls_init_filename "hls/128k/init.mp4" -hls_playlist_type vod "hls/128k/playlist.m3u8'

def mk_ffmpeg_norm_cmd(src, dst):
    src = mslex.quote(src)
    dst = mslex.quote(dst)
    return f"ffmpeg -i {src} -af loudnorm {dst} -y"

def mk_master_playlist(bitrate_list):
    playlist = "#EXTM3U\n"
    for bitrate in bitrate_list:
        playlist += f'#EXT-X-STREAM-INF:BANDWIDTH={bitrate},AUDIO="audio",CODECS="mp4a.40.2"\n'
        playlist += f"hls/{bitrate}/playlist.m3u8\n"
    return playlist

if __name__ == "__main__":
    # take args from command line, file path to target
    parser = argparse.ArgumentParser(description="Generate ffmpeg command for transcoding")
    parser.add_argument("file", help="Path to the file to be transcoded")

    args = parser.parse_args()

    if (not os.path.isfile(args.file)):
        print("File not found")
        sys.exit(1)

    # filename, no ext
    filename = os.path.basename(args.file)
    filename = filename[:filename.rfind(".")]

    parent = os.path.dirname(args.file)
    # output directory
    out_dir = os.path.join(parent, filename)
    os.makedirs(out_dir, exist_ok=True)

    # First normalize the file
    norm_filename = os.path.basename(args.file)
    norm_dst = os.path.join(parent, out_dir, f"{norm_filename}")
    cmd = mk_ffmpeg_norm_cmd(args.file, norm_dst)
    print(cmd)
    returncode = os.system(cmd)
    if (returncode != 0):
        print("Failed to normalize. FFMPEG return code: " + str(returncode))
        sys.exit(1)

    # change directory to output directory
    os.chdir(out_dir)
    print("Changed directory to " + out_dir)

    # Then transcode the file
    for bitrate in BITRATES:
        # get file diretory
        bitrate_root = os.path.join("hls", bitrate)
        playlist = os.path.join(bitrate_root, "playlist.m3u8")
        init = os.path.join(bitrate_root, "init.mp4")

        os.makedirs(bitrate_root, exist_ok=True)
        # generate ffmpeg command
        cmd = mk_ffmpeg_cvt_cmd(args.file, bitrate_root, bitrate)
        # print command
        print(cmd)
        # run command
        returncode = os.system(cmd)
        if (returncode != 0):
            print("Failed to transcode. FFMPEG return code: " + str(returncode))
            sys.exit(1)
        # mv init.mp4 to bitrate specific
        print("Moving init.mp4 to " + bitrate_root)
        os.rename("init.mp4", init)

    # generate master playlist
    master_playlist = mk_master_playlist(BITRATES)
    master_path = os.path.join(parent, "playlist.m3u8")
    with open(master_path, "w", encoding="utf-8") as f:
        f.write(master_playlist)
