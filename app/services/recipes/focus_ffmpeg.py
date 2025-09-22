# app/services/recipes/focus_ffmpeg_simple.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess, shlex, time, re, math
import numpy as np

class FFmpegError(RuntimeError): ...

_YAVG_RE = re.compile(r"lavfi\.signalstats\.YAVG\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)")

def _smooth(xs: List[float], win: int = 5) -> List[float]:
    if win <= 1 or len(xs) <= 2: return xs
    win = min(win, len(xs))
    kernel = np.ones(win, dtype=np.float64) / win
    sm = np.convolve(np.asarray(xs, dtype=np.float64), kernel, mode="same")
    return sm.tolist()

def _segments(scores: List[float], fps: float, thr: float,
              min_len_s: float = 0.5, merge_gap_s: float = 0.33):
    # נמוך מהסף => מטושטש (פחות קצוות)
    blurry = [s < thr for s in scores]
    segs = []
    start = None
    for i, b in enumerate(blurry):
        if b and start is None:
            start = i
        elif not b and start is not None:
            segs.append((start, i-1))
            start = None
    if start is not None:
        segs.append((start, len(blurry)-1))

    min_len = max(1, int(round(min_len_s * fps)))
    gap = max(0, int(round(merge_gap_s * fps)))
    segs = [(a,b) for (a,b) in segs if (b - a + 1) >= min_len]

    merged = []
    for s,e in segs:
        if not merged:
            merged.append([s,e]); continue
        ps,pe = merged[-1]
        if s - pe - 1 <= gap:
            merged[-1][1] = e
        else:
            merged.append([s,e])

    return [{"start_sec": round(s/fps,3), "end_sec": round(e/fps,3)} for s,e in merged]

def _run_ffmpeg_scores(input_path: Path, fps: float, width: int) -> Tuple[List[float], str]:
    # שרשרת: דגימה → הקטנה → אפור → Sobel (קצוות) → signalstats (סטטיסטיקות) → metadata=print (להדפיס ללוג)
    vf = f"fps={fps},scale={width}:-2,format=gray,sobel,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "info",    # כדי שה-metadata יודפס
        "-i", str(input_path),
        "-vf", vf,
        "-f", "null", "-"       # לא מייצרים קובץ פלט; רק מריצים פילטרים
    ]
    cmd_str = " ".join(shlex.quote(x) for x in cmd)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise FFmpegError((p.stderr or p.stdout)[-500:])

    # מחפשים כל הופעה של YAVG בלוג (stderr/stdout—בפועל זה בדרך כלל ב-stderr)
    log = (p.stderr or "") + "\n" + (p.stdout or "")
    scores: List[float] = [float(m.group(1)) for m in _YAVG_RE.finditer(log)]
    return scores, cmd_str

def analyze_focus_segments_ffmpeg(
    input_path: Path,
    *,
    fps: float = 6.0,
    width: int = 640,
    smooth_win: int = 5,
    thr_factor: float = 0.6,
    min_len_s: float = 0.5,
    merge_gap_s: float = 0.33,
    include_scores: bool = False,
) -> Tuple[Dict, float, str]:
    """
    FFmpeg בלבד: מחשב 'צפיפות קצוות' (YAVG אחרי sobel) לכל פריים דגום,
    מחליק, שם סף אדפטיבי ומחזיר קטעי 'אין פוקוס' כ-dict.
    """
    t0 = time.time()
    scores_raw, cmd_str = _run_ffmpeg_scores(input_path, fps=fps, width=width)
    if not scores_raw:
        raise FFmpegError("no per-frame scores parsed from ffmpeg output")

    smooth = _smooth(scores_raw, win=max(3, smooth_win))
    median = float(np.median(smooth))
    threshold = float(median * thr_factor)  # מתחת לכך => מעט קווים => מטושטש

    segs = _segments(
        scores=smooth, fps=fps, thr=threshold,
        min_len_s=min_len_s, merge_gap_s=merge_gap_s
    )

    result = {
        "fps_analyzed": fps,
        "frame_size": {"width": width, "height": None},  # לא צריך לגובה כאן לבנצ'מרק
        "metric": "sobel_edge_YAVG",
        "median_score": median,
        "threshold": threshold,
        "num_frames": len(smooth),
        "blurry_segments": segs
    }
    if include_scores:
        result["per_frame_scores"] = [round(x, 3) for x in smooth]

    elapsed = time.time() - t0
    return result, elapsed, cmd_str
