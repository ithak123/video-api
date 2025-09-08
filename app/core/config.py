#קובץ הגדרות נתונים סטטיים
from pathlib import Path

# איפה שומרים קבצים (סדר וניקיון)
DATA_DIR = Path("data")
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"

# Prefixים לבניית URLs שיוחזרו בתוך ה-JSON
FILES_URL_PREFIX = "/files"        # קישור לצפייה/הורדת הסרטון
MANIFEST_URL_PREFIX = "/manifest"  #קישור לדו"ח המלא

# מגבלות דמו
MAX_UPLOAD_BYTES   = 150 * 1024 * 1024   # 150MB
FFMPEG_TIMEOUT_SEC = 7 * 60              # 420 שניות
FFMPEG_LOGLEVEL    = "error"             # רק שגיאות בלי חפירות מיותרות

# כמה תווים מה-stderr להחזיר בתיאור שגיאה (ב-JSON) אם FFmpeg נפל
STDERR_TAIL_CHARS  = 800