import mimetypes
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse

from app.core.config import MAX_UPLOAD_BYTES
from app.core.errors import FFmpegError
from app.utils.paths import save_upload_to_temp

# בדיקה והרצה של המתכון הרצוי!!
async def run_recipe_from_upload(
    upload_file,
    *, #מחייב אותנו שהכל אחריו יבוא לא בשורה אלא בעמודה
    suffix_from: str | None,
    recipe_fn,  # פונקציית המתכון: Path -> (Path, float, str)
    output_media_type: str | None = None,
    extra_headers: dict | None = None,
):

    data = await upload_file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large for demo")
    suffix = Path(suffix_from or "upload.bin").suffix or ".bin"

    #שמירה זמנית
    input_path = save_upload_to_temp(data, suffix=suffix)

    try:
        out_path, elapsed, cmd = recipe_fn(input_path)
    except FFmpegError as e:
        raise HTTPException(status_code=500, detail=f"FFmpegError: {e}")
    except Exception as e:
        # למשל בעיות הרשאות, נתיב, או באג בפייתון
        raise HTTPException(status_code=500, detail=f"Unhandled error: {repr(e)}")
    finally:
        #  ניקוי
        try:
            input_path.unlink(missing_ok=True)
        except Exception:
            pass


    headers = {"X-Elapsed-Seconds": f"{elapsed:.3f}", "X-FFmpeg-Cmd": cmd}
    if extra_headers:
        headers.update(extra_headers)

    #  זיהוי MIME אוטומטי אם לא הועבר במפורש
    media_type = output_media_type or mimetypes.guess_type(out_path.name)[0] or "application/octet-stream"

    return FileResponse(path=out_path, media_type=media_type, filename=out_path.name, headers=headers)

