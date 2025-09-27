from __future__ import annotations
from pathlib import Path
from typing import Tuple
from app.services.ffmpeg_runner import  run_ffmpeg
from app.utils.paths import unique_output
from app.core.errors import FFmpegError
import ffmpeg
from app.core.config import WEB_SAFE

def trim_video(input_path: Path, start: float, duration: float, overwrite: bool = True) -> Tuple[Path, float, str]:

    if start < 0 or duration <= 0:
        raise FFmpegError("start must be >= 0 and duration > 0")

    out_path = unique_output(input_path.stem, input_path.suffix or ".bin")
    """"
    cmd = [
        "ffmpeg",
        *base_flags(overwrite),
        "-ss", str(start), "-t", str(duration), #זה אומר מאיפה עד איפה זה הולך לרוץ,ושמנו את זה לפני ה -i כדי שהקורא ידע לקפוץ ישר לשם ולא לקרו סתם עד לשם
        "-i", str(input_path),
        "-c", "copy", "-map", "0", "-avoid_negative_ts", "make_zero",#אל תקודד מחדש אלא פשוט תעתיק,שמור על כל עטיפות שבאות עם הקובץ(כתוביות באנגלית/בעברית),ואם נקודת ההתחלה לאחר החיתוך של הSS מתחת לאפס אז אנחנו מזיזים אותו לאפס
        str(out_path),
    ]
    """""
    cmd = (
        ffmpeg
        .input(str(input_path), ss=start, t=duration)
        .output(str(out_path), **WEB_SAFE)
    )
    _, elapsed = run_ffmpeg(cmd)

    if not out_path.exists():
        raise FFmpegError("no output produced")

    return out_path, elapsed, " ".join(cmd)