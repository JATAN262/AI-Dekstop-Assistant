import os
import re
import sys
from datetime import datetime
import geocoder
import groq
import speech_recognition as sr
import wikipedia
from pywhatkit import take_screenshot, sendwhatmsg_instantly
from twilio.rest import Client
import requests
import webbrowser
import socket
import uuid
from dotenv import load_dotenv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import screen_brightness_control as sbc
import threading
import platform
import tempfile
import pyttsx3
import time
import pyautogui
import json
import subprocess
from typing import Dict, Any, List, Tuple, Optional


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nlp_processor import process_nlp

load_dotenv()

# Initialize the text-to-speech engine using pyttsx3 (older version)
engine = None
try:
    # Try initializing directly without using comtypes
    engine = pyttsx3.init()
    
    if engine:
        # Set properties
        engine.setProperty('rate', 175)
        engine.setProperty('volume', 1.0)
        
        # Get voices and try to select a female voice if available
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
            
        # Simple test
        engine.say("Text to speech initialized")
        engine.runAndWait()
        print("Text-to-speech engine initialized successfully")
except Exception as e:
    print(f"Warning: Could not initialize text-to-speech engine: {e}")
    engine = None

# Function to make the assistant speak
def speak(audio):
    """Function to make the assistant speak with error handling"""
    try:
        if engine is not None:
            # Convert any non-string input to string
            text = str(audio).strip()
            if text:  # Only speak if there's an actual text
                engine.say(text)
                engine.runAndWait()
                print(f"Assistant: {text}")
        else:
            # Fallback to just printing if TTS is not available
            print(f"Assistant (TTS Disabled): {audio}")
    except Exception as e:
        print(f"Error in speak function: {e}")
        print(f"Assistant (Error): {audio}")


def take_command():
    """Optimized speech recognition."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        # Dynamic energy threshold adaptation for better recognition in noisy environments
        r.dynamic_energy_threshold = True
        r.energy_threshold = 300  # Adjust based on your environment
        r.dynamic_energy_adjustment_ratio = 1.5
        
        # Adjust for ambient noise
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            print("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            print(f"User: {query}")
            return query.lower()

        except sr.UnknownValueError:
            speak("I didn't catch that. Can you say it again?")
            return ""  # Changed to return empty string instead of recursive call to avoid stack overflow

        except sr.RequestError:
            speak("There was a problem with the speech recognition service.")
            return ""

        except Exception as e:
            print(f"Error: {e}")
            speak("An error occurred while recognizing speech.")
            return ""


def wish():
    hour = int(datetime.now().hour)
    if 0 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")
    speak("I am your Assip. How can I help you today?")


def get_ip_mac():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        mac_address = ':'.join(re.findall('..', '%012x' % uuid.getnode()))  # Format MAC address

        result = f"IP Address: {ip_address}\nMAC Address: {mac_address}"
        print(result)
        speak(result)

    except Exception as e:
        speak("I couldn't retrieve the IP and MAC address.")
        print(f"Error: {e}")


# Twilio Credentials
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
EMERGENCY_CONTACT = os.getenv('EMERGENCY_CONTACT')

def get_location():
    g = geocoder.ip('me')
    if g.latlng:
        return g.latlng
    return None

# SOS Signal
def send_sos_sms():
    location = get_location()
    if location:
        sos_message = f"🚨 SOS Alert! Emergency at location: {location} 🚨\nGoogle Maps: https://www.google.com/maps/search/?api=1&query={location[0]},{location[1]}"
    else:
        sos_message = "🚨 SOS Alert! Location not found. Please check manually."
    msg = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    message = msg.messages.create(body=sos_message, from_=TWILIO_PHONE_NUMBER, to=EMERGENCY_CONTACT)
    print(f"SOS SMS sent! Message SID: {message.sid}")


# WhatsApp Messaging
contacts = {"dhruvin": "9913635130", "papa": "9879674896", "mummy": "8488901762", "grandfather": "9879665906",
            "harsh": "9727009440"}


def validate_phone_number(number):
    return re.match(r"^\d{10}$", number)


def get_phone_number(contact_name):
    contact_name = contact_name.lower()
    return contacts.get(contact_name, None)


def send_whatsapp_message(contact_name, message):
    phone_number = get_phone_number(contact_name)
    if phone_number and validate_phone_number(phone_number):
        sendwhatmsg_instantly(f"+91{phone_number}", message, wait_time=10)
        speak("Message sent successfully.")
    else:
        speak("Invalid contact name or number.")


# Groq AI Chatbot
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if GROQ_API_KEY:
    try:
        client = groq.Client(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Groq client: {e}")
        client = None
else:
    print("Warning: GROQ_API_KEY not found in environment variables")
    client = None

def get_chat_response(user_input):
    """Get AI response using Groq model"""
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are ASSIP, a virtual assistant with a human-like personality. Keep responses brief and conversational - 1-2 sentences max. Never say 'as an AI' or similar phrases. Use casual language like a helpful friend would. Be direct and to the point."
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=100,
            top_p=1,
            stream=False,
        )
        
        response = chat_completion.choices[0].message.content
        print(f"AI: {response}")
        speak(response)
        return response

    except Exception as e:
        error_message = f"I having trouble to connecting my AI services. {str(e)}"
        print(f"Error: {e}")
        speak(error_message)
        return error_message


def search_wikipedia(query):
    """Searches Wikipedia based on user input."""
    try:
        speak("Searching Wikipedia...")
        query = query.replace("wikipedia", "").strip()
        results = wikipedia.summary(query, sentences=2)
        speak("According to Wikipedia")
        print(results)
        speak(results)
    except wikipedia.exceptions.DisambiguationError:
        speak("Your query is too broad. Please be more specific.")
    except wikipedia.exceptions.PageError:
        speak("I couldn't find anything on Wikipedia for that.")


def open_website(query):
    """Handles website opening or searching the web."""
    domain_pattern = r"\b(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})\b"
    match = re.search(domain_pattern, query)
    if match:
        domain = match.group(0)
        if not domain.startswith("http"):
            domain = "https://" + domain
        webbrowser.open(domain)
        speak(f"Opening website {domain.split('//')[-1]}")
    else:
        search_url = f"https://www.google.com/search?q={query}"
        webbrowser.open(search_url)
        speak(f"Searching Google for {query}")


def web_search(query):
    """Function to search the web for any query."""
    search_url = f"https://www.google.com/search?q={query}"
    webbrowser.open(search_url)
    speak(f"Searching the web for {query}")


# API Keys
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# Extract category for news
def extract_category(user_input):
    categories = {
        "sports": ["sports", "cricket", "football", "tennis"],
        "business": ["finance", "stocks", "economy", "business"],
        "technology": ["tech", "gadgets", "AI", "software"],
        "health": ["health", "medicine", "COVID", "fitness"],
        "entertainment": ["movies", "music", "entertainment", "Hollywood"]
    }
    for category, keywords in categories.items():
        if any(word in user_input for word in keywords):
            return category
    return "general"  # Default category


# Add cache for API responses to improve performance
api_cache = {}
def cache_api_response(func):
    """Decorator to cache API responses."""
    def wrapper(*args, **kwargs):
        cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
        current_time = time.time()
        
        # If cached result exists and is less than 10 minutes old, return it
        if cache_key in api_cache and current_time - api_cache[cache_key]['time'] < 600:
            print(f"Using cached result for {func.__name__}")
            return api_cache[cache_key]['result']
        
        # Otherwise call the function and cache the result
        result = func(*args, **kwargs)
        api_cache[cache_key] = {'result': result, 'time': current_time}
        return result
    
    return wrapper

# Weather function with caching
@cache_api_response
def get_weather(city):
    """Get weather with caching for improved performance."""
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
    response = requests.get(url)

    if response.status_code == 200:
        weather_data = response.json()
        temp = weather_data["current"]["temp_c"]  # Corrected key for temperature in Celsius
        condition = weather_data["current"]["condition"]["text"]  # Corrected key for weather condition
        forecast = f"The weather in {city} is {condition} with a temperature of {temp}°C."
        print(forecast)
        speak(forecast)  # Assuming 'speak()' is defined elsewhere
        return forecast
    else:
        message = "Sorry, I couldn't fetch the weather data. Please try again."
        speak(message)
        return message

# News function with caching
@cache_api_response
def get_daily_news(api_key, category='general', country='us', page_size=5):
    """Get news with caching for improved performance."""
    url = f'https://newsapi.org/v2/top-headlines?country={country}&category={category}&pageSize={page_size}&apiKey={api_key}'
    response = requests.get(url)

    if response.status_code == 200:
        news_data = response.json()
        articles = news_data.get('articles', [])

        if articles:
            speak(f"Here are the top {len(articles)} news headlines in {category}.")
            result = []
            for i, article in enumerate(articles, 1):
                headline = f"{i}. {article['title']}"
                print(headline)
                print(f"   Source: {article['source']['name']}")
                speak(article['title'])
                result.append(headline)
            return result
        else:
            message = "No news found for this category."
            speak(message)
            return message
    else:
        message = "Error fetching news."
        speak(message)
        return message


def ask_for_application():
    """Asks the user to specify which application to open or close."""
    speak("Which application would you like to open or close?")
    app = take_command()
    process_command(app)


# System Control functionality
def get_system_info():
    """Provides detailed system information with better formatting."""
    # Get CPU information
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count(logical=False)
    cpu_logical = psutil.cpu_count(logical=True)
    
    # Get memory information
    memory = psutil.virtual_memory()
    memory_total = round(memory.total / (1024**3), 2)  # Convert to GB
    memory_used = round(memory.used / (1024**3), 2)  # Convert to GB
    memory_percent = memory.percent
    
    # Get disk information
    disk = psutil.disk_usage('/')
    disk_total = round(disk.total / (1024**3), 2)  # Convert to GB
    disk_used = round(disk.used / (1024**3), 2)  # Convert to GB
    disk_percent = disk.percent
    
    # Get battery information if available
    battery_info = "Not available"
    battery = psutil.sensors_battery()
    if battery:
        battery_percent = battery.percent
        charging = "Plugged In" if battery.power_plugged else "On Battery"
        battery_info = f"{battery_percent}% ({charging})"
    
    # Get network information
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    
    # Format the information
    info = f"""
System Information:
CPU: {cpu_percent}% usage across {cpu_logical} logical cores ({cpu_count} physical)
Memory: {memory_used}GB used out of {memory_total}GB ({memory_percent}%)
Storage: {disk_used}GB used out of {disk_total}GB ({disk_percent}%)
Network: IP address {ip_address} on {hostname}
Battery: {battery_info}
    """
    
    print(info)
    speak(f"Here's your system information. CPU usage is {cpu_percent}%, memory usage is {memory_percent}%, and disk usage is {disk_percent}%. Battery is {battery_info}.")
    return info

def adjust_brightness(level):
    try:
        if 0 <= level <= 100:
            sbc.set_brightness(level)
            speak(f"Brightness set to {level}%")
        else:
            speak("Brightness level should be between 0 and 100")
    except Exception as e:
        speak(f"Sorry, I couldn't adjust the brightness. {str(e)}")

def adjust_volume(level):
    try:
        if 0 <= level <= 100:
            # First mute to ensure we start from 0
            pyautogui.press('volumemute')
            # Wait a moment for the mute to take effect
            time.sleep(0.5)
            
            # Press volume up key multiple times based on the level
            # Each press is approximately 2% volume on most Windows systems
            # So for 70% we need to press it 35 times
            steps = int(level / 2)
            
            # Make sure steps is valid
            if steps < 0:
                steps = 0
            elif steps > 50:  # limit to 50 steps for safety
                steps = 50
                
            # Reset volume to 0 by pressing mute
            pyautogui.press('volumemute')
            time.sleep(0.2)
            
            # Now press volume up exact number of times needed
            for _ in range(steps):
                pyautogui.press('volumeup')
                time.sleep(0.05)  # Small delay to ensure all keypresses register
            
            speak(f"Volume set to {level}%")
        else:
            speak("Volume level should be between 0 and 100")
    except Exception as e:
        print(f"Error adjusting volume: {e}")
        speak(f"Sorry, I couldn't adjust the volume. {str(e)}")

def process_system_control(command, entities):
    """Process system control commands more intelligently based on user input."""
    # Handle brightness commands
    if 'brightness' in entities:
        brightness_level = entities['brightness']
        adjust_brightness(brightness_level)
        return True
        
    # Handle volume commands (fallback to the direct pattern matching which is more robust)
    elif 'volume' in entities:
        volume_level = entities['volume']
        adjust_volume(volume_level)
        return True
        
    # Handle specific system info requests
    elif re.search(r'(cpu|processor)', command.lower()):
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count(logical=False)
        speak(f"CPU usage is currently {cpu_percent}% across {cpu_count} physical cores.")
        return True
        
    elif re.search(r'(memory|ram)', command.lower()):
        memory = psutil.virtual_memory()
        memory_total = round(memory.total / (1024**3), 2)
        memory_used = round(memory.used / (1024**3), 2)
        speak(f"Memory usage is {memory.percent}%. {memory_used} gigabytes used out of {memory_total} gigabytes total.")
        return True
        
    elif re.search(r'(disk|storage|drive)', command.lower()):
        disk = psutil.disk_usage('/')
        disk_total = round(disk.total / (1024**3), 2)
        disk_used = round(disk.used / (1024**3), 2)
        speak(f"Disk usage is {disk.percent}%. {disk_used} gigabytes used out of {disk_total} gigabytes total.")
        return True
        
    elif re.search(r'(battery|power)', command.lower()):
        battery = psutil.sensors_battery()
        if battery:
            charging = "plugged in" if battery.power_plugged else "on battery power"
            speak(f"Battery is at {battery.percent}% and currently {charging}.")
        else:
            speak("Battery information is not available.")
        return True
        
    elif re.search(r'(network|internet|ip|connection)', command.lower()):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        speak(f"Your device name is {hostname} with IP address {ip_address}.")
        return True
        
    # If no specific system info was requested, provide general info
    else:
        get_system_info()
        return True
        
    return False

def process_command(command):
    """Process the voice command using NLP and execute appropriate functions"""
    if not command:
        speak("I didn't hear anything. Please try again.")
        return
    
    # Direct pattern matches for common commands
    # Volume control patterns
    volume_match = re.search(r'(?:set|change|adjust)?\s*(?:the\s*)?(volume|sound)(?:\s*(?:level|up|down)?)?\s*(?:to|at)?\s*(\d+)(?:\s*percent|%)?', command.lower())
    if volume_match:
        try:
            volume_level = int(volume_match.group(2))
            print(f"Setting volume to {volume_level}%")
            adjust_volume(volume_level)
            return
        except (ValueError, IndexError):
            speak("I couldn't understand the volume level. Please try again.")
            return
    
    # Check for direct volume up/down commands
    if re.search(r'(volume|sound)\s+(up|increase|higher|louder)', command.lower()):
        adjust_volume(70)  # Default increase to 70%
        return
    
    if re.search(r'(volume|sound)\s+(down|decrease|lower|quieter)', command.lower()):
        adjust_volume(30)  # Default decrease to 30%
        return
        
    if re.search(r'mute|quiet|silence', command.lower()):
        adjust_volume(0)  # Mute
        return
    
    # System info direct pattern matching
    if re.search(r'(system|computer)\s+(info|information|status)', command.lower()):
        get_system_info()
        return
        
    if re.search(r'(cpu|processor)\s+(usage|info|status)', command.lower()):
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count(logical=False)
        speak(f"CPU usage is currently {cpu_percent}% across {cpu_count} physical cores.")
        return
        
    if re.search(r'(memory|ram)\s+(usage|info|status)', command.lower()):
        memory = psutil.virtual_memory()
        memory_total = round(memory.total / (1024**3), 2)
        memory_used = round(memory.used / (1024**3), 2)
        speak(f"Memory usage is {memory.percent}%. {memory_used} gigabytes used out of {memory_total} gigabytes total.")
        return
        
    if re.search(r'(disk|storage|drive)\s+(usage|info|status)', command.lower()):
        disk = psutil.disk_usage('/')
        disk_total = round(disk.total / (1024**3), 2)
        disk_used = round(disk.used / (1024**3), 2)
        speak(f"Disk usage is {disk.percent}%. {disk_used} gigabytes used out of {disk_total} gigabytes total.")
        return
        
    if re.search(r'(battery|power)\s+(level|status|info)', command.lower()):
        battery = psutil.sensors_battery()
        if battery:
            charging = "plugged in" if battery.power_plugged else "on battery power"
            speak(f"Battery is at {battery.percent}% and currently {charging}.")
        else:
            speak("Battery information is not available.")
        return
    
    # Screenshot pattern
    screenshot_match = re.search(r'(?:take|capture)\s+(?:a\s+)?screenshot', command.lower())
    if screenshot_match:
        try:
            speak("Taking screenshot")
            take_screenshot()
            speak("Screenshot taken")
            return
        except Exception as e:
            speak(f"I couldn't take a screenshot. {e}")
            return
    
    # Add direct search pattern matching
    search_match = re.search(r'(?:search|look\s+(?:up|for)|find|google)\s+(?:for\s+)?(.*)', command.lower())
    if search_match:
        search_query = search_match.group(1).strip()
        if search_query:
            web_search(search_query)
            return
    
    # Add pattern matching for new functionality
    file_explorer_match = re.search(r'(open|launch|show)(?:\s+(?:the|my))?\s+(?:file(?:\s+)?(?:explorer|manager)|documents|files)', command.lower())
    if file_explorer_match:
        open_file_explorer()
        return
    
    internet_speed_match = re.search(r'(check|test|what\'s|how\'s|measure)(?:\s+(?:the|my))?\s+(?:internet|network|wifi|wi-fi|connection)(?:\s+speed)?', command.lower())
    if internet_speed_match:
        check_internet_speed()
        return
    
    reminder_match = re.search(r'(?:set|create|add|remind\s+me\s+(?:about|of))(?:\s+a)?\s+reminder\s+(?:for|about|to)?\s+(.+?)(?:\s+in\s+(\d+)\s+minutes?)?(?:\?|$|please)', command.lower())
    if reminder_match:
        title = reminder_match.group(1).strip()
        minutes = reminder_match.group(2) if reminder_match.group(2) else "5"  # Default to 5 minutes
        set_reminder(title, minutes)
        return
    
    # Use NLP to understand the command
    nlp_result = process_nlp(command)
    intent = nlp_result['intent']
    entities = nlp_result['entities']
    
    # Process based on intent
    if intent == 'open_website' and 'website' in entities:
        open_website(entities['website'])
    
    elif intent == 'wikipedia' and 'query' in entities:
        search_wikipedia(entities['query'])
    
    elif intent == 'web_search' and 'query' in entities:
        search_query = entities['query']
        web_search(search_query)
    
    elif intent == 'search' and 'query' in entities:  # Add fallback for 'search' intent
        search_query = entities['query']
        web_search(search_query)
    
    elif intent == 'weather' and 'city' in entities:
        get_weather(entities['city'])
    
    elif intent == 'news':
        category = entities.get('category', 'general')
        get_daily_news(NEWS_API_KEY, category=category)
    
    elif intent == 'system_info':
        get_ip_mac()
    
    elif intent == 'whatsapp' and 'contact' in entities:
        message = entities.get('message', '')
        if not message:
            speak("What message would you like to send?")
            message = take_command()
        send_whatsapp_message(entities['contact'], message)
    
    elif intent == 'emergency':
        send_sos_sms()
    
    elif intent == 'app_control' and 'app_name' in entities:
        try:
            os.system(f"start {entities['app_name']}")
            speak(f"Opening {entities['app_name']}")
        except Exception as e:
            speak(f"I couldn't open {entities['app_name']}. {e}")
    
    elif intent == 'system_control':
        process_system_control(command, entities)
        
    # Add handlers for new intents
    elif intent == 'file_explorer':
        path = entities.get('path', None)
        open_file_explorer(path)
        
    elif intent == 'internet_speed':
        check_internet_speed()
        
    elif intent == 'set_reminder':
        title = entities.get('title', 'reminder')
        minutes = entities.get('minutes', 5)
        set_reminder(title, minutes)
    
    # Fallback to AI chatbot for general queries
    else:
        get_chat_response(command)


def create_gui():
    global root, start_button, status_label, update_status  # Make these global so other functions can access them
    root = tk.Tk()
    root.title("AI Assistant")
    root.geometry("400x350")
    
    # Set theme colors
    bg_color = "#f0f0f0"
    accent_color = "#4a86e8"
    text_color = "#333333"
    
    # Apply colors
    root.configure(bg=bg_color)
    style = ttk.Style()
    style.configure('TButton', padding=10, font=('Helvetica', 12))
    style.configure('Accent.TButton', background=accent_color)
    style.configure('TLabel', background=bg_color, foreground=text_color, font=('Helvetica', 10))
    style.configure('Title.TLabel', background=bg_color, foreground=text_color, font=('Helvetica', 16, 'bold'))
    
    # Create a main frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Add a title
    title_label = ttk.Label(
        main_frame,
        text="AI Desktop Assistant",
        style='Title.TLabel'
    )
    title_label.pack(pady=10)
    
    # Add status indicator
    status_frame = ttk.Frame(main_frame)
    status_frame.pack(fill=tk.X, pady=10)
    
    status_label = ttk.Label(
        status_frame,
        text="Status: Ready",
        style='TLabel'
    )
    status_label.pack(side=tk.LEFT, padx=5)
    
    # Status indicator (circle)
    status_canvas = tk.Canvas(status_frame, width=15, height=15, bg=bg_color, highlightthickness=0)
    status_canvas.pack(side=tk.LEFT)
    status_indicator = status_canvas.create_oval(2, 2, 13, 13, fill="gray")
    
    # Center the button frame
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(expand=True)
    
    # Make start_button global so we can enable/disable it
    start_button = ttk.Button(
        button_frame,
        text="Start Assistant",
        command=start_assistant,
        style='Accent.TButton'
    )
    start_button.pack(pady=10)
    
    # Add settings button
    settings_button = ttk.Button(
        button_frame,
        text="Settings",
        command=show_settings,
        style='TButton'
    )
    settings_button.pack(pady=10)
    
    # Add a quit button
    quit_button = ttk.Button(
        button_frame,
        text="Quit",
        command=root.destroy,
        style='TButton'
    )
    quit_button.pack(pady=10)
    
    # Add version information
    version_label = ttk.Label(
        main_frame,
        text="v1.0.0",
        style='TLabel'
    )
    version_label.pack(side=tk.BOTTOM, pady=5)
    
    # Function to update status indicator
    def update_status(status="ready"):
        if status == "listening":
            status_canvas.itemconfig(status_indicator, fill="green")
            status_label.config(text="Status: Listening")
        elif status == "processing":
            status_canvas.itemconfig(status_indicator, fill="orange")
            status_label.config(text="Status: Processing")
        elif status == "speaking":
            status_canvas.itemconfig(status_indicator, fill="blue")
            status_label.config(text="Status: Speaking")
        else:
            status_canvas.itemconfig(status_indicator, fill="gray")
            status_label.config(text="Status: Ready")
    
    # Assign the function to the global variable
    globals()['update_status'] = update_status
    
    root.mainloop()

def show_settings():
    """Show settings dialog"""
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("300x400")
    settings_window.resizable(False, False)
    
    # Add settings options
    ttk.Label(settings_window, text="Assistant Settings", font=('Helvetica', 14, 'bold')).pack(pady=10)
    
    # Voice settings frame
    voice_frame = ttk.LabelFrame(settings_window, text="Voice Settings")
    voice_frame.pack(fill=tk.X, padx=10, pady=5, ipady=5)
    
    # Voice speed
    ttk.Label(voice_frame, text="Speech Rate:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    speed_var = tk.IntVar(value=175)  # Default value
    speed_scale = ttk.Scale(voice_frame, from_=100, to=250, variable=speed_var, orient=tk.HORIZONTAL)
    speed_scale.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
    ttk.Label(voice_frame, textvariable=speed_var).grid(row=0, column=2, padx=5, pady=5)
    
    # Voice volume
    ttk.Label(voice_frame, text="Volume:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
    volume_var = tk.IntVar(value=100)  # Default value
    volume_scale = ttk.Scale(voice_frame, from_=0, to=100, variable=volume_var, orient=tk.HORIZONTAL)
    volume_scale.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
    ttk.Label(voice_frame, textvariable=volume_var).grid(row=1, column=2, padx=5, pady=5)
    
    # API Settings frame
    api_frame = ttk.LabelFrame(settings_window, text="API Settings")
    api_frame.pack(fill=tk.X, padx=10, pady=5, ipady=5)
    
    # Weather API key
    ttk.Label(api_frame, text="Weather API Key:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    weather_api_entry = ttk.Entry(api_frame, width=20)
    weather_api_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
    weather_api_entry.insert(0, WEATHER_API_KEY if WEATHER_API_KEY else "")
    
    # News API key
    ttk.Label(api_frame, text="News API Key:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
    news_api_entry = ttk.Entry(api_frame, width=20)
    news_api_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
    news_api_entry.insert(0, NEWS_API_KEY if NEWS_API_KEY else "")
    
    # Save button
    ttk.Button(settings_window, text="Save Settings", command=lambda: save_settings(
        speed_var.get(),
        volume_var.get(),
        weather_api_entry.get(),
        news_api_entry.get(),
        settings_window
    )).pack(pady=10)

def save_settings(speed, volume, weather_api, news_api, window):
    """Save settings to a config file"""
    try:
        settings = {
            "speech_rate": speed,
            "volume": volume,
            "weather_api_key": weather_api,
            "news_api_key": news_api
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f, indent=4)
        
        # Update engine settings if it exists
        if 'engine' in globals() and engine is not None:
            engine.setProperty('rate', speed)
            engine.setProperty('volume', volume / 100)
        
        # Update API keys
        global WEATHER_API_KEY, NEWS_API_KEY
        WEATHER_API_KEY = weather_api
        NEWS_API_KEY = news_api
        
        messagebox.showinfo("Settings", "Settings saved successfully!")
        window.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

def start_assistant():
    """Start the assistant in a separate thread"""
    try:
        # Disable the start button to prevent multiple instances
        start_button.configure(state='disabled')
        update_status("listening")
        
        # Create and start the assistant thread
        assistant_thread = threading.Thread(target=run_assistant)
        assistant_thread.daemon = True  # Thread will be terminated when the main program exits
        assistant_thread.start()
        
    except Exception as e:
        error_msg = f"Error starting assistant: {str(e)}"
        print(error_msg)
        messagebox.showerror("Error", error_msg)
        start_button.configure(state='normal')
        update_status("ready")

def run_assistant():
    """Function that runs in a separate thread to handle the assistant's main loop"""
    try:
        wish()
        while True:
            update_status("listening")
            command = take_command()
            if command:
                update_status("processing")
                process_command(command)
                update_status("ready")
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        print(error_msg)
        root.after(0, lambda: messagebox.showerror("Error", error_msg))
        root.after(0, lambda: start_button.configure(state='normal'))
        root.after(0, lambda: update_status("ready"))

# Add new functionality for file operations
def open_file_explorer(path=None):
    """Opens the file explorer at the specified path or home directory."""
    try:
        if not path:
            path = os.path.expanduser("~")
        if platform.system() == "Windows":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])
        speak(f"Opening file explorer at {path}")
    except Exception as e:
        speak(f"I couldn't open the file explorer. {str(e)}")

def check_internet_speed():
    """Check internet connection speed."""
    try:
        speak("Testing your internet speed. This might take a few seconds...")
        
        # Simple ping test as a basic speed check
        host = "www.google.com"
        ping_result = subprocess.run(["ping", "-n", "4", host], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True)
        
        if ping_result.returncode == 0:
            # Extract average time from ping response
            result = ping_result.stdout
            avg_line = [line for line in result.split('\n') if "Average" in line]
            if avg_line:
                avg_time = avg_line[0].split("=")[-1].strip()
                speak(f"Your internet connection is working. Average ping time to Google is {avg_time}.")
            else:
                speak("Your internet connection is working, but I couldn't determine the speed.")
        else:
            speak("I couldn't reach the internet. Please check your connection.")
    except Exception as e:
        speak(f"I couldn't test your internet speed. {str(e)}")

def set_reminder(title, minutes):
    """Set a reminder for a specified number of minutes."""
    try:
        minutes = int(minutes)
        speak(f"Setting a reminder for {title} in {minutes} minutes.")
        
        def reminder_callback():
            messagebox.showinfo("Reminder", f"Reminder: {title}")
            speak(f"Reminder: {title}")
        
        # Schedule the reminder
        threading.Timer(minutes * 60, reminder_callback).start()
        
    except Exception as e:
        speak(f"I couldn't set the reminder. {str(e)}")

if __name__ == "__main__":
    create_gui()