from __future__ import annotations
from pathlib import Path
from typing import Tuple
from app.services.ffmpeg_runner import run_ffmpeg
from app.utils.paths import unique_output
from app.core.errors import FFmpegError
from app.core.config import WEB_SAFE
import ffmpeg


def rotate_video(input_path: Path, degrees: int, overwrite: bool = True) -> Tuple[Path, float, str]:

    if degrees not in (90, 180, 270):
        raise FFmpegError("degrees must be 90, 180, or 270")

    suffix = f"_rot{degrees}cw"
    out_path = unique_output(input_path.stem + suffix, ".mp4")
    """""
    if degrees == 90:
        vf = "transpose=1"
    elif degrees == 180:
        vf = "hflip,vflip"
    else:
        vf = "transpose=2"

    cmd = [
        "ffmpeg",
        "-noautorotate",#אומר לFFmpeg להתעלם אם יש דגל של rotate במאטה דאטה
        *base_flags(overwrite),
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-metadata:s:v:0", "rotate=0",#אנחנו מאפסים את הדגל של הrotate בכדי למנוע סיבוב כפול
        str(out_path),
    ]
    """""
    if degrees in (90, 270):
        # transpose מדויק ל-90/270
        mode = 1 if degrees == 90 else 2
        cmd = (
            ffmpeg
            .input(str(input_path))
            .filter("transpose", mode)
            .output(str(out_path), **WEB_SAFE)
        )
    elif degrees == 180:
        cmd = (
            ffmpeg
            .input(str(input_path))
            .filter("hflip")
            .filter("vflip")
            .output(str(out_path), **WEB_SAFE)
        )
    else:
        raise ValueError("degrees must be 90/180/270")
    elapsed,c = run_ffmpeg(cmd)

    if not out_path.exists():
        raise FFmpegError("no output produced")

    return out_path, elapsed, " ".join(c)