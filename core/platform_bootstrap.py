import platform
import subprocess
import sys


for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


if platform.system() == "Windows":
    _OriginalPopen = subprocess.Popen

    class _NoConsolePopen(_OriginalPopen):
        def __init__(self, args, **kwargs):
            kwargs["creationflags"] = (
                kwargs.get("creationflags", 0) | subprocess.CREATE_NO_WINDOW
            )
            kwargs.pop("startupinfo", None)
            super().__init__(args, **kwargs)

    subprocess.Popen = _NoConsolePopen
