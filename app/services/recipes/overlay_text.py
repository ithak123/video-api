from __future__ import annotations
from pathlib import Path
from typing import Tuple

from app.services.ffmpeg_runner import run_ffmpeg, base_flags
from app.utils.paths import unique_output
from app.core.errors import FFmpegError
from app.core.config import (
    T_O_FONT_FILE,
    T_O_MARGIN_PX,
    T_O_FONT_COLOR,
    T_O_BORDER_W,
    T_O_BORDER_COLOR,
    T_O_DEFAULT_POSITION,
    T_O_DEFAULT_FONT_SIZE,
)

def _escape_drawtext_text(s: str) -> str:
    """Escape בסיסי ל-drawtext כשמשתמשים text='...'. מספיק ל-MVP."""
    if not s:
        return ""
    # נרמול שורות חלונות → '\n', ואז בריחה לפי הסדר הנכון
    s = s.replace("\r\n", "\n")
    s = s.replace("\\", "\\\\")  # קודם backslash!
    s = s.replace(":", "\\:")
    s = s.replace("'", "\\'")
    s = s.replace("%", "\\%")
    s = s.replace("\n", "\\n")
    return s

def _xy_for_position(position: str) -> tuple[str, str]:
    """
    ממפה פריסט מיקום לביטויי x,y ב-drawtext.
    text_w/text_h מגיעים מהפילטר עצמו; w/h הם ממדי הווידאו.
    """
    pos = (position or T_O_DEFAULT_POSITION).lower()
    m = T_O_MARGIN_PX
    if pos == "top-left":
        return (f"{m}", f"{m}")
    elif pos == "top-right":
        return (f"(w-text_w-{m})", f"{m}")
    elif pos == "bottom-left":
        return (f"{m}", f"(h-text_h-{m})")
    elif pos == "center":
        return ("(w-text_w)/2", "(h-text_h)/2")
    # ברירת מחדל: bottom-right
    return (f"(w-text_w-{m})", f"(h-text_h-{m})")

def overlay_text_video(
    input_path: Path,
    *,
    text: str,
    position: str = T_O_DEFAULT_POSITION,
    font_size: int = T_O_DEFAULT_FONT_SIZE,
    overwrite: bool = True,
) -> Tuple[Path, float, str]:
    """
    צריבת טקסט סטטי לכל אורך הווידאו עם outline לקריאות.
    צבע טקסט: לבן; outline: שחור (דק).
    מחזיר: (out_path, elapsed, cmd_str)
    """
    if not text or not text.strip():
        raise FFmpegError("text must not be empty")
    if font_size <= 0:
        raise FFmpegError("font_size must be > 0")

    # פלט MP4 תואם דפדפן
    suffix = "_txt"
    out_path = unique_output(input_path.stem + suffix, ".mp4")

    # פרמטרי drawtext
    esc_text = _escape_drawtext_text(text.strip())
    x_expr, y_expr = _xy_for_position(position)

    font_args = []
    if T_O_FONT_FILE.exists():
        font_args.append("fontfile=" + str(T_O_FONT_FILE))

    drawtext_parts = [
        *font_args,
        f"text='{esc_text}'",
        f"fontsize={font_size}",
        f"fontcolor={T_O_FONT_COLOR}",
        f"borderw={T_O_BORDER_W}",
        f"bordercolor={T_O_BORDER_COLOR}",
        f"x={x_expr}",
        f"y={y_expr}",
    ]
    drawtext_filter = "drawtext=" + ":".join(drawtext_parts)

    cmd = [
        "ffmpeg",
        "-noautorotate",
        *base_flags(overwrite),
        "-i", str(input_path),
        "-vf", drawtext_filter,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-metadata:s:v:0", "rotate=0",
        str(out_path),
    ]
    print("FFmpeg CMD:", " ".join(cmd), flush=True)
    _, elapsed = run_ffmpeg(cmd)

    if not out_path.exists():
        raise FFmpegError("no output produced")

    return out_path, elapsed, " ".join(cmd)
