from typing import Callable, List, Dict
import json, mimetypes
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse

from app.core.config import MAX_UPLOAD_BYTES
from app.core.errors import FFmpegError
from app.utils.paths import save_upload_to_temp
from app.services.recipes.grayscale import grayscale_video
from app.services.recipes.rotate import rotate_video
from app.services.recipes.overlay_text import overlay_text_video
from app.services.recipes.resize import resize_video
from app.services.recipes.trim import trim_video
from app.services.recipes.convert import convert_to_mp4


_VALID_POSITIONS = {"top-left","top-right","bottom-left","bottom-right","center"}

# בדיקה והרצה של המתכון הרצוי!! - למתכון בודד
async def run_recipe_from_upload(
    upload_file,
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
def build_steps_from_ops_json(ops_json: str) -> tuple[List[tuple[str, Callable]], List[str]]:
    """
    ops JSON example:
    [{"op":"grayscale"},{"op":"rotate","degrees":90},{"op":"overlay_text","text":"שלום"}]
    """
    try:
        spec = json.loads(ops_json)
        if not isinstance(spec, list) or not spec:
            raise ValueError
    except Exception:
        raise HTTPException(422, "ops must be a non-empty JSON list")

    steps: List[tuple[str, Callable]] = []
    names: List[str] = []

    for item in spec:
        if not isinstance(item, dict) or "op" not in item:
            raise HTTPException(422, "each item must be an object with 'op' key")
        op = str(item.get("op") or "").lower().strip() #בשביל לא ליפויל בNONE

        if op == "grayscale":
            name, fn = "grayscale", (lambda p: grayscale_video(p, overwrite=True))

        elif op == "rotate":
            deg = item.get("degrees")
            if deg not in (90, 180, 270):
                raise HTTPException(422, "rotate.degrees must be 90,180,270")
            name, fn = "rotate", (lambda p, d=int(deg): rotate_video(p, degrees=d, overwrite=True))

        elif op == "overlay_text":
            text = item.get("text")
            if text is None or not str(text).strip():
                raise HTTPException(422, "overlay_text.text is required")
            position = str(item.get("position", "bottom-right"))
            if position not in _VALID_POSITIONS:
                raise HTTPException(422, f"overlay_text.position must be one of {sorted(_VALID_POSITIONS)}")
            font_size = int(item.get("font_size", 36))
            if not (1 <= font_size <= 200):
                raise HTTPException(422, "overlay_text.font_size must be in 1..200")
            name, fn = "overlay_text", (lambda p, t=str(text), pos=position, fs=font_size:
                                        overlay_text_video(p, text=t, position=pos, font_size=fs, overwrite=True))

        elif op == "resize":
            try:
                sp = float(item.get("scale_percent"))
            except Exception:
                raise HTTPException(422, "resize.scale_percent must be a number")
            if sp <= 4 or sp > 400:
                raise HTTPException(422, "resize.scale_percent must be in (4, 400]")
            name, fn = "resize", (lambda p, s=sp: resize_video(p, scale_percent=s, overwrite=True))

        elif op == "trim":
            try:
                start = float(item.get("start")); duration = float(item.get("duration"))
            except Exception:
                raise HTTPException(422, "trim.start and trim.duration must be numbers")
            if start < 0 or duration <= 0:
                raise HTTPException(422, "trim.start must be >=0 and duration > 0")
            name, fn = "trim", (lambda p, st=start, du=duration: trim_video(p, start=st, duration=du, overwrite=True))

        elif op == "convert":
            name, fn = "convert", (lambda p: convert_to_mp4(p, overwrite=True))  # כרגע תמיד ל-MP4

        else:
            raise HTTPException(422, f"unknown op: {op}")

        steps.append((name, fn))
        names.append(name)

    return steps, names

async def run_pipeline_from_upload(
    upload_file,
    *,
    suffix_from: str | None,
    steps: List[tuple[str, Callable]],
    output_media_type: str | None = "video/mp4",
    extra_headers: Dict | None = None,
):
    """
    מריץ את כל הצעדים ברצף. אם צעד נכשל – מדלגים וממשיכים.
    מחזיר את הווידאו האחרון שהצליח (או את המקור אם אף צעד לא הצליח) + כותרות סיכום.
    """
    data = await upload_file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large")

    suffix = Path(suffix_from or "upload.bin").suffix or ".bin"
    first_input: Path = save_upload_to_temp(data, suffix=suffix)

    cur = first_input
    last_ok: Path | None = None
    total_elapsed = 0.0
    ok, fail = 0, 0
    results: list[str] = []   # למשל: ["grayscale=ok","rotate=fail",...]
    garbage: list[Path] = []

    try:
        for name, fn in steps:
            try:
                out_path, elapsed, _cmd = fn(cur)
                results.append(f"{name}=ok")
                total_elapsed += float(elapsed)
                ok += 1
                if cur is not first_input and cur.exists():
                    garbage.append(cur)
                cur = out_path
                last_ok = out_path
            except (FFmpegError, Exception):
                results.append(f"{name}=fail")
                fail += 1
                # לא משנים cur; ממשיכים לצעד הבא

        final_out = last_ok if (last_ok and last_ok.exists()) else first_input

        headers = {
            "X-Operation": "pipeline",
            "X-Operations": ",".join([n for n, _ in steps]),
            "X-Operations-Results": ",".join(results),
            "X-Operations-Count": str(len(steps)),
            "X-Success-Count": str(ok),
            "X-Failure-Count": str(fail),
            "X-Any-Success": "true" if ok > 0 else "false",
            "X-Total-Elapsed": f"{total_elapsed:.3f}",
        }
        if extra_headers:
            headers.update(extra_headers)

        # ניקוי ביניים
        for p in garbage:
            try: p.unlink(missing_ok=True)
            except Exception: pass
        try:
            if final_out != first_input:
                first_input.unlink(missing_ok=True)
        except Exception: pass

        media_type = output_media_type or (mimetypes.guess_type(final_out.name)[0] or "video/mp4")
        return FileResponse(final_out, media_type=media_type, filename=final_out.name, headers=headers)

    except Exception as e:
        for p in garbage:
            try: p.unlink(missing_ok=True)
            except Exception: pass
        raise HTTPException(500, f"pipeline failed: {e}")
