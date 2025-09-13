from __future__ import annotations
from pathlib import Path
from typing import Tuple

from app.services.ffmpeg_runner import run_ffmpeg,base_flags
from app.utils.paths import unique_output
from app.core.errors import FFmpegError


def grayscale_video(input_path: Path, overwrite: bool = True) -> Tuple[Path, float, str]:

    out_path = unique_output(input_path.stem + "_gray", ".mp4")

    vf = "hue=s=0,scale=trunc(iw/2)*2:trunc(ih/2)*2"

    cmd = [
        "ffmpeg",
        "-noautorotate",
        *base_flags(overwrite),
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(out_path),
    ]

    _, elapsed = run_ffmpeg(cmd)

    if not out_path.exists():
        raise FFmpegError("no output produced")

    return out_path, elapsed, " ".join(cmd)