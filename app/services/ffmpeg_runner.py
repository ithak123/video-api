# app/services/ffmpeg_runner.py
from __future__ import annotations
from typing import List, Tuple
import subprocess, time

from app.core.config import FFMPEG_TIMEOUT_SEC, FFMPEG_LOGLEVEL, STDERR_TAIL_CHARS
from app.core.errors import FFmpegError


def run_ffmpeg(args: List[str], timeout: int = FFMPEG_TIMEOUT_SEC) -> Tuple[str, float]:
    """
    מריץ FFmpeg כפרוסס חיצוני בצורה בטוחה:
    - shell=False + רשימת ארגומנטים → אין הזרקת shell.
    - מודדים זמן ריצה (לשקיפות), לוכדים stderr (לדיבוג).
    - timeout מגן מתקיעות אינסופית.
    מחזיר: (stderr המלא, זמן ריצה בשניות).
    """
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
    """דגלים גלובליים מומלצים לכל הרצה."""
    return [
        "-hide_banner", "-loglevel", FFMPEG_LOGLEVEL,
        "-y" if overwrite else "-n",
    ]