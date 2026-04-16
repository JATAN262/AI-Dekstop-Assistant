import re

import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ensure NLTK resources are downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Define command patterns
COMMAND_PATTERNS = {
    'web_search': [
        'search for', 'google', 'look up', 'find', 'find information about', 'search the web for', 'search',
        'look for', 'browse for', 'find online', 'check online for', 'search google for', 'web search'
    ],
    'open_website': [
        'open', 'navigate to', 'go to', 'visit', 'browse'
    ],
    'weather': [
        'weather', 'temperature', 'forecast', 'humidity', 'climate'
    ],
    'news': [
        'news', 'headlines', 'current events', 'latest updates'
    ],
    'system_info': [
        'ip address', 'mac address', 'network', 'system information', 'cpu usage', 'memory usage',
        'battery status', 'disk space'
    ],
    'whatsapp': [
        'send message', 'whatsapp', 'text', 'message'
    ],
    'wikipedia': [
        'wikipedia', 'wiki', 'what is', 'according to wikipedia', 'who is', 'information about'
    ],
    'emergency': [
        'sos', 'emergency', 'help', 'danger', 'alert'
    ],
    'app_control': [
        'open app', 'launch', 'start', 'run program', 'execute'
    ],
    'system_control': [
        'adjust brightness', 'set brightness', 'change brightness',
        'adjust volume', 'set volume', 'change volume',
        'system info', 'system status', 'performance'
    ],
    'file_explorer': [
        'open file explorer', 'show files', 'file manager', 'show documents', 'explore files'
    ],
    'internet_speed': [
        'check internet speed', 'internet speed test', 'network speed', 'internet connection', 'wifi speed'
    ],
    'set_reminder': [
        'remind me', 'set reminder', 'set a reminder', 'create reminder', 'add reminder'
    ]
}

# Intent classification
def preprocess_text(text):
    """Preprocess text by tokenizing, removing stopwords, and lemmatizing"""
    text = text.lower()
    tokens = word_tokenize(text)
    tokens = [lemmatizer.lemmatize(token) for token in tokens if token.isalnum() and token not in stop_words]
    return ' '.join(tokens)

def classify_intent(user_input):
    """Classify the intent of the user's input"""
    processed_input = preprocess_text(user_input)
    
    # Calculate similarity with each command pattern
    scores = {}
    for intent, patterns in COMMAND_PATTERNS.items():
        # Create a corpus with the patterns and the user input
        corpus = [preprocess_text(pattern) for pattern in patterns] + [processed_input]
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)
        
        # Calculate cosine similarity between user input and patterns
        user_vector = tfidf_matrix[-1]
        pattern_vectors = tfidf_matrix[:-1]
        
        # Get the maximum similarity score
        similarity_scores = cosine_similarity(user_vector, pattern_vectors)
        max_score = np.max(similarity_scores)
        scores[intent] = max_score
    
    # Return the intent with the highest score if it's above a threshold
    max_intent = max(scores, key=scores.get)
    if scores[max_intent] > 0.1:  # Threshold for confidence
        return max_intent, scores[max_intent]
    else:
        return 'general_query', 0.0

def extract_entities(user_input, intent):
    """Extract relevant entities based on the identified intent"""
    entities = {}
    
    if intent == 'weather':
        # Extract city name
        city_pattern = r'(?:weather|forecast|temperature)(?:\s+in\s+|\s+for\s+|\s+of\s+)?([A-Za-z\s]+?)(?:\?|$|please)'
        city_match = re.search(city_pattern, user_input, re.IGNORECASE)
        if city_match:
            entities['city'] = city_match.group(1).strip()
    
    elif intent == 'open_website':
        # Extract website name
        website_pattern = r'(?:open|go to|visit|browse|navigate to)\s+(?:the\s+)?(?:website\s+)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        website_match = re.search(website_pattern, user_input, re.IGNORECASE)
        if website_match:
            entities['website'] = website_match.group(1).strip()
    
    elif intent == 'web_search' or intent == 'search':
        # Extract search query - more robust pattern
        search_patterns = [
            r'(?:search|google|look up|find|search for|look for)\s+(?:information about|about|for)?\s+(.+?)(?:\?|$|please)',
            r'(?:search|google|look up)\s+(?:for|on|about)?\s+"?([^"]+?)"?(?:\?|$|please)',
            r'(?:find|get|show me)\s+(?:information|results|details|data)\s+(?:about|for|on)\s+(.+?)(?:\?|$|please)',
            r'(?:can you|please|hey|could you)\s+(?:search|find|google)\s+(?:for|about)?\s+(.+?)(?:\?|$|please)'
        ]
        
        for pattern in search_patterns:
            query_match = re.search(pattern, user_input, re.IGNORECASE)
            if query_match:
                entities['query'] = query_match.group(1).strip()
                break
                
        # Fallback - if no match, use everything after search/google/etc.
        if 'query' not in entities:
            simple_pattern = r'(?:search|google|find|look up)(?:\s+(?:for|about))?\s+(.+)'
            simple_match = re.search(simple_pattern, user_input, re.IGNORECASE)
            if simple_match:
                entities['query'] = simple_match.group(1).strip()
    
    elif intent == 'whatsapp':
        # Extract contact name and message
        contact_pattern = r'(?:send|text|message|whatsapp)\s+(?:a\s+)?(?:message\s+)?(?:to\s+)?([A-Za-z\s]+?)(?:\s+saying|\s+with message|\s+that says|$)'
        contact_match = re.search(contact_pattern, user_input, re.IGNORECASE)
        
        message_pattern = r'(?:saying|that says|with message|with text)\s+"?([^"]+?)"?(?:\?|$|please)'
        message_match = re.search(message_pattern, user_input, re.IGNORECASE)
        
        if contact_match:
            entities['contact'] = contact_match.group(1).strip()
        if message_match:
            entities['message'] = message_match.group(1).strip()
    
    elif intent == 'news':
        # Extract news category
        category_pattern = r'(?:news|headlines|updates)\s+(?:about|on|regarding)?\s+([a-zA-Z]+)'
        category_match = re.search(category_pattern, user_input, re.IGNORECASE)
        if category_match:
            category = category_match.group(1).lower().strip()
            valid_categories = ['general', 'business', 'entertainment', 'health', 'science', 'sports', 'technology']
            if category in valid_categories:
                entities['category'] = category
            else:
                entities['category'] = 'general'
        else:
            entities['category'] = 'general'
    
    elif intent == 'wikipedia':
        # Extract search query
        query_pattern = r'(?:wikipedia|wiki|search|look up|information about)\s+(?:for\s+)?(.+?)(?:\?|$|please)'
        query_match = re.search(query_pattern, user_input, re.IGNORECASE)
        if query_match:
            entities['query'] = query_match.group(1).strip()
    
    elif intent == 'app_control':
        # Extract application name
        app_pattern = r'(?:open|launch|start|run)\s+(?:the\s+)?(?:application\s+)?([A-Za-z\s]+?)(?:\s+application|\?|$|please)'
        app_match = re.search(app_pattern, user_input, re.IGNORECASE)
        if app_match:
            app_name = app_match.group(1).strip().lower()
            # Map common application names
            app_map = {
                'notepad': 'notepad',
                'calculator': 'calc',
                'paint': 'mspaint',
                'command prompt': 'cmd',
                'cmd': 'cmd',
                'browser': 'msedge',
                'edge': 'msedge',
                'chrome': 'chrome',
                'word': 'winword',
                'excel': 'excel',
                'powerpoint': 'powerpnt'
            }
            entities['app_name'] = app_map.get(app_name, app_name)
    
    elif intent == 'system_control':
        # Extract brightness/volume level
        level_pattern = r'(?:set|change|adjust)\s+(?:the\s+)?(?:brightness|volume)\s+(?:to\s+)?(\d+)(?:\s*%)?'
        level_match = re.search(level_pattern, user_input, re.IGNORECASE)
        if level_match:
            level = int(level_match.group(1))
            if 'brightness' in user_input.lower():
                entities['brightness'] = level
            elif 'volume' in user_input.lower():
                entities['volume'] = level
    
    elif intent == 'set_reminder':
        # Extract reminder title and time
        reminder_pattern = r'(?:remind|reminder|remind me)(?:\s+(?:to|about))?\s+(.+?)(?:\s+in\s+(\d+)\s+minutes?)?(?:\?|$|please)'
        reminder_match = re.search(reminder_pattern, user_input, re.IGNORECASE)
        if reminder_match:
            entities['title'] = reminder_match.group(1).strip()
            if reminder_match.group(2):
                entities['minutes'] = int(reminder_match.group(2))
            else:
                entities['minutes'] = 5  # Default to 5 minutes
    
    elif intent == 'internet_speed':
        # No specific entities needed for internet speed test
        pass
    
    elif intent == 'file_explorer':
        # Extract path if specified
        path_pattern = r'(?:open|show|launch)(?:\s+(?:file explorer|files|documents))(?:\s+(?:in|at|for))?\s+(.+?)(?:\?|$|please)'
        path_match = re.search(path_pattern, user_input, re.IGNORECASE)
        if path_match:
            entities['path'] = path_match.group(1).strip()
    
    return entities

def process_nlp(user_input):
    """Process user input with NLP techniques to understand intent and extract entities"""
    intent, confidence = classify_intent(user_input)
    entities = extract_entities(user_input, intent)
    
    return {
        'input': user_input,
        'intent': intent,
        'confidence': float(confidence),
        'entities': entities
    }

# Example usage
if __name__ == "__main__":
    # Test the NLP processor
    test_inputs = [
        "What's the weather like in New York?",
        "Open youtube.com",
        "Send a message to Mom saying \"I'll be home soon\"",
        "Tell me the latest sports news",
        "Search Wikipedia for Albert Einstein",
        "Open notepad application"
    ]
    
    for test_input in test_inputs:
        result = process_nlp(test_input)
        print(f"Input: {test_input}")
        print(f"Intent: {result['intent']} (confidence: {result['confidence']:.2f})")
        print(f"Entities: {result['entities']}")
        print("-" * 50) 