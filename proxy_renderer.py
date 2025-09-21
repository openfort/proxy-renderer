import subprocess
import os
from pathlib import Path
import json
import time

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
    return None

def get_ffmpeg_encoders():
    def test_encoder(encoder):
        cmd = [
            "ffmpeg", "-hide_banner", "-f", "lavfi",
            "-i", "testsrc=duration=1:size=1280x720:rate=30",
            "-c:v", encoder, "-f", "null", "-"
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0

    hw_encoders = ["hevc_nvenc", "hevc_qsv", "hevc_amf"]

    supported = [e for e in hw_encoders if test_encoder(e)]
    print("Supported encoders:", supported)
    return supported

def detect_hw_encoder(encoders_list):
    if "hevc_nvenc" in encoders_list:
        return "hevc_nvenc"
    elif "hevc_qsv" in encoders_list:
        return "hevc_qsv"
    elif "hevc_amf" in encoders_list:
        return "hevc_amf"
    else:
        return "libx265"  # fallback to software
    
def render_proxy(input_file):
    folder_path = Path(os.path.dirname(input_file) + '/Proxy')
    folder_path.mkdir(parents=True, exist_ok=True)
    output_file = get_proxy_path(input_file)
    if not os.path.exists(input_file):
        print("File does not exist!")
        return 1
    if os.path.exists(output_file):
        print("File already exists!")
        return 1

    timecode = get_timecode(input_file)

    encoders_list = get_ffmpeg_encoders()
    hw_encoder = detect_hw_encoder(encoders_list)
    print(hw_encoder, output_file)

    result = subprocess.run([
        "ffmpeg",
        "-i", input_file,
        "-vf", "scale=1920:-2",      # resize to Full HD
        "-c:v", hw_encoder,
        "-rc:v", "vbr",
        "-b:v", "2M",                # target bitrate
        "-preset", "slow",           # encoding speed vs efficiency
        "-crf", "28",                # quality (higher = smaller files)
        "-c:a", "pcm_s16le",         # uncompressed audio
        "-timecode", timecode,       # preserve TC from metadata stream
        output_file
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
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

while(True):

    RAW_Data_dir = 'RAW_Data'

    render_list = get_render_list(RAW_Data_dir)

    for p in render_list:
        render_proxy(p)

    print('wait')
    time.sleep(60)