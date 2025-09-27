""""
#יffmpeg_runner גרסאת CLI 
from __future__ import annotations
from typing import List, Tuple
import subprocess, time
from app.core.errors import FFmpegError
from app.core.config import FFMPEG_TIMEOUT_SEC, FFMPEG_LOGLEVEL, STDERR_TAIL_CHARS

def run_ffmpeg(args: List[str], timeout: int = FFMPEG_TIMEOUT_SEC) -> Tuple[str, float]:
    # time.perf_counter() שעון של המערכת
    t0 = time.perf_counter()
    # בגלל שזו רשימה, subprocess משתמש ב־shell=False (בטיחותי, לא מפרש תווים מסוכנים).
    # יcapture_output אומר שאל תדפיס כלום למסך לאחר הרצת הshell
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    elapsed = time.perf_counter() - t0

    if proc.returncode != 0:
        tail = (proc.stderr or "")[-(STDERR_TAIL_CHARS):]  # לוקחים רק את ה"זנב" להגשה נקייה
        raise FFmpegError(f"FFmpeg failed (code {proc.returncode}). Tail:\n{tail}")

    # מחזירים stderr מלא (יש מקרים שבהם FFmpeg כותב לשם מידע חשוב) + זמן ריצה
    return proc.stderr or "", elapsed


def base_flags(overwrite: bool = True) -> List[str]:
    return [
        "-hide_banner", "-loglevel", FFMPEG_LOGLEVEL,
        "-y" if overwrite else "-n",
    ]
"""""

# יffmpeg_runner גרסאת ספריית פייתון
from __future__ import annotations
import time,ffmpeg
from app.core.errors import FFmpegError


def run_ffmpeg(cmd, overwrite_output: bool = True) -> tuple[float,str]:
    cmd = cmd.global_args("-hide_banner", "-loglevel", "error")
    if overwrite_output:
        cmd = cmd.overwrite_output()
    t0 = time.time()
    try:
        ffmpeg.run(cmd, capture_stdout=True, capture_stderr=True) #stdout – פלט רגיל,stderr – שגיאות/אזהרות/לוגים
    except ffmpeg.Error as e:
        tail = (e.stderr or b"").decode(errors="ignore").splitlines()[-10:]
        raise FFmpegError("ffmpeg failed:\n" + "\n".join(tail))

    elapsed = time.time() - t0
    cmd_str = " ".join(ffmpeg.compile(cmd))
    return elapsed, cmd_str
