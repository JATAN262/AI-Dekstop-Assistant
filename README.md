# AI Desktop Assistant (ASSIP)

ASSIP is a Python-based desktop assistant that listens to voice commands, talks back, and handles everyday tasks on your computer. It has a simple Tkinter GUI with a start button and a live status indicator, so you can see when it's listening, processing, or speaking.

## Features

- Voice recognition and text-to-speech replies
- General conversation powered by Groq's LLaMA 3 model, for anything outside the built-in commands
- Open websites or run a Google search by voice
- Wikipedia lookups
- Live weather reports by city
- Daily news headlines by category (sports, business, tech, health, entertainment)
- System info: CPU, memory, disk, battery, and network status
- Brightness and volume control
- Screenshots, file explorer access, and internet speed checks
- Voice-set reminders with popup alerts
- WhatsApp messaging to saved contacts
- SOS text alert with your live location, sent through Twilio

## Tech stack

- Python
- SpeechRecognition + pyttsx3 for voice input and output
- Groq API for conversational responses
- Tkinter for the GUI
- psutil and screen_brightness_control for system control
- Twilio for SOS messaging
- pywhatkit for WhatsApp automation

## Project structure

```
AI-Dekstop-Assistant/
├── main.py                  # GUI, voice loop, and command handling
├── nlp_processor.py         # Intent and entity extraction from commands
├── requirements.txt
├── contacts.example.json    # Template for your WhatsApp contacts
└── README.md
```

## Setup

1. Clone the repository
   ```
   git clone https://github.com/JATAN262/AI-Dekstop-Assistant.git
   cd AI-Dekstop-Assistant
   ```

2. Install dependencies
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your own API keys:
   ```
   TWILIO_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=your_twilio_number
   EMERGENCY_CONTACT=your_emergency_contact_number
   GROQ_API_KEY=your_groq_key
   NEWS_API_KEY=your_newsapi_key
   WEATHER_API_KEY=your_weatherapi_key
   ```

4. Copy `contacts.example.json` to `contacts.json` and fill in your own contacts for the WhatsApp feature. This file is gitignored, so your numbers stay off GitHub.

5. Run it
   ```
   python main.py
   ```

Click "Start Assistant" in the GUI and speak your command. Make sure your microphone is connected.

## Example commands

- "What's the weather in Mumbai?"
- "Open YouTube"
- "Search for Python tutorials"
- "Set brightness to 70"
- "Take a screenshot"
- "Set a reminder for team meeting in 10 minutes"
- "What's the system info?"

## Requirements

- Python 3.8 or higher
- Working microphone
- Internet connection
- API keys for Groq, WeatherAPI, NewsAPI, and Twilio (all have free tiers)

## Security note

Never commit your `.env` or `contacts.json` files. Both are gitignored by default in this repo. If you're forking this project, double check your git history doesn't already contain real API keys or phone numbers before making the repo public.

## Author

Jatan  
GitHub: [JATAN262](https://github.com/JATAN262)

## License

This project is for educational purposes. Feel free to use, modify, and learn from it.
