# Harvey AI Assistant

Harvey is a voice-controlled AI assistant with multiple HUD interfaces and trading capabilities, inspired by JARVIS from Iron Man.

## Features

- 🎤 **Voice Recognition**: Wake word activation ("Harvey", "wake up", "I'm home", "Jarvis")
- 🗣️ **Text-to-Speech**: Natural voice responses
- 🖥️ **Multiple HUDs**: Different interfaces for various tasks
  - Harvey (Main interface with system stats)
  - Maxima (AI Optimization Engine)
  - Arc (Digital clock interface)
  - Printer (Print queue simulation)
  - Day Trader (Live stock data and trading)
- 📊 **Stock Trading**: Integration with Alpaca API for paper trading
- 🌐 **Web Integration**: Open websites by voice command
- 📈 **Live Data**: Real-time weather, system stats, and stock prices

## Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
python setup_harvey.py
```

### Option 2: Manual Setup

1. **Install System Dependencies** (Linux/Ubuntu):
```bash
sudo apt-get update
sudo apt-get install -y python3-pyaudio portaudio19-dev python3-pip
sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev
sudo apt-get install -y flac
```

2. **Install Python Dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure Trading** (Optional):
   - Edit `alpaca_keys.txt` with your Alpaca API credentials
   - Sign up at [Alpaca Markets](https://alpaca.markets/) for paper trading

## Usage

### Starting Harvey
```bash
python harvey.py
```

### Voice Commands

1. **Wake Harvey**: Say "Harvey", "wake up", "I'm home", or "Jarvis"
2. **Wait for response**: Harvey will say "Yes sir?"
3. **Give command**: Speak your command clearly

### Available Commands

- **"status"** - Check system status
- **"show harvey"** / **"main hud"** - Main interface
- **"show maxima"** - AI Optimization Engine HUD
- **"show arc"** - Digital clock HUD  
- **"show printer"** - Print queue HUD
- **"day trader"** / **"start trading"** - Trading HUD with live data
- **"stop trading"** - Stop automated trading
- **"open [website]"** - Open websites (e.g., "open google.com")
- **"shut down"** - Exit Harvey

### HUD Interfaces

#### Harvey (Main)
- Animated neon ring and pulse effects
- Real-time CPU and RAM monitoring
- Live weather data
- AAPL stock price display

#### Maxima
- AI-themed interface with rotating ring
- Optimization engine simulation

#### Arc
- Purple-themed interface
- Live digital clock display

#### Printer
- Print queue simulation
- Progress bar animation

#### Day Trader
- Live AAPL stock price
- Trading signals (BUY/SELL/HOLD)
- Automated trading with Alpaca API

## Troubleshooting

### Audio Issues

**Can't hear Harvey:**
```bash
# Install/reinstall text-to-speech
sudo apt-get install espeak espeak-data
pip install --upgrade pyttsx3
```

**Harvey can't hear you:**
```bash
# Check microphone permissions
sudo apt-get install portaudio19-dev
pip install --upgrade pyaudio SpeechRecognition

# Test microphone
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"
```

### Common Fixes

1. **Permission Denied**: Run with `sudo` if needed for system packages
2. **PyAudio Issues**: 
   - Linux: `sudo apt-get install python3-pyaudio`
   - Windows: Download wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
3. **No Sound**: Check system volume and audio drivers
4. **Microphone Not Working**: Check privacy settings and permissions

### Trading Setup

1. Create free account at [Alpaca Markets](https://alpaca.markets/)
2. Get paper trading API keys
3. Edit `alpaca_keys.txt`:
```
YOUR_API_KEY_HERE
YOUR_SECRET_KEY_HERE
```

## System Requirements

- Python 3.7+
- Working microphone
- Audio output (speakers/headphones)
- Internet connection
- Linux/Windows/macOS

## Dependencies

- `pyttsx3` - Text-to-speech
- `SpeechRecognition` - Voice recognition
- `pyaudio` - Audio I/O
- `tkinter` - GUI (usually included with Python)
- `requests` - HTTP requests
- `yfinance` - Stock data
- `alpaca-trade-api` - Trading API
- `psutil` - System monitoring

## Architecture

```
harvey.py
├── Voice Engine (pyttsx3)
├── Speech Recognition (Google Speech API)
├── HUD System (tkinter)
│   ├── BaseHUD (parent class)
│   ├── HarveyHUD (main interface)
│   ├── MaximaHUD (AI theme)
│   ├── ArcHUD (clock theme)
│   ├── PrinterHUD (print queue)
│   └── DayTraderHUD (trading)
├── Trading System (Alpaca API)
└── Voice Command Handler
```

## Security Notes

- Uses paper trading by default (no real money)
- API keys stored in local file (keep secure)
- Voice data processed by Google Speech Recognition
- No sensitive data transmitted except for API calls

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is for educational purposes. Please respect API terms of service for external services used.