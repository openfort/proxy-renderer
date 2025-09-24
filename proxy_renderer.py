import subprocess
import os
from pathlib import Path
import json
import time
try:
    import grp
except:
    pass

def get_proxy_path(file_dir):
    proxy_path = os.path.dirname(file_dir) + '/Proxy/' + os.path.basename(file_dir).split('.')[0] + '.mov'
    return proxy_path

def get_timecode(file_path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_streams",
            "-of", "json",
            file_path
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    data = json.loads(result.stdout)
    # Search all streams for a timecode tag
    for stream in data.get("streams", []):
        tags = stream.get("tags", {})
        if "timecode" in tags:
            return tags["timecode"]
    return "00:00:00:00"

def render_proxy(input_file):
    folder_path = Path(os.path.dirname(input_file) + '/Proxy')
    folder_path.mkdir(parents=True, exist_ok=True)
    try:
        gid = grp.getgrnam("users").gr_gid
        os.chown(folder_path, -1, gid)
        os.chmod(folder_path, 0o770)
    except:
        pass

    output_file = get_proxy_path(input_file)
    if not os.path.exists(input_file):
        print("File does not exist!")
        return 1
    if os.path.exists(output_file):
        print("File already exists!")
        return 1

    timecode = get_timecode(input_file)

    cmd = [
        "ffmpeg",
        '-hwaccel', 'vaapi',
        "-i", input_file,
        "-c:v", 'hevc_vaapi',
        "-vf", 'scale=1920:-2,format=nv12,hwupload',      # resize to Full HD
        "-rc:v", "vbr",
        "-b:v", "2M",                # target bitrate
        "-preset", "slow",           # encoding speed vs efficiency
        "-crf", "28",                # quality (higher = smaller files)
        "-c:a", "pcm_s16le",         # uncompressed audio
        "-timecode", timecode,       # preserve TC from metadata stream
        output_file
        ]

    result = subprocess.run(cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print('hevc_vaapi', output_file)
    try:
        gid = grp.getgrnam("users").gr_gid
        os.chown(output_file, -1, gid)
        os.chmod(output_file, 0o770)
    except:
        pass

    if result.returncode:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)

def find_video_files(root_folder):
    VIDEO_EXTS = {".mov", ".mp4", ".mxf", ".avi", ".mkv"}
    root = Path(root_folder)
    return [p for p in root.rglob("*") if p.suffix.lower() in VIDEO_EXTS]

def get_render_list(dir):
    videos = find_video_files(dir)
    render_list = []
    for p in videos:
        p = str(p)
        if not 'Proxy' in p:
            proxy_path = get_proxy_path(p)
            if Path(proxy_path) not in videos:
                render_list.append(Path(p))
    return render_list

RAW_Data_dir = 'RAW_Data'
render_list = get_render_list(RAW_Data_dir)
while(len(render_list)):
    for p in render_list:
        try:
            render_proxy(p)
        except:
            print(f'render failed: "{p}"')
    print('wait 1m')
    time.sleep(60)
    render_list = get_render_list(RAW_Data_dir)

print('Done!')