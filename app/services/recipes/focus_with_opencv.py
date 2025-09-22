from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import time, math
import numpy as np
import cv2

#מטרת הפונקציה לתת מספר חדות(כמה התמונה משוננת)
def _vol(gray: np.ndarray) -> float:
    #יnp.ndarray הוא מערך דו ממדי שבו כל תא מבטא פיקסל
    gray = cv2.GaussianBlur(gray, (3,3), 0.8)  # יGaussianBlur מוריד רעש נקודתי(פעמון גאוס)
    lap = cv2.Laplacian(gray, ddepth=cv2.CV_64F, ksize=3) #יLaplacian בודק כמה כל פיקסל שונה משכנו(מכפיל במסכה ומאחד למספר)
    return float(lap.var()) #חישוב שונות לפריים


# מחליק את ציוני החדות לאורך הזמן בעזרת ממוצע נע (חלון win) כדי לצמצם ריצוד ופולסים בודדים.
def _smooth(xs: List[float], win: int = 5) -> List[float]:
    #חלון(win ) אומר כמה ניקח מכל צד לשכלול הממוצע
    # רשימת ציוני חדות xs לפרימים
    if win <= 1 or len(xs) <= 2: return xs
    kernel = np.ones(win, dtype=np.float64) / win #אנחנו יוצרים מערך בגודל win שממולה באחד חלקי הwin
    sm = np.convolve(np.asarray(xs, dtype=np.float64), kernel, mode="same")#הפעולה convolve בעצם עובר על כל איבר במערך הציונים לוקח את WIN/2 מכל צד שלו הסכום שלהם חלקיWIN הוא הממוצע הנע
    # יmode="same" אומר לנו שאם אנחנו מחשבים  convolve לציון קיצון שיש לו רק שכן אחד, משמאל או מימין אז נחשב את השכן השני שלו בתור 0,אבל בכל זאת נעבור על כל המערך הציונים
    #NumPy הופכים את הציונים למערך np.asarray
    return sm.tolist()


#פונקציה  שלוקחת  רשימת ציוני חדות לאורך הזמן ומחזירה  מקטעים בזמן שבהם הווידאו מטושטש
def _segments(scores: List[float], fps: float, thr: float,
              min_len_s: float = 0.5, merge_gap_s: float = 0.33):
    blurry = [s < thr for s in scores]
    segs = [] # רשימה שעאינה ניתנת לשינוי -> List[Tuple[s,e]]
    start = None
    for i, b in enumerate(blurry): #יenumerate מחזיר את האינדקס(i) וגם את הערך(b) לכל איבר בblurry
        if b and start is None:
            start = i
        elif not b and start is not None:
            segs.append((start, i-1))
            start = None
    if start is not None: #אם הסרטון נגמר מטושטש אז נסגור ידנית
        segs.append((start, len(blurry)-1))

    min_len = max(1, int(round(min_len_s * fps))) # מה אורך המינמום שנחשיב את זה לנפילה
    gap = max(0, int(round(merge_gap_s * fps)))
    segs = [(a,b) for (a,b) in segs if (b - a + 1) >= min_len] # שומרים רק רצפים של אין פוקוס ולא פריים אחד או שתיים שנפל להם הפוקוס

    # (gap)אם יש חזרה לפופקוס אבל לקצת זמן אז נמזג את זה לנפיל הפוקוס הקודמת אם לא עברה כמות הפרימים המקסימאלית שהגדרנו
    merged = [] # רשימה שניתנת לשינוי -> List[List[s,e]]
    for s,e in segs:
        if not merged:
            merged.append([s,e]); continue
        ps,pe = merged[-1] #שליפת הזוג האחרון ברשימה
        if s - pe - 1 <= gap:
            merged[-1][1] = e
        else:
            merged.append([s,e])

    return [{"start_sec": round(s/fps,3), "end_sec": round(e/fps,3)} for s,e in merged]# מחזיר רשימה של מילונים שהמציגים את הנקודה בה התחיל ונגמר חוסר הפוקוס

#פונקציה שממריה כל פריים שהיא מקבלת לאפור וקטן יותר
def _resize_gray(frame_bgr: np.ndarray, target_w: int) -> np.ndarray:
    h, w = frame_bgr.shape[:2] #מחזיר (height, width, channels) ואנחנו מתייחסים רק לשניים הראשונים
    if w == 0 or h == 0:
        raise ValueError("empty frame")

    w_target = min(target_w, w)  # אל תעלה מעל רוחב המקור
    ratio = w_target / float(w) # כאן אנו קובעים בכמה נכווץ את הפריים או לא נכווץ אם הפריים בא באיכות נמוכה יותר מהסף
    new_h = int(round(h * ratio))# חישוב הגובה החדש
    if new_h % 2: new_h += 1
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (target_w, new_h), interpolation=cv2.INTER_AREA) # יINTER_LINEAR היא שיטה שמקטינה את הפריים
    return gray

def analyze_focus_segments_simple(
    input_path: Path,
    target_fps: float = 6.0,
    width: int = 640,
    smooth_win: int = 5,
    thr_factor: float = 0.6,
    min_len_s: float = 0.5,
    merge_gap_s: float = 0.33,
    include_scores: bool = False,
) -> Tuple[Dict, float]:

    t0 = time.time()
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError("could not open video")

    src_fps = cap.get(cv2.CAP_PROP_FPS)
    if not src_fps or math.isnan(src_fps) or src_fps <= 0:
        src_fps = 30.0  # ברירת מחדל אם חסר מידע
    stride = max(1, int(round(src_fps / float(target_fps))))
    fps_analyzed = src_fps / stride

    scores: List[float] = []
    first_h = None
    i = 0
    ok, frame = cap.read()
    while ok:
        if i % stride == 0:
            gray_small = _resize_gray(frame, width)
            if first_h is None:
                first_h = gray_small.shape[0]
            s = _vol(gray_small)
            scores.append(s if math.isfinite(s) else 0.0)
        ok, frame = cap.read()
        i += 1

    cap.release()

    if not scores:
        raise RuntimeError("no frames analyzed")

    smooth = _smooth(scores, win=max(3, smooth_win))
    median = float(np.median(smooth))
    threshold = float(median * thr_factor)

    segs = _segments(
        scores=smooth,
        fps=fps_analyzed,
        thr=threshold,
        min_len_s=min_len_s,
        merge_gap_s=merge_gap_s,
    )

    result = {
        "fps_analyzed": round(fps_analyzed, 4),
        "frame_size": {"width": width, "height": int(first_h or 0)},
        "metric": "variance_of_laplacian",
        "median_score": median,
        "threshold": threshold,
        "num_frames": len(smooth),
        "blurry_segments": segs,
    }
    if include_scores:
        result["per_frame_scores"] = [round(x, 3) for x in smooth]

    elapsed = time.time() - t0
    return result, elapsed
