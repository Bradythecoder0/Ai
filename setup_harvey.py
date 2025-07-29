#!/usr/bin/env python3
"""
Harvey AI Assistant Setup Script
This script helps install dependencies and configure Harvey.
"""

import subprocess
import sys
import os
import platform

def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        print(f"Error: {e.stderr}")
        return False

def install_system_dependencies():
    """Install system-level dependencies"""
    system = platform.system().lower()
    
    print("Installing system dependencies...")
    
    if system == "linux":
        # Ubuntu/Debian
        commands = [
            "sudo apt-get update",
            "sudo apt-get install -y python3-pyaudio portaudio19-dev python3-pip",
            "sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev",
            "sudo apt-get install -y flac"
        ]
        for cmd in commands:
            if not run_command(cmd):
                print(f"Failed to run: {cmd}")
                print("You may need to install these manually:")
                print("- portaudio19-dev (for microphone support)")
                print("- espeak (for text-to-speech)")
                print("- flac (for audio processing)")
                
    elif system == "darwin":  # macOS
        commands = [
            "brew install portaudio",
            "brew install espeak",
            "brew install flac"
        ]
        for cmd in commands:
            if not run_command(cmd):
                print("Please install Homebrew and run these commands manually:")
                for c in commands:
                    print(f"  {c}")
                    
    elif system == "windows":
        print("On Windows, PyAudio should install from pip.")
        print("If you have issues, download PyAudio wheel from:")
        print("https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")

def install_python_dependencies():
    """Install Python dependencies"""
    print("\nInstalling Python dependencies...")
    
    # Upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip")
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        success = run_command(f"{sys.executable} -m pip install -r requirements.txt")
        if not success:
            print("Failed to install from requirements.txt")
            print("Trying individual packages...")
            
            packages = [
                "pyttsx3==2.90",
                "SpeechRecognition==3.10.0", 
                "requests==2.31.0",
                "yfinance==0.2.28",
                "alpaca-trade-api==3.1.1",
                "psutil==5.9.8"
            ]
            
            # Try PyAudio separately as it often causes issues
            print("Installing PyAudio (this might take a moment)...")
            pyaudio_success = run_command(f"{sys.executable} -m pip install pyaudio")
            if not pyaudio_success:
                print("PyAudio installation failed. Trying alternative...")
                run_command(f"{sys.executable} -m pip install --only-binary=all pyaudio")
            
            for package in packages:
                run_command(f"{sys.executable} -m pip install {package}")
    else:
        print("requirements.txt not found!")

def test_audio():
    """Test audio functionality"""
    print("\nTesting audio functionality...")
    
    try:
        import pyttsx3
        engine = pyttsx3.init()
        print("✓ Text-to-speech engine initialized")
        
        # Test speaking
        engine.say("Harvey audio test successful")
        engine.runAndWait()
        print("✓ Text-to-speech working")
        
    except Exception as e:
        print(f"✗ Text-to-speech error: {e}")
    
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        mics = sr.Microphone.list_microphone_names()
        print(f"✓ Found {len(mics)} microphones:")
        for i, mic in enumerate(mics):
            print(f"  {i}: {mic}")
            
    except Exception as e:
        print(f"✗ Microphone error: {e}")

def setup_config():
    """Setup configuration files"""
    print("\nSetting up configuration...")
    
    if not os.path.exists("alpaca_keys.txt"):
        with open("alpaca_keys.txt", "w") as f:
            f.write("YOUR_ALPACA_API_KEY_HERE\n")
            f.write("YOUR_ALPACA_SECRET_KEY_HERE\n")
        print("✓ Created alpaca_keys.txt template")
        print("  Please edit this file with your Alpaca API credentials")
    else:
        print("✓ alpaca_keys.txt already exists")

def main():
    print("=== Harvey AI Assistant Setup ===")
    print("This script will install dependencies and configure Harvey.\n")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version}")
    
    # Install system dependencies
    install_system_dependencies()
    
    # Install Python dependencies  
    install_python_dependencies()
    
    # Setup config files
    setup_config()
    
    # Test audio
    test_audio()
    
    print("\n=== Setup Complete ===")
    print("To run Harvey:")
    print("  python harvey.py")
    print("\nTroubleshooting:")
    print("- If microphone doesn't work, check permissions")
    print("- If voice doesn't work, try: sudo apt-get install espeak")
    print("- For trading, edit alpaca_keys.txt with your API keys")

if __name__ == "__main__":
    main()