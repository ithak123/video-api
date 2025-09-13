from fastapi import FastAPI,UploadFile,File, Form, HTTPException

from app.services.request_runner import run_recipe_from_upload
from app.services.recipes.convert import convert_to_mp4
from app.services.recipes.trim import trim_video          # ← חדש
from app.services.recipes.resize import resize_video
from app.services.recipes.rotate import rotate_video
from app.services.recipes.overlay_text import overlay_text_video
from app.core.config import T_O_DEFAULT_POSITION, T_O_DEFAULT_FONT_SIZE

app = FastAPI(title="Video Processing API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/convert")
async def convert(file: UploadFile = File(...), to_formt: str = Form("mp4")):
    #כרגע אני מאפשר המרה רק לMP4
    if to_formt.lower() != "mp4":
        raise HTTPException(status_code=422, detail="Only mp4 is supported in this request")
    return await run_recipe_from_upload(
        file,
        suffix_from=file.filename,
        recipe_fn=lambda p: convert_to_mp4(p, overwrite=True),
        output_media_type="video/mp4",
        extra_headers={"X-Operation": "convert"},
    )

@app.post("/trim")
async def trim(
    file: UploadFile = File(...),
    start: float = Form(..., description="Start time (seconds, >= 0)"),
    duration: float = Form(..., description="Clip length (seconds, > 0)"),
):
    if start < 0 or duration <= 0:
        raise HTTPException(status_code=422, detail="start must be >= 0 and duration > 0")

    return await run_recipe_from_upload(
        file,
        suffix_from=file.filename,
        recipe_fn=lambda p: trim_video(p, start=start, duration=duration, overwrite=True),
        extra_headers={"X-Operation": "trim", "X-Mode": "copy"},
    )

@app.post("/resize")
async def resize(file: UploadFile = File(...), scale_percent: float = Form(...)):
    if scale_percent <= 4 or scale_percent > 400:
        raise HTTPException(status_code=422, detail="scale percentage must be between 4 and 400")

    return await run_recipe_from_upload(
        file,
        suffix_from=file.filename,
        recipe_fn=lambda p: resize_video(p, scale_percent=scale_percent, overwrite=True),
        extra_headers={"X-Operation": "resize", "X-Scale-Percent": str(scale_percent)},
    )

@app.post("/rotate")
async def rotate(file: UploadFile = File(...), degrees: int = Form(..., description="90,180,270 only")):

    if degrees not in (90, 180, 270):
        raise HTTPException(status_code=422, detail="degrees must be 90,180,270 only")

    return await run_recipe_from_upload(
        file,
        suffix_from=file.filename,
        recipe_fn=lambda p: rotate_video(p, degrees=degrees, overwrite=True),
        extra_headers={"X-Operation": "rotate", "X-Rotate-Degrees": str(degrees)},
    )

@app.post("/overlay_text")
async def overlay_text(
    file: UploadFile = File(...),
    text: str = Form(..., description="טקסט לצריבה (לבן + outline שחור)"),
    position: str = Form(T_O_DEFAULT_POSITION, description="top-left | top-right | bottom-left | bottom-right | center"),
    font_size: int = Form(T_O_DEFAULT_FONT_SIZE, description="גודל פונט (ברירת מחדל 36)"),
):
    valid_positions = {"top-left","top-right","bottom-left","bottom-right","center"}
    if position not in valid_positions:
        raise HTTPException(status_code=422, detail=f"position must be one of {sorted(valid_positions)}")
    if not (1 <= font_size <= 200):
        raise HTTPException(status_code=422, detail="font_size must be in 1..200")

    return await run_recipe_from_upload(
        file,
        suffix_from=file.filename,
        recipe_fn=lambda p: overlay_text_video(
            p,
            text=text,
            position=position,
            font_size=font_size,
            overwrite=True,
        ),
        extra_headers={
            "X-Operation": "overlay-text",
            "X-Overlay-Position": position,
            "X-Overlay-FontSize": str(font_size),
            "X-Overlay-FontColor": "white",
            "X-Overlay-Outline": "borderw=2,bordercolor=black@1",
        },
    )