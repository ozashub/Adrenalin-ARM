import os
import sys
import subprocess
import threading
import time
import ctypes
import queue
import winreg

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY=True
except:
    HAS_TRAY=False

import speech_recognition as sr
from rapidfuzz import fuzz

SCRIPT_DIR=os.path.dirname(os.path.abspath(__file__))
COOLDOWN_SECONDS=1.5

tray_icon=None
last_trigger_time=0.0
is_listening=True
audio_q=queue.Queue()

def get_app_path():
    try:
        key=winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Adrenalin")
        path, _=winreg.QueryValueEx(key, "ExecutablePath")
        winreg.CloseKey(key)
        if os.path.isfile(path):
            return path
    except:
        pass
    return None

def show_error_and_exit(msg):
    ctypes.windll.user32.MessageBoxW(None, msg, "Error", 0x10)
    sys.exit(1)

APP_PATH=get_app_path()
if not APP_PATH:
    show_error_and_exit("Could not find Adrenalin. Please launch Adrenalin first to set the location.")

def recognize_speech(audio):
    try:
        recognizer=sr.Recognizer()
        text=recognizer.recognize_google(audio, language="en-US")
        return text.lower().strip()
    except:
        return None

def matches_trigger_phrase(text):
    if not text or ("start" not in text and "launch" not in text):
        return False
    
    triggers=[
        "start the macro",
        "start macro", 
        "launch macro",
        "fire up the macro",
        "start adrenalin"
    ]
    
    for trigger in triggers:
        score=fuzz.partial_ratio(text, trigger)
        if score >= 80:  # 80 seems to work best idk
            print(f"[MATCH] '{text}' ≈ '{trigger}' ({score})")
            return True
    
    return False

def listen_for_speech():
    global last_trigger_time
    
    recognizer=sr.Recognizer()
    
    # aggressive settings to catch everything
    recognizer.energy_threshold=300
    recognizer.dynamic_energy_threshold=True
    recognizer.dynamic_energy_adjustment_damping=0.15
    recognizer.dynamic_energy_ratio=1.5
    recognizer.pause_threshold=0.8
    recognizer.phrase_threshold=0.3
    recognizer.non_speaking_duration=0.5
    
    with sr.Microphone(sample_rate=16000) as mic:
        try:
            import pyaudio
            p=pyaudio.PyAudio()
            
            device_idx=mic.device_index if mic.device_index else p.get_default_input_device_info()['index']
            device_info=p.get_device_info_by_index(device_idx)
            mic_name=device_info['name']
            p.terminate()
            
            print(f"Listening to: {mic_name}")
        except:
            print("Listening to: Default Microphone")
        
        print("Calibrating mic")
        recognizer.adjust_for_ambient_noise(mic, duration=2)
        print("Calibrated.")
        
        while is_listening:
            try:
                audio=recognizer.listen(mic, timeout=None, phrase_time_limit=10)
                threading.Thread(target=process_audio, args=(audio,), daemon=True).start()
            except sr.WaitTimeoutError:
                continue
            except:
                time.sleep(0.1)

def process_audio(audio):
    global last_trigger_time
    
    text=recognize_speech(audio)
    if not text:
        return
    
    print(f"[HEARD] {text}")
    
    now=time.time()
    if now - last_trigger_time < COOLDOWN_SECONDS:
        return
    
    if matches_trigger_phrase(text):
        launch_app()

def is_app_running():
    exe_name=os.path.basename(APP_PATH)
    try:
        result=subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {exe_name}"], 
                              capture_output=True, text=True, timeout=2)
        return exe_name.lower() in result.stdout.lower()
    except:
        return False

def launch_app():
    global last_trigger_time
    
    if is_app_running():
        print("[DEBUG] App already running, skipping launch")
        ctypes.windll.user32.MessageBeep(0x10)
        return
    
    def do_launch():
        print("Macro launched")
        subprocess.Popen([APP_PATH, "-disableshowonstart"],
                       creationflags=0x08)  # no clue why but this fixes it
    
    threading.Thread(target=do_launch, daemon=True).start()
    last_trigger_time=time.time()

def hide_console():
    kernel32=ctypes.windll.kernel32
    user32=ctypes.windll.user32
    h=kernel32.GetConsoleWindow()
    if h:
        user32.ShowWindow(h, 0)

def show_console():
    kernel32=ctypes.windll.kernel32
    user32=ctypes.windll.user32
    h=kernel32.GetConsoleWindow()
    if h:
        user32.ShowWindow(h, 9)
        user32.SetForegroundWindow(h)


def create_tray_icon():
    global tray_icon
    
    if not HAS_TRAY:
        return None
    
    img=Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw=ImageDraw.Draw(img)
    draw.ellipse((4, 4, 60, 60), fill=(30, 144, 255, 255))
    
    def on_start_click(icon, item):
        launch_app()
    
    def on_show_click(icon, item):
        show_console()
    
    def on_quit_click(icon, item):
        global is_listening
        is_listening=False
        icon.visible=False
        icon.stop()
        os._exit(0)
    
    menu=pystray.Menu(
        pystray.MenuItem("Start Macro", on_start_click),
        pystray.MenuItem("Show Console", on_show_click, default=True),
        pystray.MenuItem("Quit", on_quit_click)
    )
    
    icon=pystray.Icon("AdrenalinArm", img, "Adrenalin Arm", menu)
    tray_icon=icon
    return icon

def main():
    hide_console()
    icon=create_tray_icon()
    
    listen_thread=threading.Thread(target=listen_for_speech, daemon=True)
    listen_thread.start()
    
    if icon:
        icon.run()
    else:
        while is_listening:
            time.sleep(1)

if __name__ == "__main__":
    main()