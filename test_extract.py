#!/usr/bin/env python3
"""
Test script to extract place ID from Google Maps URL
"""

import re
import sys
import urllib.parse

def print_url_parts(url):
    """Print URL parts in a readable format"""
    print("\nURL ANALYSIS:")
    print("-" * 50)
    
    # Parse the URL
    parsed = urllib.parse.urlparse(url)
    
    print(f"Scheme: {parsed.scheme}")
    print(f"Netloc: {parsed.netloc}")
    print(f"Path: {parsed.path}")
    
    # Parse the query parameters
    query_params = urllib.parse.parse_qs(parsed.query)
    if query_params:
        print("Query parameters:")
        for key, value in query_params.items():
            print(f"  {key}: {value[0]}")
    
    # Parse the path segments
    path_segments = parsed.path.split('/')
    print("Path segments:")
    for i, segment in enumerate(path_segments):
        if segment:
            print(f"  {i}: {segment}")
    
    # If there's a data parameter, parse it
    if 'data=' in url:
        data_part = url.split('data=')[1].split('&')[0]
        data_segments = data_part.split('!')
        print("Data segments:")
        for i, segment in enumerate(data_segments):
            if segment:
                print(f"  {i}: {segment}")
    
    print("-" * 50)

def extract_place_id(url):
    """Extract place ID from Google Maps URL using various patterns"""
    
    print(f"Testing URL: {url}")
    
    # Print URL parts for analysis
    print_url_parts(url)
    
    # Pattern 1: Check for place_id parameter in URL
    place_id_match = re.search(r'[?&]place_id=([^&]+)', url)
    if place_id_match:
        place_id = place_id_match.group(1)
        print(f"Pattern 1 - Found place ID in URL parameter: {place_id}")
        return place_id
    
    # Pattern 2: Check for placeid parameter in URL (used in review URLs)
    placeid_match = re.search(r'[?&]placeid=([^&]+)', url)
    if placeid_match:
        place_id = placeid_match.group(1)
        print(f"Pattern 2 - Found place ID in URL parameter: {place_id}")
        return place_id
    
    # Pattern 3: Check for ChIJ format place ID in URL
    chij_match = re.search(r'(ChIJ[a-zA-Z0-9_-]+)', url)
    if chij_match:
        place_id = chij_match.group(1)
        print(f"Pattern 3 - Found ChIJ format place ID in URL: {place_id}")
        return place_id
    
    # Pattern 4: Extract from data segment (most reliable for Google Maps URLs)
    if 'data=' in url:
        try:
            data_part = url.split('data=')[1].split('&')[0]
            data_segments = data_part.split('!')
            
            # Look for the segment that starts with '1s' and contains the place ID
            for segment in data_segments:
                if segment.startswith('1s'):
                    place_id = segment[2:]  # Remove the '1s' prefix
                    print(f"Pattern 4 - Found place ID in data segment: {place_id}")
                    return place_id
        except Exception as e:
            print(f"Error parsing data segment: {str(e)}")
    
    # Pattern 5: Check for maps URLs with !1s prefix (common in Google Maps URLs)
    place_id_in_path = re.search(r'!1s(0x[0-9a-f]+:[0-9a-f]+)', url)
    if place_id_in_path:
        place_id = place_id_in_path.group(1)
        print(f"Pattern 5 - Found place ID in URL path: {place_id}")
        return place_id
    
    # Pattern 6: Check for maps URLs with !1s prefix (ChIJ format)
    place_id_in_path_chij = re.search(r'!1s(ChIJ[a-zA-Z0-9_-]+)', url)
    if place_id_in_path_chij:
        place_id = place_id_in_path_chij.group(1)
        print(f"Pattern 6 - Found ChIJ format place ID in URL path: {place_id}")
        return place_id
    
    # Pattern 7: Check for CID format in URL
    cid_match = re.search(r'[?&]cid=([0-9]+)', url)
    if cid_match:
        place_id = cid_match.group(1)
        print(f"Pattern 7 - Found CID in URL: {place_id}")
        return place_id
    
    # Pattern 8: Look for 0x format in any part of the URL
    hex_match = re.search(r'(0x[0-9a-f]+:[0-9a-f]+)', url)
    if hex_match:
        place_id = hex_match.group(1)
        print(f"Pattern 8 - Found hex format place ID in URL: {place_id}")
        return place_id
    
    print("No place ID found in URL")
    return None

if __name__ == "__main__":
    # Use URL from command line or default to the one in business_url.txt
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        try:
            with open("business_url.txt", "r") as f:
                url = f.read().strip()
        except:
            url = "https://www.google.com/maps/place/Chez+Milo+Bar/@46.2044975,6.1216524,1934m/data=!3m2!1e3!4b1!4m6!3m5!1s0x478c64c94ab64313:0x9123b4804e731bbd!8m2!3d46.2044938!4d6.1242273!16s%2Fg%2F11hzg0vg96?entry=ttu&g_ep=EgoyMDI1MDIyNi4xIKXMDSoASAFQAw%3D%3D"
    
    place_id = extract_place_id(url)
    
    if place_id:
        print(f"\nExtracted place ID: {place_id}")
        print(f"Direct review URL: https://search.google.com/local/writereview?placeid={place_id}")
    else:
        print("\nFailed to extract place ID") 