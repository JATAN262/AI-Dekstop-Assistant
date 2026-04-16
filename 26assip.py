import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import speech_recognition as sr
import pyttsx3
import webbrowser
import wikipedia
import re
from datetime import datetime

# Initialize the text-to-speech engine
engine = None
try:
    engine = pyttsx3.init()
    if engine:
        engine.setProperty('rate', 175)
        engine.setProperty('volume', 1.0)
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
except Exception as e:
    print(f"Warning: Could not initialize text-to-speech engine: {e}")
    engine = None

def speak(audio):
    """Function to make the assistant speak with error handling"""
    try:
        if engine is not None:
            text = str(audio).strip()
            if text:
                engine.say(text)
                engine.runAndWait()
                print(f"Assistant: {text}")
        else:
            print(f"Assistant (TTS Disabled): {audio}")
    except Exception as e:
        print(f"Error in speak function: {e}")

def take_command():
    """Optimized speech recognition."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.dynamic_energy_threshold = True
        r.energy_threshold = 300
        r.dynamic_energy_adjustment_ratio = 1.5
        try:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            print("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            print(f"User: {query}")
            return query.lower()
        except sr.UnknownValueError:
            speak("I didn't catch that. Can you say it again?")
            return ""
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

def search_wikipedia(query):
    """Searches Wikipedia based on user input."""
    try:
        speak("Searching Wikipedia...")
        # Remove 'wikipedia' from the query to get the topic
        query = re.sub(r'wikipedia', '', query, flags=re.IGNORECASE).strip()
        if not query:
            speak("What should I search on Wikipedia?")
            return
            
        results = wikipedia.summary(query, sentences=2)
        speak("According to Wikipedia")
        print(results)
        speak(results)
    except wikipedia.exceptions.DisambiguationError:
        speak("Your query is too broad. Please be more specific.")
    except wikipedia.exceptions.PageError:
        speak("I couldn't find anything on Wikipedia for that.")
    except Exception as e:
        speak(f"An error occurred with Wikipedia search: {e}")

def open_website(query):
    """Handles website opening."""
    # Extract domain or just use the query if it looks like a url
    domain_pattern = r"\b(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})\b"
    match = re.search(domain_pattern, query)
    
    if match:
        domain = match.group(0)
        if not domain.startswith("http"):
            domain = "https://" + domain
        webbrowser.open(domain)
        speak(f"Opening website {domain}")
    else:
        # Check for common sites by name
        common_sites = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "facebook": "https://www.facebook.com",
            "instagram": "https://www.instagram.com",
            "twitter": "https://www.twitter.com",
            "linkedin": "https://www.linkedin.com",
            "github": "https://github.com",
            "stackoverflow": "https://stackoverflow.com"
        }
        
        found = False
        for site, url in common_sites.items():
            if site in query.lower():
                webbrowser.open(url)
                speak(f"Opening {site}")
                found = True
                break
        
        if not found:
            # Fallback to Google search if no domain or known site found
            search_query = query.replace('open', '').replace('website', '').strip()
            if search_query:
                search_url = f"https://www.google.com/search?q={search_query}"
                webbrowser.open(search_url)
                speak(f"Searching Google for {search_query}")
            else:
                speak("Which website should I open?")

def web_search(query):
    """Function to search the web for any query."""
    # Remove 'search' or 'google' keywords
    query = re.sub(r'(search|web search|google|find|look up)', '', query, flags=re.IGNORECASE).strip()
    if not query:
        speak("What do you want me to search for?")
        return
        
    search_url = f"https://www.google.com/search?q={query}"
    webbrowser.open(search_url)
    speak(f"Searching the web for {query}")

def process_command(command):
    """Process the voice command"""
    if not command:
        return
    
    command = command.lower()
    
    # 1. Wikipedia
    if "wikipedia" in command:
        search_wikipedia(command)
        return

    # 2. Open Website (prioritize "open" keyword)
    if "open" in command:
        open_website(command)
        return

    # 3. Web Search
    if any(keyword in command for keyword in ["search", "google", "find", "look up"]):
        web_search(command)
        return

    # If no specific keyword matched but command exists, maybe default to search or ask again?
    # User said "only this 3 fraute mast be workable".
    speak("I can only help with Wikipedia, opening websites, and web searching.")

def update_status(status="ready"):
    """Updates the status indicator in the GUI safely."""
    def _update():
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
    
    if 'root' in globals() and root:
        root.after(0, _update)

def start_assistant():
    """Start the assistant in a separate thread"""
    try:
        start_button.configure(state='disabled')
        update_status("listening")
        
        assistant_thread = threading.Thread(target=run_assistant)
        assistant_thread.daemon = True
        assistant_thread.start()
        
    except Exception as e:
        error_msg = f"Error starting assistant: {str(e)}"
        print(error_msg)
        messagebox.showerror("Error", error_msg)
        start_button.configure(state='normal')
        update_status("ready")

def run_assistant():
    """Function that runs in a separate thread"""
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
        if 'root' in globals() and root:
            root.after(0, lambda: messagebox.showerror("Error", error_msg))
            root.after(0, lambda: start_button.configure(state='normal'))
            root.after(0, lambda: update_status("ready"))

def create_gui():
    global root, start_button, status_label, status_indicator, status_canvas
    root = tk.Tk()
    root.title("AI Assistant")
    root.geometry("400x300")
    
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
    
    start_button = ttk.Button(
        button_frame,
        text="Start Assistant",
        command=start_assistant,
        style='Accent.TButton'
    )
    start_button.pack(pady=10)
    
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
        text="v1.0.0 (Lite)",
        style='TLabel'
    )
    version_label.pack(side=tk.BOTTOM, pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    create_gui()
