from fastapi import FastAPI,UploadFile,File, Form, HTTPException
from app.services.recipes.convert import convert_to_mp4
from app.services.request_runner import run_recipe_from_upload

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