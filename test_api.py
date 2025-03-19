#!/usr/bin/env python3
"""
Test Google Places API

This script tests the Google Places API functionality for retrieving place IDs.
"""

import re
import urllib.parse
import os
import requests
import sys

def get_place_id_from_api(business_url, api_key):
    """Get place ID from Google Places API using the business URL"""
    try:
        print(f"Using Google Places API key: {api_key[:10]}...")
        
        # Extract business name and location from URL
        business_name = None
        location = None
        
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
                print(f"Extracted business name: {business_name}")
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
                print(f"Extracted business name from path: {business_name}")
        
        if not business_name:
            print("❌ Could not extract business name from URL")
            return None
        
        # Clean up business name - remove any @ and following text
        if '@' in business_name:
            business_name = business_name.split('@')[0]
        
        # Try to extract location from URL
        location_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', business_url)
        if location_match:
            lat = location_match.group(1)
            lng = location_match.group(2)
            location = f"{lat},{lng}"
            print(f"Extracted location: {location}")
        
        print(f"Using business name for API request: {business_name}")
        
        # Use Google Places API to find the place ID
        # First try with text search
        search_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={urllib.parse.quote(business_name)}&inputtype=textquery&fields=place_id,name,formatted_address&key={api_key}"
        
        # Add location bias if available
        if location:
            search_url += f"&locationbias=circle:5000@{location}"
        
        print(f"Making API request to: {search_url}")
        
        response = requests.get(search_url)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('candidates'):
            place_id = data['candidates'][0]['place_id']
            place_name = data['candidates'][0].get('name', 'Unknown')
            place_address = data['candidates'][0].get('formatted_address', 'Unknown')
            
            print(f"✅ Found place ID using Google Places API: {place_id}")
            print(f"Business Name: {place_name}")
            print(f"Address: {place_address}")
            
            return place_id
        else:
            print(f"❌ API Error: {data.get('status')}")
            print(f"API Response: {data}")
            
            # If first method fails, try with nearby search
            if location:
                print("Trying nearby search instead...")
                nearby_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius=500&keyword={urllib.parse.quote(business_name)}&key={api_key}"
                
                print(f"Making API request to: {nearby_url}")
                
                response = requests.get(nearby_url)
                data = response.json()
                
                if data.get('status') == 'OK' and data.get('results'):
                    place_id = data['results'][0]['place_id']
                    place_name = data['results'][0].get('name', 'Unknown')
                    
                    print(f"✅ Found place ID using nearby search: {place_id}")
                    print(f"Business Name: {place_name}")
                    
                    return place_id
                else:
                    print(f"❌ Nearby search API Error: {data.get('status')}")
                    print(f"API Response: {data}")
            
            print(f"❌ All API methods failed")
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
    """Main function to test Google Places API"""
    print("=" * 60)
    print("                TEST GOOGLE PLACES API                ")
    print("=" * 60)
    print()
    
    # Set API key
    api_key = "AIzaSyDl29jzOdfmgKKuoI-j5lgrCaCgp-A6ygo"
    
    # Get business URL from command line or prompt
    if len(sys.argv) > 1:
        business_url = sys.argv[1]
    else:
        business_url = input("Enter Google Maps URL: ").strip()
    
    if not business_url:
        print("❌ Business URL cannot be empty")
        return
    
    print(f"Testing URL: {business_url}")
    print()
    
    # Get place ID from API
    place_id = get_place_id_from_api(business_url, api_key)
    
    # Generate direct review URL if place ID was found
    if place_id:
        direct_url = get_direct_review_url(place_id)
        print(f"\nDirect Review URL: {direct_url}")
    else:
        print("\n❌ Failed to generate direct review URL")

if __name__ == "__main__":
    main() 