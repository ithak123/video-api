from __future__ import annotations
from pathlib import Path
from typing import Tuple
from app.services.ffmpeg_runner import run_ffmpeg
from app.utils.paths import unique_output
from app.core.config import WEB_SAFE
import ffmpeg

def convert_to_mp4(input_path: Path, overwrite: bool = True) -> Tuple[Path, float, str]:

    # יstem אומר לי להחזיר את השם בלי הסיומת
    out_path = unique_output(input_path.stem, ".mp4")
    """cmd = [
        "ffmpeg",
        *base_flags(overwrite=overwrite),# הוככבית אומרת שאני רוצה להכניס רשימה לתוך רשימה אחרת
        "-i", str(input_path),  # -i אומר שהקלט אמור לבוא אחריו
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",#פה אנחנו קובעים באיזה מקודד נשתמש ,כמה מהר נקודד את זה, וכמה חזק נכווץ כל פריים
        "-pix_fmt", "yuv420p",  # אומר לי כל כמה פיקסלים אפורים אני שם פיקסל עם צבע(4),.
        "-c:a", "aac", "-b:a", "128k",#סוג מקודד האודיו
        "-movflags", "+faststart",#בעצם פה אנחנו מזיזים את קובץ הmoov שהוא אחד משלושת המרכיבים של MP4 והוא מחיל את המאטה דאטה , ואנחנו מזיזים אותו שיופיע לפני התוכן עצמו (מהיר יותר)
        str(out_path),
    ]"""
    cmd =(
        ffmpeg
        .input(str(input_path))
        .output(str(out_path),**WEB_SAFE)
    )
    #ההרצה בפועל ושמירת זמן הריצה
    _, elapsed = run_ffmpeg(cmd)

    if not out_path.exists():
        raise RuntimeError("Output not created (unexpected).")

        # מחזירים את נתיב הפלט, זמן הריצה
    return out_path, elapsed, " ".join(cmd)