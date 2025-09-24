# Video Processing API

A FastAPI-based service for **basic video editing** using **FFmpeg** (and optionally OpenCV for focus detection).  
Implements the following operations as standalone endpoints *and* a declarative `/process` pipeline:

- **Convert** (re-encode to MP4 / H.264 + AAC)
- **Trim** (cut by time range)
- **Resize** (scale by percentage, keeping aspect ratio)
- **Rotate** (rotate pixels, not just metadata)
- **Text Overlay** (drawtext on video)
- **Filter** (grayscale, sharpen, etc.)
- **Focus Detection** (OpenCV implementation; FFmpeg-based version experimental)
- **Process** (batch multiple operations in one request)

---

## Quickstart (local, dev mode)

```bash
# install deps
pip install -r requirements.txt

# run server
uvicorn app.main:app --reload --port 8000

Open docs at: http://localhost:8000/docs
/process API
Request format

A JSON array of operations, in order:

[
  {"op":"grayscale"},
  {"op":"rotate","degrees":90}
]


Other examples:

[
  {"op":"trim","start":"00:00:00.0","end":"00:00:10.0"},
  {"op":"resize","scale_percent":50}
]

[
  {"op":"convert","to_format":"mp4"},
  {"op":"text","text":"Demo","x":40,"y":40,"font_size":24}
]

Response format

Video file is returned as attachment. Response headers include metadata:

x-any-success: true
x-success-count: 2
x-failure-count: 0
x-operations: grayscale,rotate
x-operations-results: grayscale=ok,rotate=ok
x-total-elapsed: 20.260

Focus Detection (optional)

Two implementations:

OpenCV (recommended)

Computes Variance of Laplacian per frame (or sampled frames).

Frames below a threshold for ≥ min_duration_sec are marked as “out of focus”.

Flexible: exposes laplacian_thresh, sample_rate_fps, min_duration_sec.

Output: JSON with blurry segments + optional annotated video.

FFmpeg (experimental)

Uses built-in filters (signalstats, convolution kernels) to measure sharpness per frame.

Advantage: runs fully in CLI, no Python frame decoding.

Limitation: less flexible for custom thresholds.

Focus is currently a separate endpoint (/focus/opencv, /focus/ffmpeg).
Not yet integrated into /process to keep the pipeline stable for demo.

Error Handling

API returns clear HTTP status codes:

400 Bad Request – invalid parameters (e.g. missing degrees).

413 Payload Too Large – file exceeds MAX_UPLOAD_BYTES.

415 Unsupported Media Type – input format not supported.

422 Unprocessable Entity – FFmpeg failed with invalid command/filters.

504 Gateway Timeout – processing exceeded the allowed runtime.

Each error response is JSON with { "ok": false, "error": "..." }.

Docker & Compose

Dockerfile defines a reproducible runtime (FFmpeg + Python + FastAPI).

docker-compose.yml allows running everything with one command.

Even with one service, Compose provides: reproducibility, shared volumes, and future extension (e.g. DB, Redis).

Project Notes

Default encoding: H.264 video + AAC audio, yuv420p, with faststart flag (web-safe).

Resize enforces even dimensions (required by H.264 / 4:2:0 chroma subsampling).

Rotate uses pixel-level transform, not just metadata, to ensure consistency.

Headers (x-operations, x-total-elapsed, etc.) provide debug/CI transparency.

Optional dev-only UI (ui.html) is included but not required by the assignment.