import functools
import inspect
import sys
import os
import traceback
import asyncio

def error_reporter(func):
    async def handle_async(*args, **kwargs):
        print(f"Called {func.__name__}")
        try:
            
            return await func(*args, **kwargs)
        except Exception as e:
            return _format_error(func, e)

    def handle_sync(*args, **kwargs):
        print(f"Called {func.__name__}")
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return _format_error(func, e)
    #print(f"[Functions] Agent has {func.__name__}")        
    return handle_async if inspect.iscoroutinefunction(func) else handle_sync


def _format_error(func, e):
    exc_type, _, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    line_number = exc_tb.tb_lineno
    tb = traceback.format_exc()

    error_info = {
        "error": f"{exc_type.__name__}: {e}",
        "function_name": func.__name__,
        "file": fname,
        "line": line_number,
        "traceback": tb
    }

    print("=== Exception caught in inner function ===")
    for k, v in error_info.items():
        print(f"{k}: {v}")
    print("=========================================")

    return error_info