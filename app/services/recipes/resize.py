from __future__ import annotations
from pathlib import Path
from typing import Tuple

from app.services.ffmpeg_runner import run_ffmpeg, base_flags
from app.utils.paths import unique_output
from app.core.errors import FFmpegError


def resize_video(input_path: Path, scale_percent: float, overwrite: bool = True) -> Tuple[Path, float, str]:

    if scale_percent < 4:
       raise FFmpegError("scale_percent must be > 4")

    factor = scale_percent / 100

    out_path = unique_output(input_path.stem, ".mp4")

    # בדיקה האם זה אי זוגי , והמרה בהתאם לזוגי בשביל המוקדד
    scale_expr = f"scale=trunc(iw*{factor}/2)*2:trunc(ih*{factor}/2)*2"

    cmd = [
        "ffmpeg",
        *base_flags(overwrite),
        "-i", str(input_path),
        "-vf", scale_expr,#יscale ההוא פילטר שמקטין/מגדיל את רזולוציית התמונה בסרטון
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(out_path),
    ]

    _, elapsed = run_ffmpeg(cmd)

    if not out_path.exists():
        raise FFmpegError("No output produced")

    return out_path, elapsed, " ".join(cmd)