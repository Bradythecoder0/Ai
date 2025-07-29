#!/usr/bin/env python3
"""
Harvey AI Assistant - Complete Version
A voice-controlled AI assistant with multiple HUD interfaces and trading capabilities
"""

import os
import time
import threading
import tkinter as tk
from tkinter import Canvas
import webbrowser
import requests
import random
import re

# Try to import required modules, install if missing
def install_and_import(package, pip_name=None):
    if pip_name is None:
        pip_name = package
    try:
        return __import__(package)
    except ImportError:
        print(f"Installing {pip_name}...")
        os.system(f"pip3 install {pip_name} --break-system-packages")
        return __import__(package)

# Install and import required packages
pyttsx3 = install_and_import('pyttsx3')
sr = install_and_import('speech_recognition', 'SpeechRecognition')
yf = install_and_import('yfinance')
psutil = install_and_import('psutil')

# Try to import trading API (optional)
try:
    tradeapi = install_and_import('alpaca_trade_api', 'alpaca-trade-api')
except:
    tradeapi = None
    print("Alpaca trading API not available - trading features disabled")

# Try to install PyAudio (often problematic)
try:
    import pyaudio
except ImportError:
    print("Installing PyAudio...")
    os.system("pip3 install pyaudio --break-system-packages")
    try:
        import pyaudio
    except ImportError:
        print("PyAudio installation failed - using fallback audio")

# ========== SECTION: VOICE ENGINE ==========
def init_voice_engine():
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 175)
        engine.setProperty('volume', 1.0)
        voices = engine.getProperty('voices')
        if voices and len(voices) > 0:
            # Try to use a female voice if available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            else:
                engine.setProperty('voice', voices[0].id)
        print(f"✓ Voice engine initialized successfully")
        return engine
    except Exception as e:
        print(f"✗ Error initializing voice engine: {e}")
        return None

engine = init_voice_engine()

def speak(text):
    print(f"Harvey: {text}")
    if engine:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"Error speaking: {e}")
    else:
        print("Voice engine not available")

# ========== SECTION: BASE HUD CLASS ==========
class BaseHUD:
    def __init__(self, root, bg="#000000"):
        self.root = root
        self.root.configure(bg=bg)
        self.root.geometry("1280x720")
        self.root.title("Harvey AI Assistant")
        self.canvas = Canvas(root, width=1280, height=720, bg=bg, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
    
    def destroy(self):
        self.canvas.destroy()
    
    def update_status(self, msg):
        # Base implementation - can be overridden
        print(f"Status: {msg}")

# ========== SECTION: ALPACA KEY LOADING ==========
def load_alpaca_keys():
    try:
        if os.path.exists("alpaca_keys.txt"):
            with open("alpaca_keys.txt") as f:
                lines = f.read().splitlines()
                if len(lines) >= 2 and "YOUR_ALPACA" not in lines[0]:
                    return lines[0], lines[1]
        return None, None
    except Exception as e:
        print("Could not load Alpaca keys:", e)
        return None, None

ALPACA_API_KEY, ALPACA_SECRET_KEY = load_alpaca_keys()
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # Paper trading for safety

if ALPACA_API_KEY and ALPACA_SECRET_KEY and tradeapi:
    try:
        api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')
        print("✓ Alpaca API initialized")
    except:
        api = None
        print("✗ Alpaca API initialization failed")
else:
    api = None
    print("✓ Trading disabled (no API keys or module)")

trading_active = False

def get_signal(symbol="AAPL"):
    if not api:
        return "HOLD"
    try:
        # Use yfinance as backup for price data since Alpaca might have issues
        stock = yf.Ticker(symbol)
        hist = stock.history(period="5d", interval="5m")
        if hist.empty or len(hist) < 20:
            return "HOLD"
        closes = hist['Close'].tolist()
        if len(closes) < 20:
            return "HOLD"
        short_ma = sum(closes[-5:]) / 5
        long_ma = sum(closes[-20:]) / 20
        if short_ma > long_ma:
            return "BUY"
        elif short_ma < long_ma:
            return "SELL"
        else:
            return "HOLD"
    except Exception as e:
        print(f"Error getting signal: {e}")
        return "HOLD"

def trade(symbol="AAPL", hud=None):
    if not api:
        msg = "Alpaca API not initialized."
        print(msg)
        if hud:
            hud.update_status(msg)
        return
    
    signal = get_signal(symbol)
    position = None
    try:
        position = api.get_position(symbol)
    except:
        pass  # No position

    try:
        if signal == "BUY" and not position:
            api.submit_order(
                symbol=symbol,
                qty=1,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            msg = f"Bought {symbol}"
        elif signal == "SELL" and position:
            api.submit_order(
                symbol=symbol,
                qty=abs(int(float(position.qty))),
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            msg = f"Sold {symbol}"
        else:
            msg = f"No action taken. Signal: {signal}"
    except Exception as e:
        msg = f"Trading error: {e}"
    
    print(msg)
    if hud:
        hud.update_status(msg)

def trading_loop(hud):
    global trading_active
    while trading_active:
        trade("AAPL", hud)
        time.sleep(300)  # Every 5 minutes

# ========== SECTION: HARVEY HUD ==========
class HarveyHUD(BaseHUD):
    def __init__(self, root):
        super().__init__(root, bg="#10131a")
        # Sleek neon Harvey name
        self.canvas.create_text(640, 90, text="HARVEY", font=("Arial", 56, "bold"), fill="#00f0ff", anchor="center")
        # Sleek neon ring
        self.ring_angle = 0
        self.ring = self.canvas.create_arc(420, 170, 860, 610, start=0, extent=330, style='arc', outline="#00f0ff", width=12)
        self.animate_ring()
        # Subtle pulse
        self.pulse = self.canvas.create_oval(520, 270, 760, 510, outline="#00f0ff", width=2)
        self.pulse_dir = 1
        self.pulse_radius = 0
        self.animate_pulse()
        # Glass-style info panels
        self.info_bg = self.canvas.create_rectangle(440, 340, 840, 420, fill="#1a2a3a", outline="#00f0ff", width=2)
        self.info_text = self.canvas.create_text(640, 380, text="Awaiting command...", font=("Arial", 22, "bold"), fill="#00fff7")
        # Floating system stats
        self.cpu_panel = self._glass_panel(180, 600, "CPU", "#00ffcc")
        self.ram_panel = self._glass_panel(180, 650, "RAM", "#00ffcc")
        self.weather_panel = self._glass_panel(1100, 600, "Weather", "#00ffcc")
        self.trading_panel = self._glass_panel(1100, 650, "AAPL", "#00ffcc")
        self.update_system_stats()
        self.update_weather()
        self.update_trading_info()

    def _glass_panel(self, x, y, label, color):
        bg = self.canvas.create_rectangle(x-70, y-20, x+70, y+20, fill="#1a2a3a", outline=color, width=2)
        text = self.canvas.create_text(x, y, text=f"{label}: --", font=("Arial", 16, "bold"), fill=color)
        return (bg, text)

    def animate_ring(self):
        self.canvas.itemconfig(self.ring, start=self.ring_angle)
        self.ring_angle = (self.ring_angle + 2) % 360
        self.root.after(20, self.animate_ring)

    def animate_pulse(self):
        # Subtle breathing effect
        r = 120 + self.pulse_radius
        self.canvas.coords(self.pulse, 640 - r, 390 - r, 640 + r, 390 + r)
        self.pulse_radius += self.pulse_dir
        if self.pulse_radius > 10 or self.pulse_radius < 0:
            self.pulse_dir *= -1
        self.root.after(40, self.animate_pulse)

    def update_status(self, msg):
        self.canvas.itemconfig(self.info_text, text=msg)

    def update_system_stats(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            self.canvas.itemconfig(self.cpu_panel[1], text=f"CPU: {cpu}%")
            self.canvas.itemconfig(self.ram_panel[1], text=f"RAM: {ram}%")
        except Exception as e:
            print(f"Error updating system stats: {e}")
        self.root.after(2000, self.update_system_stats)

    def update_weather(self):
        try:
            r = requests.get("https://wttr.in/?format=1", timeout=3)
            weather = r.text.strip()
        except Exception:
            weather = "N/A"
        self.canvas.itemconfig(self.weather_panel[1], text=f"Weather: {weather}")
        self.root.after(600000, self.update_weather)

    def update_trading_info(self):
        try:
            stock = yf.Ticker("AAPL")
            price = stock.history(period="1d", interval="1m")['Close'][-1]
            self.canvas.itemconfig(self.trading_panel[1], text=f"AAPL: ${price:.2f}")
        except Exception:
            self.canvas.itemconfig(self.trading_panel[1], text="AAPL: --")
        self.root.after(10000, self.update_trading_info)

# ========== SECTION: UPGRADED HUDS ==========
class MaximaHUD(BaseHUD):
    def __init__(self, root):
        super().__init__(root, bg="#0a2233")
        self.canvas.create_text(640, 120, text="MAXIMA", font=("Arial", 48, "bold"), fill="#00ffff")
        self.canvas.create_rectangle(440, 200, 840, 500, outline="#00ffff", width=4)
        self.canvas.create_text(640, 220, text="AI Optimization Engine", font=("Arial", 24), fill="#00ffff")
        # Status text
        self.status_text = self.canvas.create_text(640, 350, text="Awaiting command...", font=("Arial", 18), fill="#00ffff")
        # Unique: Animated glowing ring
        self.angle = 0
        self.ring = self.canvas.create_arc(500, 260, 780, 540, start=0, extent=270, style='arc', outline="#00ffff", width=8)
        self.animate_ring()

    def animate_ring(self):
        self.canvas.itemconfig(self.ring, start=self.angle)
        self.angle = (self.angle + 7) % 360
        self.root.after(40, self.animate_ring)
    
    def update_status(self, msg):
        self.canvas.itemconfig(self.status_text, text=msg)

class ArcHUD(BaseHUD):
    def __init__(self, root):
        super().__init__(root, bg="#2a1033")
        self.canvas.create_text(640, 120, text="ARC", font=("Arial", 48, "bold"), fill="#ff00ff")
        # Status text
        self.status_text = self.canvas.create_text(640, 200, text="Awaiting command...", font=("Arial", 18), fill="#ff00ff")
        # Unique: Digital clock with glowing effect
        self.clock_text = self.canvas.create_text(640, 320, text="", font=("Arial", 44, "bold"), fill="#ff00ff")
        self.canvas.create_oval(540, 220, 740, 420, outline="#ff00ff", width=6)
        self.update_clock()

    def update_clock(self):
        now = time.strftime("%H:%M:%S")
        self.canvas.itemconfig(self.clock_text, text=f"System Time: {now}")
        self.root.after(1000, self.update_clock)
    
    def update_status(self, msg):
        self.canvas.itemconfig(self.status_text, text=msg)

class PrinterHUD(BaseHUD):
    def __init__(self, root):
        super().__init__(root, bg="#332a10")
        self.canvas.create_text(640, 120, text="PRINTER", font=("Arial", 48, "bold"), fill="#ffcc00")
        # Status text
        self.status_text = self.canvas.create_text(640, 200, text="Awaiting command...", font=("Arial", 18), fill="#ffcc00")
        # Unique: Print queue simulation with progress bar
        self.queue = ["Job A", "Job B", "Job C"]
        self.queue_text = self.canvas.create_text(640, 320, text="", font=("Arial", 24), fill="#ffcc00")
        self.progress = self.canvas.create_rectangle(440, 400, 440, 440, fill="#ffcc00", outline="")
        self.update_queue()

    def update_queue(self):
        queue_str = "Print Queue:\n" + "\n".join(self.queue)
        self.canvas.itemconfig(self.queue_text, text=queue_str)
        progress_len = 400 if not self.queue else 400 - len(self.queue) * 100
        self.canvas.coords(self.progress, 440, 400, 440 + progress_len, 440)
        self.root.after(3000, self.simulate_print)

    def simulate_print(self):
        if self.queue:
            self.queue.pop(0)
        self.update_queue()
    
    def update_status(self, msg):
        self.canvas.itemconfig(self.status_text, text=msg)

class DayTraderHUD(BaseHUD):
    def __init__(self, root):
        super().__init__(root, bg="#102a1a")
        self.canvas.create_text(640, 120, text="DAY TRADER", font=("Arial", 48, "bold"), fill="#00ff99")
        # Status text
        self.status_text = self.canvas.create_text(640, 200, text="Awaiting command...", font=("Arial", 18), fill="#00ff99")
        # Unique: Live AAPL price and trading signal
        self.price_text = self.canvas.create_text(640, 320, text="AAPL: --", font=("Arial", 36), fill="#00ff99")
        self.signal_text = self.canvas.create_text(640, 400, text="Signal: --", font=("Arial", 24), fill="#00ff99")
        self.update_price_and_signal()

    def get_trading_signal(self):
        try:
            stock = yf.Ticker("AAPL")
            hist = stock.history(period="5d", interval="5m")
            close = hist['Close']
            short_ma = close.rolling(window=5).mean()
            long_ma = close.rolling(window=20).mean()
            if short_ma.iloc[-1] > long_ma.iloc[-1]:
                return "BUY"
            elif short_ma.iloc[-1] < long_ma.iloc[-1]:
                return "SELL"
            else:
                return "HOLD"
        except Exception as e:
            print("[Signal Error]", e)
            return "N/A"

    def update_price_and_signal(self):
        try:
            stock = yf.Ticker("AAPL")
            price = stock.history(period="1d", interval="1m")['Close'][-1]
            self.canvas.itemconfig(self.price_text, text=f"AAPL: ${price:.2f}")
            signal = self.get_trading_signal()
            self.canvas.itemconfig(self.signal_text, text=f"Signal: {signal}")
        except Exception:
            self.canvas.itemconfig(self.price_text, text="AAPL: --")
            self.canvas.itemconfig(self.signal_text, text="Signal: --")
        self.root.after(10000, self.update_price_and_signal)
    
    def update_status(self, msg):
        self.canvas.itemconfig(self.status_text, text=msg)

# ========== SECTION: CONTROLLER ==========
class HarveyController:
    def __init__(self, root):
        self.root = root
        self.current_hud = None
        self.huds = {
            "harvey": HarveyHUD,
            "maxima": MaximaHUD,
            "arc": ArcHUD,
            "printer": PrinterHUD,
            "day trader": DayTraderHUD
        }
        self.show_hud("harvey")

    def show_hud(self, hud_name):
        if self.current_hud:
            self.current_hud.destroy()
        hud_class = self.huds.get(hud_name.lower())
        if hud_class:
            self.current_hud = hud_class(self.root)
            self.current_hud.update_status(f"{hud_name.upper()} HUD loaded.")
        else:
            speak("HUD not found.")

    def update_status(self, msg):
        if self.current_hud:
            self.current_hud.update_status(msg)

# ========== SECTION: VOICE COMMANDS ==========
def init_speech_recognition():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    recognizer.operation_timeout = None
    recognizer.phrase_threshold = 0.3
    recognizer.non_speaking_duration = 0.8
    
    # List microphones and let you pick the right one
    try:
        mic_list = sr.Microphone.list_microphone_names()
        print("\n=== Available microphones ===")
        for idx, name in enumerate(mic_list):
            print(f"{idx}: {name}")
        print("=" * 40)
    except Exception as e:
        print(f"Error listing microphones: {e}")
        mic_list = []

    # Try to find the best microphone
    mic = None
    MIC_INDEX = None
    
    # First try default microphone
    try:
        mic = sr.Microphone()
        print("✓ Using default microphone")
    except Exception as e:
        print(f"Error with default microphone: {e}")
        
        # Try to find a working microphone
        if mic_list:
            for idx in range(len(mic_list)):
                try:
                    test_mic = sr.Microphone(device_index=idx)
                    # Test the microphone
                    with test_mic as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.1)
                    mic = test_mic
                    MIC_INDEX = idx
                    print(f"✓ Using microphone {idx}: {mic_list[idx]}")
                    break
                except Exception as mic_error:
                    print(f"Microphone {idx} failed: {mic_error}")
                    continue
    
    if not mic:
        print("WARNING: No working microphone found!")
        mic = sr.Microphone()  # Fallback
    
    return recognizer, mic

recognizer, mic = init_speech_recognition()
wake_words = ["harvey", "wake up", "i'm home", "jarvis"]
active_project = None

def listen_for_command():
    if not mic:
        print("No microphone available")
        return ""
        
    try:
        with mic as source:
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            print("Listening... (speak now)")
            
            try:
                # Increased timeout and phrase time limit
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
                print("Audio captured, processing...")
            except sr.WaitTimeoutError:
                print("Listening timed out - no speech detected.")
                return ""
                
        try:
            print("Recognizing speech...")
            command = recognizer.recognize_google(audio, language='en-US').lower()
            print(f"[User]: {command}")
            return command
        except sr.UnknownValueError:
            print("Could not understand audio - please speak clearly.")
            return ""
        except sr.RequestError as e:
            print(f"Google Speech Recognition error: {e}")
            return ""
    except Exception as e:
        print(f"Error in listen_for_command: {e}")
        return ""

def handle_command(command, controller):
    global active_project, trading_active

    if "status" in command:
        controller.update_status("Systems normal. All functions green.")
        speak("All systems are running within optimal parameters.")

    elif "show harvey" in command or "main hud" in command:
        active_project = "HARVEY"
        controller.show_hud("harvey")
        speak("Here's the main Harvey interface.")

    elif "show maxima" in command:
        active_project = "MAXIMA"
        controller.show_hud("maxima")
        speak("Here's Project MAXIMA.")

    elif "show arc" in command:
        active_project = "ARC"
        controller.show_hud("arc")
        speak("Here's Project ARC.")

    elif "show printer" in command:
        active_project = "PRINTER"
        controller.show_hud("printer")
        speak("Here's Project PRINTER.")

    elif "day trader" in command or "start trading" in command:
        active_project = "DAY TRADER"
        controller.show_hud("day trader")
        controller.update_status("Day Trading HUD engaged. Alpaca trading started.")
        speak("Launching Day Trading Engine with Alpaca.")
        if not trading_active and api:
            trading_active = True
            threading.Thread(target=trading_loop, args=(controller.current_hud,), daemon=True).start()

    elif "stop trading" in command:
        trading_active = False
        controller.update_status("Trading stopped.")
        speak("Trading stopped.")

    elif "open" in command:
        match = re.search(r"open (.+)", command)
        if match:
            site = match.group(1).strip()
            if not site.startswith("http"):
                if "." not in site:
                    site += ".com"
                site = "https://" + site
            speak(f"Opening {site}")
            webbrowser.open(site)
            controller.update_status(f"Opened {site}")
        else:
            speak("Please specify a website to open.")

    elif "shut down" in command:
        controller.update_status("Shutting down...")
        speak("System shutting down now.")
        exit()

    else:
        controller.update_status("Command not recognized.")
        speak("Sorry, I didn't catch that.")

# ========== SECTION: STARTUP + MAIN LOOP ==========
def create_alpaca_keys_file():
    """Create alpaca keys file if it doesn't exist"""
    if not os.path.exists("alpaca_keys.txt"):
        with open("alpaca_keys.txt", "w") as f:
            f.write("YOUR_ALPACA_API_KEY_HERE\n")
            f.write("YOUR_ALPACA_SECRET_KEY_HERE\n")
        print("✓ Created alpaca_keys.txt template")
        print("  Edit this file with your Alpaca API credentials for trading")

def launch_harvey():
    print("=" * 50)
    print("🤖 HARVEY AI ASSISTANT STARTING UP 🤖")
    print("=" * 50)
    
    # Create config files
    create_alpaca_keys_file()
    
    # Test audio
    if engine:
        print("✓ Text-to-speech ready")
    else:
        print("✗ Text-to-speech not available")
        
    if mic:
        print("✓ Microphone ready")
    else:
        print("✗ Microphone not available")
    
    print("\nStarting GUI...")
    root = tk.Tk()
    controller = HarveyController(root)

    def voice_loop():
        print("Voice loop started. Say 'Harvey' to wake me up!")
        speak("Harvey AI system online. Say Harvey to activate voice commands.")
        
        while True:
            try:
                cmd = listen_for_command()
                if cmd and any(word in cmd for word in wake_words):
                    speak("Yes sir?")
                    print("Wake word detected! Listening for command...")
                    full_command = listen_for_command()
                    if full_command:
                        handle_command(full_command, controller)
                    else:
                        speak("I didn't catch that. Please try again.")
                elif cmd:
                    print(f"Heard: '{cmd}' but no wake word detected.")
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
            except Exception as e:
                print(f"Error in voice loop: {e}")
                time.sleep(1)

    # Start voice recognition in background
    threading.Thread(target=voice_loop, daemon=True).start()
    
    print("\n🎤 HARVEY IS LISTENING 🎤")
    print("Say 'Harvey' followed by your command!")
    print("Available commands:")
    print("- 'status' - Check system status")
    print("- 'show harvey/maxima/arc/printer' - Switch HUDs")
    print("- 'day trader' - Start trading interface")
    print("- 'open [website]' - Open websites")
    print("- 'shut down' - Exit Harvey")
    print("=" * 50)
    
    # Start GUI main loop
    root.mainloop()

if __name__ == "__main__":
    try:
        launch_harvey()
    except Exception as e:
        import traceback
        print("[HARVEY ERROR]:", e)
        traceback.print_exc()
        input("Press Enter to close...")