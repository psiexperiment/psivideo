'''
Title-bar and taskbar branding for the video window.

psivideo ships `icons/main-icon.png` and `icons/main-icon.ico` (drawn by
`icons/make_icon.py`) so that it looks like the psi program it is. The video
window is an OpenCV HighGUI window rather than a Qt one, and HighGUI has no
call for setting a window icon, so this hands the icon straight to Windows:
on Windows a HighGUI window is a plain Win32 window and takes an icon through
`WM_SETICON` like any other. Off Windows this is a no-op -- the GTK and Cocoa
HighGUI backends expose no handle to hang an icon on.

Free of cv2 imports so that a program embedding psivideo can brand its own
windows, and fails soft throughout: an unbranded window is cosmetic and must
not keep video capture from starting.
'''
import logging
log = logging.getLogger(__name__)

import importlib.resources
import os


#: AppUserModelID claimed by psivideo. Windows groups taskbar buttons by this
#: ID, and a program that never sets one inherits the interpreter's -- which
#: is also what the programs spawning psivideo would be grouped under, so the
#: video window would share their button and their icon.
APP_ID = 'psi.psivideo'

#: Window class OpenCV's Win32 HighGUI backend registers for its windows.
#: Matching on it, and on the process, keeps a window of the same name in
#: another program from being branded instead of ours.
WINDOW_CLASS = 'Main HighGUI class'

WM_SETICON = 0x0080
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010

#: wparam of WM_SETICON, and the system metrics giving the size Windows wants
#: for each: the small icon goes in the title bar and alt-tab, the big one in
#: the taskbar and the alt-tab overlay.
ICON_SMALL, SM_CXSMICON, SM_CYSMICON = 0, 49, 50
ICON_BIG, SM_CXICON, SM_CYICON = 1, 11, 12

#: Icons already loaded, keyed by wparam. Loading is not repeated because the
#: handles are owned by the process until it exits (`LoadImage` with
#: LR_LOADFROMFILE gives an unshared icon), so reloading on every call would
#: leak one handle per call.
_icons = {}


def set_app_id(app_id=APP_ID):
    '''
    Give this process its own identity on the Windows taskbar.

    Deliberately duplicates `psiapp.util.set_app_id` (and the copy of it in
    `psi.application`) rather than importing it: psiapp is built on
    psiexperiment, which is built on psivideo, so psivideo cannot depend on
    either. Keep the three in sync by hand.

    Call this before the first window is created; afterwards Windows has
    already bound the process to the default ID and it has no effect.
    '''
    if os.name != 'nt':
        return
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        log.warning('Unable to set the AppUserModelID to %r', app_id,
                    exc_info=True)


def set_window_icon(window_name):
    '''
    Set psivideo's icon on an OpenCV window.

    Parameters
    ----------
    window_name : string
        Name the window was created with (`cv2.namedWindow`), which is also
        its title. The window must already exist; `cv2.namedWindow` is enough,
        the first `imshow` is not needed.
    '''
    if os.name != 'nt':
        return
    try:
        _set_window_icon(window_name)
    except Exception:
        log.warning('Unable to set the icon on the %r window', window_name,
                    exc_info=True)


def _set_window_icon(window_name):
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL('user32', use_last_error=True)
    # Declared rather than left to the defaults, which return a C int and so
    # truncate window and icon handles to 32 bits on 64-bit Windows.
    user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.FindWindowW.restype = wintypes.HWND
    user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR,
                                  wintypes.UINT, ctypes.c_int, ctypes.c_int,
                                  wintypes.UINT]
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
                                    wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = wintypes.LPARAM

    hwnd = _find_window(user32, wintypes, window_name)
    if not hwnd:
        log.warning('No %r window of this process to set the icon on',
                    window_name)
        return

    for which, (cx, cy) in ((ICON_SMALL, (SM_CXSMICON, SM_CYSMICON)),
                            (ICON_BIG, (SM_CXICON, SM_CYICON))):
        if which not in _icons:
            size = user32.GetSystemMetrics(cx), user32.GetSystemMetrics(cy)
            _icons[which] = _load_icon(user32, ctypes, size)
        user32.SendMessageW(hwnd, WM_SETICON, which, _icons[which])


def _find_window(user32, wintypes, window_name):
    '''
    Handle of this process's HighGUI window with this name, or None.

    `FindWindow` would search every process, so the windows are enumerated
    and filtered by process instead: two programs showing video at once (a
    psi experiment and a bare `psivideo`, say) each have a window named
    `Video`, and branding the other one's would be both wrong and invisible.
    '''
    import ctypes

    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND,
                                   wintypes.LPARAM)
    user32.EnumWindows.argtypes = [enum_proc, wintypes.LPARAM]
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR,
                                     ctypes.c_int]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR,
                                      ctypes.c_int]

    pid = os.getpid()
    text = ctypes.create_unicode_buffer(512)
    found = []

    def visit(hwnd, lparam):
        window_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
        if window_pid.value != pid:
            return True
        user32.GetClassNameW(hwnd, text, len(text))
        if text.value != WINDOW_CLASS:
            return True
        user32.GetWindowTextW(hwnd, text, len(text))
        if text.value != window_name:
            return True
        found.append(hwnd)
        # Stop enumerating; the first match is the window.
        return False

    user32.EnumWindows(enum_proc(visit), 0)
    return found[0] if found else None


def _load_icon(user32, ctypes, size):
    '''
    Load main-icon.ico at `size`, picking the closest size it holds.

    `as_file` rather than a `__file__`-relative path so this keeps working if
    psivideo is installed as a zipped wheel, in which case the icon is
    unpacked to a temporary file for the moment it takes Windows to read it.
    The handle outlives the file: LoadImage copies the image into the process.
    '''
    icon = (
        importlib.resources.files('psivideo')
        .joinpath('icons')
        .joinpath('main-icon.ico')
    )
    with importlib.resources.as_file(icon) as path:
        handle = user32.LoadImageW(None, str(path), IMAGE_ICON, size[0],
                                   size[1], LR_LOADFROMFILE)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    return handle
