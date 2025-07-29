#!/usr/bin/env python3
"""
Harvey AI Assistant - Complete Fixed Version
A voice-controlled AI assistant with multiple HUD interfaces and trading capabilities
"""

import os
import time
import threading
import tkinter as tk
from tkinter import Canvas, messagebox
import webbrowser
import requests
import random
import re
import sys
import subprocess
import json
from datetime import datetime

# Auto-install required packages
def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--break-system-packages"])
        except:
            print(f"Could not install {package}")

# Try importing packages, install if missing
try:
    import pyttsx3
except ImportError:
    print("Installing pyttsx3...")
    install_package("pyttsx3")
    import pyttsx3

try:
    import speech_recognition as sr
except ImportError:
    print("Installing SpeechRecognition...")
    install_package("SpeechRecognition")
    import speech_recognition as sr

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    install_package("yfinance")
    import yfinance as yf

try:
    import psutil
except ImportError:
    print("Installing psutil...")
    install_package("psutil")
    import psutil

try:
    import alpaca_trade_api as tradeapi
except ImportError:
    print("Installing alpaca-trade-api...")
    install_package("alpaca-trade-api")
    import alpaca_trade_api as tradeapi

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
        return engine
    except Exception as e:
        print(f"Error initializing voice engine: {e}")
        return None

engine = init_voice_engine()

def speak(text):
    print(f"Harvey: {text}")
    if engine:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"Speech error: {e}")

# ========== SECTION: ALPACA KEY LOADING ==========
def load_alpaca_keys():
    try:
        if os.path.exists("alpaca_keys.txt"):
            with open("alpaca_keys.txt") as f:
                lines = f.read().splitlines()
                if len(lines) >= 2 and not lines[0].startswith("YOUR_"):
                    return lines[0], lines[1]
        return None, None
    except Exception as e:
        print("Could not load Alpaca keys:", e)
        return None, None

def create_alpaca_keys_file():
    """Create a template alpaca_keys.txt file"""
    if not os.path.exists("alpaca_keys.txt"):
        with open("alpaca_keys.txt", "w") as f:
            f.write("YOUR_ALPACA_API_KEY_HERE\n")
            f.write("YOUR_ALPACA_SECRET_KEY_HERE\n")
        print("Created alpaca_keys.txt template. Please add your real keys.")

create_alpaca_keys_file()
ALPACA_API_KEY, ALPACA_SECRET_KEY = load_alpaca_keys()
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # Paper trading for safety

if ALPACA_API_KEY and ALPACA_SECRET_KEY:
    try:
        api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')
    except:
        api = None
else:
    api = None

trading_active = False

def get_signal(symbol="AAPL"):
    """Get trading signal using technical analysis"""
    try:
        # Use yfinance for reliable data
        stock = yf.Ticker(symbol)
        hist = stock.history(period="5d", interval="5m")
        if hist.empty or len(hist) < 20:
            return "HOLD"
        
        closes = hist['Close'].tolist()
        short_ma = sum(closes[-5:]) / 5
        long_ma = sum(closes[-20:]) / 20
        
        if short_ma > long_ma * 1.01:  # 1% threshold
            return "BUY"
        elif short_ma < long_ma * 0.99:
            return "SELL"
        else:
            return "HOLD"
    except Exception as e:
        print(f"Error getting signal: {e}")
        return "HOLD"

def trade(symbol="AAPL", hud=None):
    """Execute trades based on signals"""
    if not api:
        msg = "Alpaca API not initialized. Check your keys."
        print(msg)
        if hud:
            hud.update_status(msg)
        return
    
    try:
        signal = get_signal(symbol)
        position = None
        
        try:
            position = api.get_position(symbol)
        except:
            pass  # No position
        
        if signal == "BUY" and not position:
            api.submit_order(
                symbol=symbol,
                qty=1,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            msg = f"Bought 1 share of {symbol}"
        elif signal == "SELL" and position:
            api.submit_order(
                symbol=symbol,
                qty=abs(int(float(position.qty))),
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            msg = f"Sold {position.qty} shares of {symbol}"
        else:
            msg = f"No action taken for {symbol}. Signal: {signal}"
        
        print(msg)
        if hud:
            hud.update_status(msg)
            
    except Exception as e:
        msg = f"Trading error: {e}"
        print(msg)
        if hud:
            hud.update_status(msg)

def trading_loop(hud):
    """Main trading loop"""
    global trading_active
    while trading_active:
        trade("AAPL", hud)
        time.sleep(300)  # Every 5 minutes

# ========== SECTION: BASE HUD CLASS ==========
class BaseHUD:
    def __init__(self, root, bg="#000000"):
        self.root = root
        self.root.configure(bg=bg)
        self.root.attributes('-topmost', True)
        
        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Set window size and position
        window_width = 1280
        window_height = 720
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.title("Harvey AI Assistant")
        
        # Create canvas
        self.canvas = Canvas(root, width=window_width, height=window_height, bg=bg, highlightthickness=0)
        self.canvas.pack()
        
        # Status text
        self.status_text = "System Online"
        
    def update_status(self, text):
        """Update status display"""
        self.status_text = text
        
    def clear_canvas(self):
        """Clear the canvas"""
        self.canvas.delete("all")

# ========== SECTION: HARVEY HUD ==========
class HarveyHUD(BaseHUD):
    def __init__(self, root):
        super().__init__(root, bg="#10131a")
        self.setup_ui()
        self.update_loop()
        
    def setup_ui(self):
        """Setup the Harvey HUD interface"""
        # Harvey title
        self.canvas.create_text(640, 90, text="HARVEY", 
                               font=("Segoe UI", 56, "bold"), 
                               fill="#00d4ff", tags="title")
        
        # Subtitle
        self.canvas.create_text(640, 140, text="AI ASSISTANT ONLINE", 
                               font=("Segoe UI", 16), 
                               fill="#ffffff", tags="subtitle")
        
        # Status area
        self.canvas.create_rectangle(50, 200, 1230, 250, 
                                   outline="#00d4ff", width=2, tags="status_box")
        
        # System stats area
        self.canvas.create_rectangle(50, 300, 600, 650, 
                                   outline="#00d4ff", width=2, tags="stats_box")
        
        # Commands area
        self.canvas.create_rectangle(650, 300, 1230, 650, 
                                   outline="#00d4ff", width=2, tags="commands_box")
        
        # Labels
        self.canvas.create_text(325, 320, text="SYSTEM STATISTICS", 
                               font=("Segoe UI", 14, "bold"), 
                               fill="#00d4ff", tags="stats_label")
        
        self.canvas.create_text(940, 320, text="AVAILABLE COMMANDS", 
                               font=("Segoe UI", 14, "bold"), 
                               fill="#00d4ff", tags="commands_label")
        
        # Command list
        commands = [
            "• 'Harvey' - Wake up",
            "• 'Switch to [hud name]' - Change interface",
            "• 'Open [website]' - Open website",
            "• 'What time is it' - Get current time",
            "• 'System stats' - Show system info",
            "• 'Stock price [symbol]' - Get stock price",
            "• 'Start trading' - Begin auto trading",
            "• 'Stop trading' - Stop auto trading",
            "• 'Shutdown' - Close Harvey"
        ]
        
        y_pos = 360
        for cmd in commands:
            self.canvas.create_text(670, y_pos, text=cmd, 
                                   font=("Segoe UI", 11), 
                                   fill="#ffffff", anchor="w", tags="command_text")
            y_pos += 30
    
    def update_loop(self):
        """Update the display every second"""
        self.update_display()
        self.root.after(1000, self.update_loop)
    
    def update_display(self):
        """Update dynamic content"""
        # Update status
        self.canvas.delete("status_text")
        self.canvas.create_text(640, 225, text=self.status_text, 
                               font=("Segoe UI", 12), 
                               fill="#ffffff", tags="status_text")
        
        # Update system stats
        self.canvas.delete("stats_data")
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            stats_text = [
                f"CPU Usage: {cpu_percent}%",
                f"Memory: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)",
                f"Disk: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)",
                f"Time: {datetime.now().strftime('%H:%M:%S')}",
                f"Date: {datetime.now().strftime('%Y-%m-%d')}",
                f"Trading: {'Active' if trading_active else 'Inactive'}"
            ]
            
            y_pos = 360
            for stat in stats_text:
                self.canvas.create_text(70, y_pos, text=stat, 
                                       font=("Segoe UI", 11), 
                                       fill="#ffffff", anchor="w", tags="stats_data")
                y_pos += 40
                
        except Exception as e:
            self.canvas.create_text(70, 360, text=f"Stats Error: {e}", 
                                   font=("Segoe UI", 11), 
                                   fill="#ff0000", anchor="w", tags="stats_data")

# ========== SECTION: OTHER HUD CLASSES ==========
class MaximaHUD(BaseHUD):
    def __init__(self, root):
        super().__init__(root, bg="#1a0d1a")
        self.setup_ui()
        
    def setup_ui(self):
        self.canvas.create_text(640, 90, text="MAXIMA", 
                               font=("Segoe UI", 56, "bold"), 
                               fill="#ff00ff")
        self.canvas.create_text(640, 140, text="AI OPTIMIZATION ENGINE", 
                               font=("Segoe UI", 16), 
                               fill="#ffffff")

class ArcHUD(BaseHUD):
    def __init__(self, root):
        super().__init__(root, bg="#0d1a0d")
        self.setup_ui()
        self.update_clock()
        
    def setup_ui(self):
        self.canvas.create_text(640, 90, text="ARC", 
                               font=("Segoe UI", 56, "bold"), 
                               fill="#00ff00")
        self.canvas.create_text(640, 140, text="DIGITAL CLOCK INTERFACE", 
                               font=("Segoe UI", 16), 
                               fill="#ffffff")
    
    def update_clock(self):
        self.canvas.delete("clock")
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        self.canvas.create_text(640, 300, text=current_time, 
                               font=("Segoe UI", 72, "bold"), 
                               fill="#00ff00", tags="clock")
        self.canvas.create_text(640, 400, text=current_date, 
                               font=("Segoe UI", 24), 
                               fill="#ffffff", tags="clock")
        
        self.root.after(1000, self.update_clock)

class PrinterHUD(BaseHUD):
    def __init__(self, root):
        super().__init__(root, bg="#1a1a0d")
        self.setup_ui()
        
    def setup_ui(self):
        self.canvas.create_text(640, 90, text="PRINTER", 
                               font=("Segoe UI", 56, "bold"), 
                               fill="#ffff00")
        self.canvas.create_text(640, 140, text="PRINT QUEUE SIMULATION", 
                               font=("Segoe UI", 16), 
                               fill="#ffffff")

class DayTraderHUD(BaseHUD):
    def __init__(self, root):
        super().__init__(root, bg="#1a0d0d")
        self.setup_ui()
        self.update_stocks()
        
    def setup_ui(self):
        self.canvas.create_text(640, 90, text="DAY TRADER", 
                               font=("Segoe UI", 56, "bold"), 
                               fill="#ff0000")
        self.canvas.create_text(640, 140, text="LIVE STOCK DATA & TRADING", 
                               font=("Segoe UI", 16), 
                               fill="#ffffff")
    
    def update_stocks(self):
        self.canvas.delete("stock_data")
        try:
            symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
            y_pos = 200
            
            for symbol in symbols:
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.history(period="1d")
                    if not info.empty:
                        price = info['Close'].iloc[-1]
                        self.canvas.create_text(640, y_pos, 
                                               text=f"{symbol}: ${price:.2f}", 
                                               font=("Segoe UI", 18), 
                                               fill="#ffffff", tags="stock_data")
                        y_pos += 40
                except:
                    pass
        except Exception as e:
            self.canvas.create_text(640, 200, text=f"Stock data error: {e}", 
                                   font=("Segoe UI", 14), 
                                   fill="#ff0000", tags="stock_data")
        
        self.root.after(30000, self.update_stocks)  # Update every 30 seconds

# ========== SECTION: VOICE COMMANDS ==========
def init_speech_recognition():
    """Initialize speech recognition"""
    try:
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        
        # Find microphone
        mic_list = sr.Microphone.list_microphone_names()
        print("Available microphones:")
        for idx, name in enumerate(mic_list):
            print(f"{idx}: {name}")
        
        mic = sr.Microphone()  # Use default microphone
        
        # Calibrate for ambient noise
        with mic as source:
            print("Calibrating microphone for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print("Microphone calibrated!")
        
        return recognizer, mic
    except Exception as e:
        print(f"Speech recognition initialization error: {e}")
        return None, None

recognizer, mic = init_speech_recognition()
wake_words = ["harvey", "wake up", "i'm home", "jarvis"]
active_project = None

def listen_for_command():
    """Listen for voice commands"""
    if not recognizer or not mic:
        return None
    
    try:
        with mic as source:
            print("Listening...")
            audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
        
        command = recognizer.recognize_google(audio).lower()
        print(f"Heard: {command}")
        return command
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return None
    except Exception as e:
        print(f"Listen error: {e}")
        return None

def handle_command(command, controller):
    """Handle voice commands"""
    global trading_active
    
    try:
        if "switch to" in command:
            if "harvey" in command:
                controller.switch_hud("harvey")
                speak("Switching to Harvey interface")
            elif "maxima" in command:
                controller.switch_hud("maxima")
                speak("Switching to Maxima optimization engine")
            elif "arc" in command:
                controller.switch_hud("arc")
                speak("Switching to Arc clock interface")
            elif "printer" in command:
                controller.switch_hud("printer")
                speak("Switching to Printer interface")
            elif "day trader" in command or "trader" in command:
                controller.switch_hud("daytrader")
                speak("Switching to Day Trader interface")
        
        elif "open" in command:
            if "youtube" in command:
                webbrowser.open("https://youtube.com")
                speak("Opening YouTube")
            elif "google" in command:
                webbrowser.open("https://google.com")
                speak("Opening Google")
            elif "github" in command:
                webbrowser.open("https://github.com")
                speak("Opening GitHub")
        
        elif "time" in command:
            current_time = datetime.now().strftime("%I:%M %p")
            speak(f"The current time is {current_time}")
        
        elif "stock price" in command:
            # Extract symbol from command
            words = command.split()
            if len(words) > 2:
                symbol = words[-1].upper()
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.history(period="1d")
                    if not info.empty:
                        price = info['Close'].iloc[-1]
                        speak(f"The current price of {symbol} is ${price:.2f}")
                    else:
                        speak(f"Could not get price for {symbol}")
                except:
                    speak(f"Error getting stock price for {symbol}")
        
        elif "start trading" in command:
            if api:
                trading_active = True
                threading.Thread(target=trading_loop, args=(controller.current_hud,), daemon=True).start()
                speak("Auto trading started")
            else:
                speak("Trading not available. Check Alpaca API keys.")
        
        elif "stop trading" in command:
            trading_active = False
            speak("Auto trading stopped")
        
        elif "system stats" in command:
            try:
                cpu = psutil.cpu_percent()
                memory = psutil.virtual_memory().percent
                speak(f"CPU usage is {cpu} percent. Memory usage is {memory} percent.")
            except:
                speak("Could not get system statistics")
        
        elif "shutdown" in command or "exit" in command:
            speak("Shutting down Harvey AI Assistant. Goodbye!")
            controller.root.quit()
        
        else:
            responses = [
                "I'm here and ready to help",
                "How can I assist you?",
                "Yes sir, what do you need?",
                "Harvey at your service",
                "Ready for your command"
            ]
            speak(random.choice(responses))
            
    except Exception as e:
        print(f"Command handling error: {e}")
        speak("Sorry, I encountered an error processing that command")

# ========== SECTION: HUD CONTROLLER ==========
class HUDController:
    def __init__(self):
        self.root = tk.Tk()
        self.huds = {}
        self.current_hud = None
        self.setup_huds()
        
    def setup_huds(self):
        """Initialize all HUD interfaces"""
        self.huds["harvey"] = HarveyHUD(self.root)
        self.current_hud = self.huds["harvey"]
        
    def switch_hud(self, hud_name):
        """Switch between different HUD interfaces"""
        if self.current_hud:
            self.current_hud.clear_canvas()
        
        if hud_name not in self.huds:
            if hud_name == "maxima":
                self.huds[hud_name] = MaximaHUD(self.root)
            elif hud_name == "arc":
                self.huds[hud_name] = ArcHUD(self.root)
            elif hud_name == "printer":
                self.huds[hud_name] = PrinterHUD(self.root)
            elif hud_name == "daytrader":
                self.huds[hud_name] = DayTraderHUD(self.root)
            else:
                return
        
        self.current_hud = self.huds[hud_name]
    
    def start_voice_loop(self):
        """Start the voice recognition loop"""
        def voice_loop():
            print("Voice loop started. Say 'Harvey' to wake me up!")
            speak("Harvey AI system online. Say Harvey to activate voice commands.")
            
            while True:
                try:
                    cmd = listen_for_command()
                    if cmd and any(word in cmd for word in wake_words):
                        speak("Yes sir?")
                        print("Wake word detected! Listening for command...")
                        
                        # Listen for the actual command
                        full_command = listen_for_command()
                        if full_command:
                            print(f"Processing command: {full_command}")
                            handle_command(full_command, self)
                        else:
                            speak("I didn't catch that. Please try again.")
                            
                except Exception as e:
                    print(f"Error in voice loop: {e}")
                    time.sleep(1)
        
        # Start voice loop in a separate thread
        voice_thread = threading.Thread(target=voice_loop, daemon=True)
        voice_thread.start()
    
    def run(self):
        """Start the Harvey AI Assistant"""
        try:
            print("🤖 Harvey AI Assistant Starting...")
            print("=" * 50)
            
            # Start voice recognition
            if recognizer and mic:
                self.start_voice_loop()
            else:
                print("Voice recognition not available")
                speak("Voice recognition not available, but Harvey is online")
            
            # Start the GUI
            self.root.mainloop()
            
        except KeyboardInterrupt:
            print("\nShutting down Harvey...")
        except Exception as e:
            print(f"Error running Harvey: {e}")
            messagebox.showerror("Error", f"Harvey encountered an error: {e}")

# ========== SECTION: MAIN EXECUTION ==========
if __name__ == "__main__":
    try:
        print("🤖 HARVEY AI ASSISTANT 🤖")
        print("=" * 40)
        print("Initializing Harvey AI Assistant...")
        
        # Create and run the controller
        controller = HUDController()
        controller.run()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        input("Press Enter to exit...")