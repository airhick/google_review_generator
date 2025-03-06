"""
Configuration file for the Google Reviews Generator
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Google Places API key
# You can get an API key from https://developers.google.com/maps/documentation/places/web-service/get-api-key
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

# Check if API key is set
if not GOOGLE_PLACES_API_KEY:
    print("Warning: GOOGLE_PLACES_API_KEY is not set in .env file")
    print("Please create a .env file with your Google Places API key:")
    print("GOOGLE_PLACES_API_KEY=your_api_key_here") 