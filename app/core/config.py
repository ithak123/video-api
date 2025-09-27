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

T_O_FONT_FILE = Path("app/NotoSansHebrew-Regular.ttf")  # פונט עברי bundled
T_O_MARGIN_PX = 40                         # שוליים פנימיים קבועים
T_O_FONT_COLOR = "white"                   # צבע טקסט ברירת מחדל
T_O_BORDER_W = 2                           # עובי outline
T_O_BORDER_COLOR = "black@1"               # צבע outline
T_O_DEFAULT_POSITION = "bottom-right"      # מיקום ברירת מחדל
T_O_DEFAULT_FONT_SIZE = 36                 # גודל פונט ברירת מחדל

WEB_SAFE = dict(vcodec="libx264", acodec="aac", pix_fmt="yuv420p", movflags="+faststart", preset="veryfast", crf=23)