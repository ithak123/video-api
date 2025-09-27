from __future__ import annotations
from pathlib import Path
from typing import Tuple
from app.services.ffmpeg_runner import run_ffmpeg
from app.utils.paths import unique_output
from app.core.errors import FFmpegError
from app.core.config import WEB_SAFE
import ffmpeg

def overlay_text_video(input_path: Path, text: str, position: str="bottom-right",
                       font_size: int=36, overwrite: bool=True):
    out_path = unique_output(input_path.stem, ".mp4")
    pos_map = {
        "top-left":     ("10", "10+ascent"),
        "top-right":    ("w-tw-10", "10+ascent"),
        "bottom-left":  ("10", "h-th-10"),
        "bottom-right": ("w-tw-10", "h-th-10"),
        "center":       ("(w-tw)/2", "(h-th)/2+ascent/2"),
    }
    x_expr, y_expr = pos_map.get(position, pos_map["bottom-right"])
    cmd = (
        ffmpeg
        .input(str(input_path))
        .filter("drawtext",
                text=text,
                fontsize=font_size,
                fontcolor="white",
                x=x_expr, y=y_expr,
                box=1, boxcolor="black@0.5", boxborderw=10)
        .output(str(out_path), **WEB_SAFE, preset="veryfast", crf=23)
    )
    _, elapsed = run_ffmpeg(cmd)
    return out_path, elapsed, cmd

