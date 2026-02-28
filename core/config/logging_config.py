import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        base = {
            "timestamp": self.formatTime(record),
            "level":     record.levelname,
            "message":   record.getMessage(),
        }
        # record.extra already merged by logging library
        for k, v in record.__dict__.items():
            if k not in ("msg","args","levelname","levelno","pathname","filename","module","exc_info","exc_text","stack_info","lineno","funcName","created","msecs","relativeCreated","thread","threadName","processName","process"):
                base[k] = v
        return json.dumps(base)
