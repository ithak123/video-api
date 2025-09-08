# utils/paths.py
# יוצר את תיקיות העבודה, שומר קלטים זמניים בצורה יציבה ל־FFmpeg, ובוחר שמות פלט פנויים כדי שלא נדרוס קבצים קיימים.
from __future__ import annotations
from pathlib import Path
import tempfile
from app.core.config import DATA_DIR, UPLOAD_DIR, OUTPUT_DIR


def ensure_data_dirs() -> None:
    """יוצר את data/, uploads/, outputs/ אם לא קיימים."""
    for d in (DATA_DIR, UPLOAD_DIR, OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)

def save_upload_to_temp(data: bytes, suffix: str = ".bin") -> Path:
    """
    שומר את קובץ ההעלאה לקובץ זמני בתוך uploads/.
    FFmpeg מעדיף לעבוד מול נתיב קובץ יציב בדיסק.
    """
    ensure_data_dirs()
    with tempfile.NamedTemporaryFile(delete=False, dir=UPLOAD_DIR, suffix=suffix) as tmp:
        tmp.write(data)
        return Path(tmp.name)

def unique_output(name_hint: str, ext: str = ".mp4") -> Path:
    """
    מייצר שם פלט ייחודי ב-outputs/ כדי לא לדרוס פלט קיים.
    לדוגמה: clip.mp4 → clip.mp4 / clip_1.mp4 / clip_2.mp4...
    """
    ensure_data_dirs()
    # יstartswith מתודה מובנית בפייתון
    ext = ext if ext.startswith(".") else f".{ext}"
    base = OUTPUT_DIR / f"{name_hint}{ext}"
    if not base.exists():
        return base
    i = 1
    while True:
        candidate = OUTPUT_DIR / f"{name_hint}_{i}{ext}"
        if not candidate.exists():
            return candidate
        i += 1
