"""core/hw_sensors.py — leitura única de GPU/temperatura (zero subprocess)."""
import ctypes
import os
import platform

_OS = platform.system()
_nvml_lib = None
_nvml_ok = None


def get_gpu_usage() -> float:
    global _nvml_lib, _nvml_ok
    try:
        import pynvml
        pynvml.nvmlInit()
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        return float(pynvml.nvmlDeviceGetUtilizationRates(h).gpu)
    except Exception:
        pass

    if _nvml_ok is False:
        return -1.0
    try:
        class _Util(ctypes.Structure):
            _fields_ = [("gpu", ctypes.c_uint), ("memory", ctypes.c_uint)]

        if _nvml_lib is None:
            names = ("nvml",) if _OS == "Windows" else ("libnvidia-ml.so.1", "libnvidia-ml.dylib")
            loader = ctypes.WinDLL if _OS == "Windows" else ctypes.CDLL
            for n in names:
                try:
                    lib = loader(n)
                    lib.nvmlInit_v2()
                    _nvml_lib = lib
                    break
                except Exception:
                    continue

        if _nvml_lib is None:
            _nvml_ok = False
            return -1.0

        dev = ctypes.c_void_p()
        _nvml_lib.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(dev))
        u = _Util()
        _nvml_lib.nvmlDeviceGetUtilizationRates(dev, ctypes.byref(u))
        _nvml_ok = True
        return float(u.gpu)
    except Exception:
        _nvml_ok = False
        return -1.0


def get_cpu_temp() -> float:
    import psutil
    try:
        temps = psutil.sensors_temperatures()
        for name in [
            "coretemp", "k10temp", "cpu_thermal", "acpitz",
            "cpu-thermal", "zenpower", "it8688",
        ]:
            if name in temps and temps[name]:
                return temps[name][0].current
        for entries in temps.values():
            if entries:
                return entries[0].current
    except Exception:
        pass

    if _OS == "Windows":
        try:
            import wmi
            w = wmi.WMI(namespace="root/wmi")
            tz = w.MSAcpi_ThermalZoneTemperature()
            if tz:
                return (tz[0].CurrentTemperature / 10.0) - 273.15
        except Exception:
            pass

    return -1.0


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def get_idle_seconds() -> float:
    """Segundos desde o último teclado/mouse (Windows, chamada nativa). -1.0 se indisponível."""
    if _OS != "Windows":
        return -1.0
    try:
        info = _LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(info)
        if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            return -1.0
        kernel32 = ctypes.windll.kernel32
        kernel32.GetTickCount.restype = ctypes.c_uint
        return ((kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF) / 1000.0
    except Exception:
        return -1.0


def is_foreground_fullscreen() -> bool:
    """True se a janela em primeiro plano cobre a tela inteira e não tem barra de título."""
    if _OS != "Windows":
        return False
    try:
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == os.getpid():
            return False
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        if not (rect.left <= 0 and rect.top <= 0
                and rect.right >= user32.GetSystemMetrics(0)
                and rect.bottom >= user32.GetSystemMetrics(1)):
            return False
        if user32.GetWindowLongW(hwnd, -16) & 0x00C00000:
            return False
        cls = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(hwnd, cls, 64)
        return cls.value not in ("Progman", "WorkerW", "Shell_TrayWnd")
    except Exception:
        return False
