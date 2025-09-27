from __future__ import annotations
from pathlib import Path
from typing import Tuple
from app.services.ffmpeg_runner import run_ffmpeg
from app.utils.paths import unique_output
from app.core.errors import FFmpegError
import ffmpeg
from app.core.config import WEB_SAFE


def grayscale_video(input_path: Path, overwrite: bool = True) -> Tuple[Path, float, str]:

   out_path = unique_output(input_path.stem + "_gray", ".mp4")
   """vf = "hue=s=0,scale=trunc(iw/2)*2:trunc(ih/2)*2"
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
    ]"""
   cmd =(
        ffmpeg
        .input(str(input_path))
        .filter("hue", s=0)
        .output(str(out_path), **WEB_SAFE)
   )
   _, elapsed = run_ffmpeg(cmd)

   if not out_path.exists():
        raise FFmpegError("no output produced")

   return out_path, elapsed, " ".join(cmd)