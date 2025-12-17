import os
import sys
import subprocess
import threading
import time
import ctypes
from ctypes import wintypes
import queue
import winreg

try:
    import pystray
    from PIL import Image
    HAS_TRAY = True
except:
    HAS_TRAY=False

import speech_recognition as sr
from rapidfuzz import fuzz

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOLDOWN_SECONDS=0.3

# wsg chat, disclaimer: with the assist of Claude I was able to make this easily. Anything that looks odd is cause ts was written with AI however is fully functional. Edit how you want.

tray_icon = None
last_trigger_time=0.0
is_listening = True
audio_q=queue.Queue()

def get_app_path():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Adrenalin')
    path, _ = winreg.QueryValueEx(key, 'ExecutablePath')
    winreg.CloseKey(key)
    if os.path.isfile(path):
        return path
    return None

def show_error_and_exit(msg):
    ctypes.windll.user32.MessageBoxW(None, msg, "Error", 0x10)
    sys.exit(1)

APP_PATH=get_app_path()
if not APP_PATH:
    show_error_and_exit("Could not find Adrenalin. Please launch Adrenalin first to set the location.")

def recognize_speech(audio):
    recognizer = sr.Recognizer()
    try:
        text=recognizer.recognize_google(audio, language="en-US")
        return text.lower().strip()
    except (sr.UnknownValueError, sr.RequestError):
        return None

def matches_trigger_phrase(txt):
    if not txt or ("start" not in txt and "launch" not in txt):
        return False
    
    # triggers, change how you want the macro to be triggered
    triggers = [
        "start the macro",
        'start the mackarel', # i got a UK accent gng 😭
        "launch macro",
        "fire up the macro",
        'start adrenalin'
    ]

    fuzz_thres = 85  # 85 seems best, lower = more false positives but is flexible on the triggers, higher = more strict, the number you see when you speak in the console is the threshold value.
    
    for trigger in triggers:
        score = fuzz.partial_ratio(txt, trigger)
        if score >= fuzz_thres:
            print(f"[MATCH] '{txt}' ≈ '{trigger}' ({score})")
            return True
    
    return False

def listen_for_speech():
    global last_trigger_time
    
    recognizer=sr.Recognizer()
    
    recognizer.energy_threshold = 50
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.35
    recognizer.dynamic_energy_ratio = 1.4
    recognizer.pause_threshold = 0.5
    recognizer.phrase_threshold = 0.2
    recognizer.non_speaking_duration = 0.3
    
    with sr.Microphone(sample_rate=16000) as mic:
        import pyaudio
        p = pyaudio.PyAudio()
        
        print('Detecting microphone...', end='', flush=True)
        device_idx = mic.device_index if mic.device_index else p.get_default_input_device_info()['index']
        device_info=p.get_device_info_by_index(device_idx)
        mic_name = device_info['name']
        p.terminate()
        print(f' OK ({mic_name})')
        
        print('Calibrating microphone...', end='', flush=True)
        recognizer.adjust_for_ambient_noise(mic, duration=4)
        print(' OK')
        
        while is_listening:
            audio = recognizer.listen(mic, timeout=None, phrase_time_limit=8)
            threading.Thread(target=process_audio, args=(audio,), daemon=True).start()

def process_audio(audio):
    global last_trigger_time
    
    txt=recognize_speech(audio)
    if not txt:
        return
    
    print(f"[HEARD] {txt}")
    
    now = time.time()
    if now - last_trigger_time < COOLDOWN_SECONDS:
        return
    
    if matches_trigger_phrase(txt):
        launch_app()

def is_app_running():
    exe_name = os.path.basename(APP_PATH)
    result=subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {exe_name}"], 
                          capture_output=True, text=True, timeout=2)
    return exe_name.lower() in result.stdout.lower()

def launch_app():
    global last_trigger_time
    
    print('Launching Adrenalin...', end='', flush=True)
    
    if is_app_running():
        print(' ERR: App already running, skipping launch')
        ctypes.windll.user32.MessageBeep(0x10)
        return
    
    print(' OK')
    def do_launch():
        subprocess.Popen([APP_PATH, "-disableshowonstart"],
                       creationflags=0x08)  # needed for detaching
    
    threading.Thread(target=do_launch, daemon=True).start()
    last_trigger_time = time.time()

def hide_console():
    kernel32 = ctypes.windll.kernel32
    user32=ctypes.windll.user32
    h = kernel32.GetConsoleWindow()
    if h:
        user32.ShowWindow(h, 0)

def show_console():
    kernel32=ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    h=kernel32.GetConsoleWindow()
    if h:
        user32.ShowWindow(h, 9)
        user32.SetForegroundWindow(h)

def monitor_console_window():
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    SW_MINIMIZE = 6
    SW_HIDE = 0
    
    class WINDOWPLACEMENT(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_uint),
            ("flags", ctypes.c_uint),
            ("showCmd", ctypes.c_uint),
            ("ptMinPosition", wintypes.POINT),
            ("ptMaxPosition", wintypes.POINT),
            ("rcNormalPosition", wintypes.RECT)
        ]
    
    while is_listening:
        h = kernel32.GetConsoleWindow()
        if h:
            placement = WINDOWPLACEMENT()
            placement.length = ctypes.sizeof(WINDOWPLACEMENT)
            if user32.GetWindowPlacement(h, ctypes.byref(placement)):
                if placement.showCmd == SW_MINIMIZE:
                    user32.ShowWindow(h, SW_HIDE)
        time.sleep(0.5)

def create_tray_icon():
    global tray_icon
    
    if not HAS_TRAY:
        return None
    
    icon_path = os.path.join(SCRIPT_DIR, "icon.ico")
    img = Image.open(icon_path)
    
    def on_start_click(icon, item):
        launch_app()
    
    def on_show_click(icon, item):
        show_console()
    
    def on_quit_click(icon, item):
        global is_listening
        is_listening = False
        icon.visible=False
        icon.stop()
        os._exit(0)
    
    menu = pystray.Menu(
        pystray.MenuItem('Start Macro', on_start_click),
        pystray.MenuItem("Show Console", on_show_click, default=True),
        pystray.MenuItem('Quit', on_quit_click)
    )
    
    icon=pystray.Icon("AdrenalinArm", img, 'Adrenalin Arm', menu)
    tray_icon = icon
    return icon

def main():
    hide_console()
    icon = create_tray_icon()
    
    listen_thread=threading.Thread(target=listen_for_speech, daemon=True)
    listen_thread.start()
    
    monitor_thread=threading.Thread(target=monitor_console_window, daemon=True)
    monitor_thread.start()
    
    if icon:
        icon.run()
    else:
        while is_listening:
            time.sleep(1)

if __name__ == "__main__":
    main()