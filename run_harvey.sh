#!/bin/bash

echo "🤖 Harvey AI Assistant Setup & Launch 🤖"
echo "========================================"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --break-system-packages \
    pyttsx3 \
    SpeechRecognition \
    requests \
    yfinance \
    psutil \
    pyaudio \
    alpaca-trade-api

echo "Dependencies installed!"
echo "Launching Harvey AI Assistant..."
echo "========================================"

# Run Harvey
python3 harvey_complete.py