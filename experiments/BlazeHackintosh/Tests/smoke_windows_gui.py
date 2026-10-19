"""Real Windows HWND smoke for the UNRELEASED BlazeHackintosh research GUI.

This script launches the compiled EXE, verifies a visible top-level HWND belongs
specifically to the expected executable and its launched process tree, requests a graceful close, and waits
for process exit. It never invokes a hardware scan or installer action.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import sys
import time

# Windows Toolhelp process snapshots are used only for PID ancestry verification.
# A matching title and EXE path alone could belong to an unrelated, preexisting GUI.

TITLE_MARKER = "BlazeHackintosh — Research Workbench (Experimental)"


def title_is_expected(title: str) -> bool:
    return title == TITLE_MARKER


def executable_is_expected(actual: str, expected: str) -> bool:
    # Normalize separators and case on Windows. os.path.normcase is platform
    # dependent; casefold ensures test coverage on non-Windows development hosts.
    def normalize(path: str) -> str:
        return os.path.normpath(os.path.abspath(path)).replace("/", "\\").casefold()
    return normalize(actual) == normalize(expected)


def pid_is_descendant(pid: int, root_pid: int, parents: dict[int, int]) -> bool:
    """Accept only the process we launched or its child; reject cycles and gaps."""
    if pid <= 0 or root_pid <= 0:
        return False
    seen = set()
    for _ in range(64):
        if pid == root_pid:
            return True
        if pid in seen:
            return False
        seen.add(pid)
        pid = parents.get(pid, 0)
        if pid <= 0:
            return False
    return False


def _windows_process_parents() -> dict[int, int]:
    """Read process parent PIDs without shell commands or third-party modules."""
    if sys.platform != "win32":
        raise RuntimeError("Process ancestry requires Windows")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == ctypes.c_void_p(-1).value or snapshot is None:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            raise ctypes.WinError(ctypes.get_last_error())
        parents = {}
        while True:
            parents[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
            if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                error = ctypes.get_last_error()
                if error != 18:  # ERROR_NO_MORE_FILES
                    raise ctypes.WinError(error)
                break
        return parents
    finally:
        kernel32.CloseHandle(snapshot)


def _window_from_exe(expected_exe: str, launched_pid: int):
    if sys.platform != "win32":
        raise RuntimeError("Windows HWND smoke requires Windows")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [CALLBACK, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    parents = _windows_process_parents()
    matches = []
    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length < 1 or length > 512:
            return True
        title = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title, len(title))
        if not title_is_expected(title.value):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid_is_descendant(int(pid.value), launched_pid, parents):
            return True
        handle = kernel32.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return True
        try:
            buf = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(buf))
            if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                if executable_is_expected(buf.value, expected_exe):
                    matches.append(hwnd)
        finally:
            kernel32.CloseHandle(handle)
        return True
    callback_ref = CALLBACK(callback)
    if not user32.EnumWindows(callback_ref, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return matches[0] if matches else None


def run_smoke(exe: Path, timeout_seconds: int = 90) -> None:
    if sys.platform != "win32":
        raise RuntimeError("A real compiled Windows GUI smoke requires Windows")
    exe = exe.resolve(strict=True)
    if exe.suffix.lower() != ".exe":
        raise ValueError("Expected a Windows executable")
    if timeout_seconds < 10 or timeout_seconds > 180:
        raise ValueError("Invalid smoke timeout")
    print("Launching unreleased research GUI; no scan will be initiated", flush=True)
    process = subprocess.Popen([str(exe)], cwd=str(exe.parent), close_fds=True)
    try:
        deadline = time.monotonic() + timeout_seconds
        hwnd = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise AssertionError(f"GUI exited before creating a window: {process.returncode}")
            hwnd = _window_from_exe(str(exe), process.pid)
            if hwnd is not None:
                break
            time.sleep(0.5)
        if hwnd is None:
            raise AssertionError("No visible GUI HWND from expected EXE before timeout")
        print("PASS: Visible research GUI HWND owned by expected EXE", flush=True)
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.SendMessageTimeoutW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                                                wintypes.LPARAM, wintypes.UINT, wintypes.UINT,
                                                ctypes.POINTER(ctypes.c_size_t)]
        user32.SendMessageTimeoutW.restype = wintypes.LPARAM
        result = ctypes.c_size_t()
        if not user32.SendMessageTimeoutW(hwnd, 0x0010, 0, 0, 0x0002, 5000, ctypes.byref(result)):
            raise AssertionError("WM_CLOSE could not be delivered to research GUI")
        try:
            exit_code = process.wait(timeout=20)
        except subprocess.TimeoutExpired as exc:
            raise AssertionError("GUI did not exit gracefully after WM_CLOSE") from exc
        if exit_code != 0:
            raise AssertionError(f"GUI exited with code {exit_code}")
        print("PASS: Compiled research GUI closed gracefully with exit code 0", flush=True)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=15)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()
    run_smoke(args.exe, args.timeout)


if __name__ == "__main__":
    main()
