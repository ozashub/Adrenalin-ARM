import os
import sys
import subprocess
import threading
import time
import ctypes
import queue
import winreg
import json
import pyaudio

try:
    import pystray
    from PIL import Image
    HAS_TRAY = True
except:
    HAS_TRAY=False

from rapidfuzz import fuzz
from vosk import Model, KaldiRecognizer, SetLogLevel

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOLDOWN_SECONDS=0.3

tray_icon = None
last_trigger_time=0.0
is_listening = True
vosk_model = None

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

def init_vosk():
    global vosk_model
    model_path = os.path.join(SCRIPT_DIR, "../dependencies/vosk")
    
    if not os.path.exists(model_path):
        show_error_and_exit(f"Vosk model not found at: {model_path}\nDownload from https://alphacephei.com/vosk/models")
    
    SetLogLevel(-1)
    print('Loading voice model...', end='', flush=True)
    vosk_model=Model(model_path)
    print(' OK')

def matches_trigger(txt):
    if not txt:
        return False
    
    if len(txt.split()) < 2:
        return False
    
    noise_words = {"the", "a", "and", "to", "is", "it", "that", "this", "for", "huh", "with"}
    if txt.lower() in noise_words:
        return False
    
    txt_lower=txt.lower()
    if not any(word in txt_lower for word in ["start", "launch", 'fire', "adrenalin", "macro", 'mackarel']):
        return False
    
    triggers=[
        "start the macro",
        'start the mackarel',
        "launch macro",
        'fire up the macro',
        'start adrenalin',
        'open the macro'
    ]

    fuzz_thres=85
    
    for trigger in triggers:
        score=fuzz.partial_ratio(txt, trigger)
        if score>=fuzz_thres:
            print(f"[MATCH] '{txt}' ≈ '{trigger}' ({score})")
            return True
    
    return False

def listen_for_speech():
    global last_trigger_time
    
    p=pyaudio.PyAudio()
    
    print('Detecting microphone...', end='', flush=True)
    device_idx = p.get_default_input_device_info()['index']
    device_info=p.get_device_info_by_index(device_idx)
    mic_name = device_info['name']
    print(f' OK ({mic_name})')
    
    stream = p.open(format=pyaudio.paInt16,
                   channels=1,
                   rate=16000,
                   input=True,
                   frames_per_buffer=4000)
    
    rec = KaldiRecognizer(vosk_model, 16000)
    rec.SetWords(False)
    
    print('Status... OK')
    
    while is_listening:
        data = stream.read(4000, exception_on_overflow=False)
        
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            txt = result.get("text", "").strip()
            
            if txt:
                print(f"[HEARD] {txt}")
                
                now = time.time()
                if now - last_trigger_time >= COOLDOWN_SECONDS:
                    if matches_trigger(txt):
                        launch_app()
                        last_trigger_time = now
    
    stream.stop_stream()
    stream.close()
    p.terminate()

def is_app_running():
    exe_name=os.path.basename(APP_PATH)
    result = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {exe_name}"], 
                          capture_output=True, text=True, timeout=1)
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
                       creationflags=0x08)
    
    threading.Thread(target=do_launch, daemon=True).start()
    last_trigger_time=time.time()

def hide_console():
    kernel32=ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    h=kernel32.GetConsoleWindow()
    if h:
        user32.ShowWindow(h, 0)

def show_console():
    kernel32 = ctypes.windll.kernel32
    user32=ctypes.windll.user32
    h = kernel32.GetConsoleWindow()
    if h:
        user32.ShowWindow(h, 9)
        user32.SetForegroundWindow(h)

def monitor_console_window():
    kernel32=ctypes.windll.kernel32
    user32=ctypes.windll.user32
    SW_HIDE=0
    
    while is_listening:
        h=kernel32.GetConsoleWindow()
        if h and user32.IsIconic(h):
            user32.ShowWindow(h, SW_HIDE)
        time.sleep(0.1)

def create_tray_icon():
    global tray_icon
    
    if not HAS_TRAY:
        return None
    
    icon_path=os.path.join(SCRIPT_DIR, "etc/icon.ico")
    img = Image.open(icon_path)
    
    def on_start_click(icon, item):
        launch_app()
    
    def on_show_click(icon, item):
        show_console()
    
    def on_quit_click(icon, item):
        global is_listening
        is_listening=False
        icon.visible = False
        icon.stop()
        os._exit(0)
    
    menu=pystray.Menu(
        pystray.MenuItem('Start Macro', on_start_click),
        pystray.MenuItem("Show Console", on_show_click, default=True),
        pystray.MenuItem('Quit', on_quit_click)
    )
    
    icon = pystray.Icon("AdrenalinArm", img, 'Adrenalin Arm', menu)
    tray_icon=icon
    return icon

def main():
    init_vosk()
    icon=create_tray_icon()
    
    listen_thread = threading.Thread(target=listen_for_speech, daemon=True)
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