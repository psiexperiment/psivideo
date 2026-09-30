from pathlib import Path
import subprocess


def compress_video():
    import argparse
    parser = argparse.ArgumentParser('psivideo-compress-video')
    parser.add_argument('filename')
    args = parser.parse_args()

    filename = Path(args.filename)
    filename_comp = filename.parent / (filename.stem + '_comp.mp4')
    args = [
        'ffmpeg',
        '-i', filename,
        '-vcodec', 'libx265',
        '-crf', '28',
        filename_comp
    ]
    result = subprocess.check_output(args)
