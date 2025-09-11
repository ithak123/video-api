from fastapi import FastAPI,UploadFile,File, Form, HTTPException
from app.services.recipes.convert import convert_to_mp4
from app.services.request_runner import run_recipe_from_upload
from app.services.recipes.trim import trim_video          # ← חדש

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