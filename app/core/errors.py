class FFmpegError(RuntimeError):
    """שגיאה ייעודית לכשלי FFmpeg (נוח למפות ל-HTTP 500 ולהציג tail של stderr)."""
    pass
