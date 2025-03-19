#!/usr/bin/env python3
"""
Test Place ID Extraction

This script tests the extraction of place IDs from Google Maps URLs.
"""

import re
import urllib.parse
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def extract_place_id_from_url(url):
    """Extract place ID from a Google Maps URL"""
    print(f"Testing URL: {url}")
    
    # First check for standard place_id or placeid parameters
    place_id_patterns = [
        r'place_id=([^&]+)',
        r'placeid=([^&]+)'
    ]
    
    for pattern in place_id_patterns:
        match = re.search(pattern, url)
        if match:
            print(f"✅ Found place ID using pattern: {pattern}")
            return match.group(1)
    
    # Check for CID pattern (0x...:0x...)
    cid_pattern = r'(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)'
    match = re.search(cid_pattern, url)
    if match:
        print(f"✅ Found CID using pattern: {cid_pattern}")
        # For CID pattern, the entire match is the place ID
        return match.group(0)
    
    # Check for data patterns
    data_patterns = [
        r'data=!3m1!4b1!4m5!3m4!1s([^!]+)',
        r'data=!3m1!4b1!4m[0-9]+!3m[0-9]+!1s([^!]+)'
    ]
    
    for pattern in data_patterns:
        match = re.search(pattern, url)
        if match:
            print(f"✅ Found place ID using data pattern: {pattern}")
            return match.group(1)
    
    # Direct extraction from URL path for specific format
    try:
        # Parse the URL
        parsed_url = urllib.parse.urlparse(url)
        
        # Check if it's a Google Maps URL
        if 'google.com/maps' in parsed_url.netloc + parsed_url.path:
            # Look for the CID in the path or query
            path_and_query = parsed_url.path + '?' + parsed_url.query
            cid_match = re.search(r'!1s(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)', path_and_query)
            if cid_match:
                print(f"✅ Found CID using direct path extraction")
                return cid_match.group(1)
    except Exception as e:
        print(f"❌ Error in direct extraction: {str(e)}")
    
    print("❌ Could not extract place ID from URL")
    return None

def get_place_id_from_api(business_url):
    """Get place ID from Google Places API using the business URL"""
    try:
        # Get API key from environment variable
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            print("❌ Google Places API key not found in .env file")
            return None
        
        # Extract business name and location from URL
        business_name = None
        
        # Try different patterns to extract business name from URL
        patterns = [
            r'place/([^/@]+)/@',  # Standard format: place/BusinessName/@coordinates
            r'place/([^/]+)$',    # Format ending with business name
            r'place/([^/]+)/',    # Format with business name followed by more path
            r'place/([^?]+)',     # Format with query parameters
            r'q=([^&]+)'          # Format with q parameter
        ]
        
        for pattern in patterns:
            match = re.search(pattern, business_url)
            if match:
                business_name = match.group(1)
                business_name = business_name.replace('+', ' ')
                business_name = urllib.parse.unquote(business_name)
                print(f"✅ Extracted business name using pattern: {pattern}")
                break
        
        # If we still don't have a business name, try to extract it from the URL path
        if not business_name:
            # Parse the URL and extract the last part of the path
            parsed_url = urllib.parse.urlparse(business_url)
            path_parts = parsed_url.path.split('/')
            if len(path_parts) > 2:  # Ensure there's at least one part after /place/
                business_name = path_parts[-1]  # Get the last part of the path
                business_name = business_name.replace('+', ' ')
                business_name = urllib.parse.unquote(business_name)
                print(f"✅ Extracted business name from path: {business_name}")
        
        if not business_name:
            print("❌ Could not extract business name from URL")
            return None
        
        # Clean up business name - remove any @ and following text
        if '@' in business_name:
            business_name = business_name.split('@')[0]
        
        print(f"Final business name: {business_name}")
        
        # Use Google Places API to find the place ID
        search_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={urllib.parse.quote(business_name)}&inputtype=textquery&fields=place_id&key={api_key}"
        
        print(f"API URL: {search_url}")
        
        response = requests.get(search_url)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('candidates'):
            place_id = data['candidates'][0]['place_id']
            print(f"✅ Found place ID using Google Places API: {place_id}")
            return place_id
        else:
            print(f"❌ API Error: {data.get('status')}")
            print(f"API Response: {data}")
            return None
    except Exception as e:
        print(f"❌ Error getting place ID from API: {str(e)}")
        return None

def get_direct_review_url(place_id):
    """Generate a direct review URL from a place ID"""
    if place_id:
        return f"https://search.google.com/local/writereview?placeid={place_id}"
    return None

def main():
    """Main function to test place ID extraction"""
    print("=" * 60)
    print("                TEST PLACE ID EXTRACTION                ")
    print("=" * 60)
    print()
    
    # Test URLs
    test_urls = [
        "https://www.google.com/maps/place/Pulse+Incubateur+Hes/@46.2090176,6.1362299,85m/data=!3m1!1e3!4m6!3m5!1s0x478c64da24055555:0x49bef78604a2d7ad!8m2!3d46.2091643!4d6.1361713!16s%2Fg%2F11j1hyv8hh?entry=ttu&g_ep=EgoyMDI1MDMwNC4wIKXMDSoASAFQAw%3D%3D",
        "https://www.google.com/maps/place/Lancer+de+hache+Gen%C3%A8ve+-+Axvetik/@46.200488,6.1546484,967m/data=!3m2!1e3!4b1!4m6!3m5!1s0x478c6599e5dc6701:0x3d7c75ddf510d18e!8m2!3d46.2004843!4d6.1572233!16s%2Fg%2F11ptpkvfbb?entry=ttu&g_ep=EgoyMDI1MDMwNC4wIKXMDSoASAFQAw%3D%3D",
        "https://www.google.com/maps/place/Restaurant+Example/@40.7128,-74.0060,15z/data=!4m5!3m4!1s0x0:0x0!8m2!3d40.7128!4d-74.0060",
        "https://www.google.com/maps/place/Business+Name?place_id=ChIJN1t_tDeuEmsRUsoyG83frY4"
    ]
    
    for url in test_urls:
        print("\n" + "=" * 60)
        
        # Try direct extraction
        place_id = extract_place_id_from_url(url)
        
        # If direct extraction fails, try API
        if not place_id:
            print("\nDirect extraction failed, trying API...")
            place_id = get_place_id_from_api(url)
        
        # Generate direct review URL if place ID was found
        if place_id:
            direct_url = get_direct_review_url(place_id)
            print(f"\nDirect Review URL: {direct_url}")
        else:
            print("\n❌ Failed to generate direct review URL")
        
        print("=" * 60 + "\n")

if __name__ == "__main__":
    main() 