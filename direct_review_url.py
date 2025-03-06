#!/usr/bin/env python3
"""
Direct Review URL Generator

This script reads a business URL from business_url.txt, extracts the business name,
uses the Google Places API to get the place ID, and generates a direct review URL.
"""

import re
import requests
import traceback
import os
import datetime
import urllib.parse
from pathlib import Path
from fake_useragent import UserAgent
import time
from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import GOOGLE_PLACES_API_KEY

def create_debug_folder():
    """Create a debug folder with timestamp"""
    # Create debug_files directory if it doesn't exist
    os.makedirs("debug_files", exist_ok=True)
    
    # Create a timestamped folder for this run
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_folder = os.path.join("debug_files", f"debug_{timestamp}")
    os.makedirs(debug_folder, exist_ok=True)
    
    print(f"Debug files will be saved to: {debug_folder}")
    return debug_folder

def log_message(debug_folder, message):
    """Log a message to the debug log file"""
    log_file = os.path.join(debug_folder, "direct_url_log.txt")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)

def extract_business_name_from_url(url, driver=None, debug_folder=None):
    """
    Extract the business name from a Google Maps URL
    
    Args:
        url: The Google Maps URL
        driver: Optional Selenium WebDriver instance
        debug_folder: Path to debug folder for logging
        
    Returns:
        str: The business name if found, None otherwise
    """
    try:
        if debug_folder:
            log_message(debug_folder, f"Extracting business name from URL: {url}")
        else:
            print(f"Extracting business name from URL: {url}")
        
        # Try to extract business name from URL path
        # Example: https://www.google.com/maps/place/Business+Name/@coordinates
        business_name = None
        
        # Pattern 1: /place/Business+Name/
        place_match = re.search(r'/place/([^/@]+)', url)
        if place_match:
            business_name = place_match.group(1)
            business_name = business_name.replace('+', ' ')
            if debug_folder:
                log_message(debug_folder, f"Found business name in URL path: {business_name}")
            else:
                print(f"Found business name in URL path: {business_name}")
            return business_name
        
        # Handle shortened URLs (maps.app.goo.gl)
        if 'maps.app.goo.gl' in url or 'goo.gl' in url:
            if debug_folder:
                log_message(debug_folder, "Detected shortened URL, following redirect...")
            else:
                print("Detected shortened URL, following redirect...")
            
            # First try with requests to follow the redirect
            try:
                ua = UserAgent()
                headers = {
                    'User-Agent': ua.random,
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                response = requests.head(url, headers=headers, allow_redirects=True)
                
                if response.url != url:
                    if debug_folder:
                        log_message(debug_folder, f"URL redirected to: {response.url}")
                    else:
                        print(f"URL redirected to: {response.url}")
                    
                    # Try to extract business name from the redirected URL
                    return extract_business_name_from_url(response.url, driver, debug_folder)
            except Exception as e:
                if debug_folder:
                    log_message(debug_folder, f"Error following redirect with requests: {str(e)}")
                    log_message(debug_folder, "Falling back to Selenium for redirect...")
                else:
                    print(f"Error following redirect with requests: {str(e)}")
        
        # If we couldn't extract the business name from the URL, use Selenium to load the page and get it
        if business_name is None:
            if driver is None:
                if debug_folder:
                    log_message(debug_folder, "Initializing Chrome driver...")
                else:
                    print("Initializing Chrome driver...")
                driver = initialize_chrome_driver()
                
            if debug_folder:
                log_message(debug_folder, f"Loading URL with Chrome: {url}")
            else:
                print(f"Loading URL with Chrome: {url}")
            driver.get(url)
            time.sleep(3)
            
            # Check if we're on a consent page
            if 'consent.google.com' in driver.current_url:
                if debug_folder:
                    log_message(debug_folder, "Detected Google consent page, clicking agree button...")
                else:
                    print("Detected Google consent page, clicking agree button...")
                try:
                    # Try to click the agree button
                    agree_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Agree')]")
                    if agree_buttons:
                        agree_buttons[0].click()
                        time.sleep(3)
                    else:
                        # Try other possible button texts
                        for text in ["I agree", "Accept", "Accept all", "Agree to all"]:
                            buttons = driver.find_elements(By.XPATH, f"//button[contains(., '{text}')]")
                            if buttons:
                                buttons[0].click()
                                time.sleep(3)
                                break
                except Exception as e:
                    if debug_folder:
                        log_message(debug_folder, f"Error clicking agree button: {str(e)}")
                    else:
                        print(f"Error clicking agree button: {str(e)}")
            
            # Try to get the business name from the page title
            try:
                # Wait for the page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "title"))
                )
                
                # Get the page title
                title = driver.title
                
                # Extract business name from title (format: "Business Name - Google Maps")
                if " - Google Maps" in title:
                    business_name = title.replace(" - Google Maps", "").strip()
                    if debug_folder:
                        log_message(debug_folder, f"Found business name in page title: {business_name}")
                    else:
                        print(f"Found business name in page title: {business_name}")
                    return business_name
                
                # Try to find the business name in the heading
                headings = driver.find_elements(By.XPATH, "//h1")
                if headings:
                    business_name = headings[0].text.strip()
                    if business_name:
                        if debug_folder:
                            log_message(debug_folder, f"Found business name in heading: {business_name}")
                        else:
                            print(f"Found business name in heading: {business_name}")
                        return business_name
            except Exception as e:
                if debug_folder:
                    log_message(debug_folder, f"Error extracting business name from page: {str(e)}")
                else:
                    print(f"Error extracting business name from page: {str(e)}")
        
        return business_name
    
    except Exception as e:
        if debug_folder:
            log_message(debug_folder, f"Error extracting business name: {str(e)}")
            log_message(debug_folder, traceback.format_exc())
        else:
            print(f"Error extracting business name: {str(e)}")
            print(traceback.format_exc())
        return None

def extract_place_id_from_url(url, driver=None, debug_folder=None):
    """
    Extract the place ID from a Google Maps URL (fallback method)
    
    Args:
        url: The Google Maps URL
        driver: Optional Selenium WebDriver instance
        debug_folder: Path to debug folder for logging
        
    Returns:
        str: The place ID if found, None otherwise
    """
    try:
        if debug_folder:
            log_message(debug_folder, f"Extracting place ID from URL: {url}")
        else:
            print(f"Extracting place ID from URL: {url}")
        
        # Try to extract place ID directly from URL
        
        # Check for place_id parameter in URL
        place_id_match = re.search(r'[?&]place_id=([^&]+)', url)
        if place_id_match:
            place_id = place_id_match.group(1)
            if debug_folder:
                log_message(debug_folder, f"Found place ID in URL parameter: {place_id}")
            else:
                print(f"Found place ID in URL parameter: {place_id}")
            return place_id
            
        # Check for placeid parameter in URL (used in review URLs)
        placeid_match = re.search(r'[?&]placeid=([^&]+)', url)
        if placeid_match:
            place_id = placeid_match.group(1)
            if debug_folder:
                log_message(debug_folder, f"Found place ID in URL parameter: {place_id}")
            else:
                print(f"Found place ID in URL parameter: {place_id}")
            return place_id
            
        # Extract from data segment (most reliable for Google Maps URLs)
        if 'data=' in url:
            try:
                data_part = url.split('data=')[1].split('&')[0]
                data_segments = data_part.split('!')
                
                # Look for the segment that starts with '1s' and contains the place ID
                for segment in data_segments:
                    if segment.startswith('1s'):
                        place_id = segment[2:]  # Remove the '1s' prefix
                        if debug_folder:
                            log_message(debug_folder, f"Found place ID in data segment: {place_id}")
                        else:
                            print(f"Found place ID in data segment: {place_id}")
                        return place_id
            except Exception as e:
                if debug_folder:
                    log_message(debug_folder, f"Error parsing data segment: {str(e)}")
                else:
                    print(f"Error parsing data segment: {str(e)}")
        
        # Check for ChIJ format place ID in URL
        chij_match = re.search(r'(ChIJ[a-zA-Z0-9_-]+)', url)
        if chij_match:
            place_id = chij_match.group(1)
            if debug_folder:
                log_message(debug_folder, f"Found ChIJ format place ID in URL: {place_id}")
            else:
                print(f"Found ChIJ format place ID in URL: {place_id}")
            return place_id
            
        # Check for place ID in URL path (format: /place/Name/@lat,lng,zoom/data=!3m1!...!1s0x...)
        place_id_in_path = re.search(r'!1s(0x[0-9a-f]+:[0-9a-f]+)', url)
        if place_id_in_path:
            place_id = place_id_in_path.group(1)
            if debug_folder:
                log_message(debug_folder, f"Found place ID in URL path: {place_id}")
            else:
                print(f"Found place ID in URL path: {place_id}")
            return place_id
            
        # Check for place ID in URL path (ChIJ format)
        place_id_in_path_chij = re.search(r'!1s(ChIJ[a-zA-Z0-9_-]+)', url)
        if place_id_in_path_chij:
            place_id = place_id_in_path_chij.group(1)
            if debug_folder:
                log_message(debug_folder, f"Found ChIJ format place ID in URL path: {place_id}")
            else:
                print(f"Found ChIJ format place ID in URL path: {place_id}")
            return place_id
        
        # Handle shortened URLs (maps.app.goo.gl)
        if 'maps.app.goo.gl' in url or 'goo.gl' in url:
            if debug_folder:
                log_message(debug_folder, "Detected shortened URL, following redirect...")
            else:
                print("Detected shortened URL, following redirect...")
            
            # First try with requests to follow the redirect
            try:
                ua = UserAgent()
                headers = {
                    'User-Agent': ua.random,
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                response = requests.head(url, headers=headers, allow_redirects=True)
                
                if response.url != url:
                    if debug_folder:
                        log_message(debug_folder, f"URL redirected to: {response.url}")
                    else:
                        print(f"URL redirected to: {response.url}")
                    
                    # Check if we got a consent page
                    if 'consent.google.com' in response.url:
                        if debug_folder:
                            log_message(debug_folder, "Detected Google consent page, extracting continue parameter...")
                        else:
                            print("Detected Google consent page, extracting continue parameter...")
                        continue_match = re.search(r'continue=([^&]+)', response.url)
                        if continue_match:
                            continue_url = continue_match.group(1)
                            # URL decode the continue parameter
                            continue_url = urllib.parse.unquote(continue_url)
                            if debug_folder:
                                log_message(debug_folder, f"Extracted continue URL: {continue_url}")
                            else:
                                print(f"Extracted continue URL: {continue_url}")
                            
                            # Try to extract place ID from the continue URL
                            place_id_in_continue = re.search(r'!1s(0x[0-9a-f]+:[0-9a-f]+)', continue_url)
                            if place_id_in_continue:
                                place_id = place_id_in_continue.group(1)
                                if debug_folder:
                                    log_message(debug_folder, f"Found place ID in continue URL: {place_id}")
                                else:
                                    print(f"Found place ID in continue URL: {place_id}")
                                return place_id
                                
                            # Try to extract ChIJ format place ID from the continue URL
                            place_id_in_continue_chij = re.search(r'!1s(ChIJ[a-zA-Z0-9_-]+)', continue_url)
                            if place_id_in_continue_chij:
                                place_id = place_id_in_continue_chij.group(1)
                                if debug_folder:
                                    log_message(debug_folder, f"Found ChIJ format place ID in continue URL: {place_id}")
                                else:
                                    print(f"Found ChIJ format place ID in continue URL: {place_id}")
                                return place_id
                    
                    # Try to extract place ID from the redirected URL
                    return extract_place_id_from_url(response.url, driver, debug_folder)
            except Exception as e:
                if debug_folder:
                    log_message(debug_folder, f"Error following redirect with requests: {str(e)}")
                    log_message(debug_folder, "Falling back to Selenium for redirect...")
                else:
                    print(f"Error following redirect with requests: {str(e)}")
                    print("Falling back to Selenium for redirect...")
        
        # If requests failed or didn't find a place ID, try with Selenium
        if driver is None:
            if debug_folder:
                log_message(debug_folder, "Initializing Chrome driver...")
            else:
                print("Initializing Chrome driver...")
            driver = initialize_chrome_driver()
            
        if debug_folder:
            log_message(debug_folder, f"Loading URL with Chrome: {url}")
        else:
            print(f"Loading URL with Chrome: {url}")
        driver.get(url)
        time.sleep(3)
        
        # Check if we're on a consent page
        if 'consent.google.com' in driver.current_url:
            if debug_folder:
                log_message(debug_folder, "Detected Google consent page, clicking agree button...")
            else:
                print("Detected Google consent page, clicking agree button...")
            try:
                # Try to click the agree button
                agree_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Agree')]")
                if agree_buttons:
                    agree_buttons[0].click()
                    time.sleep(3)
                else:
                    # Try other possible button texts
                    for text in ["I agree", "Accept", "Accept all", "Agree to all"]:
                        buttons = driver.find_elements(By.XPATH, f"//button[contains(., '{text}')]")
                        if buttons:
                            buttons[0].click()
                            time.sleep(3)
                            break
            except Exception as e:
                if debug_folder:
                    log_message(debug_folder, f"Error clicking agree button: {str(e)}")
                else:
                    print(f"Error clicking agree button: {str(e)}")
        
        if debug_folder:
            log_message(debug_folder, f"Current URL after redirect: {driver.current_url}")
        else:
            print(f"Current URL after redirect: {driver.current_url}")
        
        # Try to extract place ID from the current URL
        redirected_url = driver.current_url
        
        # Check if we're on a maps URL
        if 'google.com/maps' in redirected_url:
            # Try to extract place ID from the page source
            match = re.search(r'"ChIJ[^"]+"|"0x[0-9a-f]+:[0-9a-f]+"', driver.page_source)
            if match:
                place_id = match.group(0).strip('"')
                if debug_folder:
                    log_message(debug_folder, f"Found place ID in page source: {place_id}")
                else:
                    print(f"Found place ID in page source: {place_id}")
                return place_id
                
            # Try to extract from the URL
            return extract_place_id_from_url(redirected_url, driver, debug_folder)
            
        # If we couldn't extract from the URL, try to find a review button
        try:
            review_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Review')]")
            if review_buttons:
                # Click the review button to get to the review page
                review_buttons[0].click()
                time.sleep(3)
                
                # Now we should be on the review page, extract the place ID from the URL
                review_url = driver.current_url
                if debug_folder:
                    log_message(debug_folder, f"Review URL: {review_url}")
                else:
                    print(f"Review URL: {review_url}")
                
                # Extract place ID from the review URL
                placeid_match = re.search(r'placeid=([^&]+)', review_url)
                if placeid_match:
                    place_id = placeid_match.group(1)
                    if debug_folder:
                        log_message(debug_folder, f"Found place ID in review URL: {place_id}")
                    else:
                        print(f"Found place ID in review URL: {place_id}")
                    return place_id
        except Exception as e:
            if debug_folder:
                log_message(debug_folder, f"Error finding review button: {str(e)}")
            else:
                print(f"Error finding review button: {str(e)}")
            
        if debug_folder:
            log_message(debug_folder, "Could not extract place ID from URL")
        else:
            print("Could not extract place ID from URL")
        return None
        
    except Exception as e:
        if debug_folder:
            log_message(debug_folder, f"Error extracting place ID from URL: {str(e)}")
            log_message(debug_folder, traceback.format_exc())
        else:
            print(f"Error extracting place ID from URL: {str(e)}")
            print(traceback.format_exc())
        return None

def get_place_id_from_api(business_name, debug_folder=None):
    """
    Get the place ID from the Google Places API
    
    Args:
        business_name: The name of the business
        debug_folder: Path to debug folder for logging
        
    Returns:
        str: The place ID if found, None otherwise
    """
    if not GOOGLE_PLACES_API_KEY:
        if debug_folder:
            log_message(debug_folder, "Error: Google Places API key not set")
            log_message(debug_folder, "Please set GOOGLE_PLACES_API_KEY in .env file")
        else:
            print("Error: Google Places API key not set")
            print("Please set GOOGLE_PLACES_API_KEY in .env file")
        return None
    
    try:
        if debug_folder:
            log_message(debug_folder, f"Searching for place ID for business: {business_name}")
        else:
            print(f"Searching for place ID for business: {business_name}")
        
        # Encode the business name for the URL
        encoded_name = urllib.parse.quote(business_name)
        
        # Build the API URL
        api_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={encoded_name}&inputtype=textquery&fields=place_id,name,formatted_address&key={GOOGLE_PLACES_API_KEY}"
        
        # Make the API request
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
            'Accept-Language': 'en-US,en;q=0.9',
        }
        response = requests.get(api_url, headers=headers)
        
        # Parse the response
        data = response.json()
        
        # Save the API response to debug folder
        if debug_folder:
            with open(os.path.join(debug_folder, "places_api_response.json"), "w") as f:
                import json
                json.dump(data, f, indent=2)
        
        # Check if the API request was successful
        if data.get('status') != 'OK':
            if debug_folder:
                log_message(debug_folder, f"API error: {data.get('status')}")
                if 'error_message' in data:
                    log_message(debug_folder, f"Error message: {data.get('error_message')}")
            else:
                print(f"API error: {data.get('status')}")
                if 'error_message' in data:
                    print(f"Error message: {data.get('error_message')}")
            return None
        
        # Check if any candidates were found
        candidates = data.get('candidates', [])
        if not candidates:
            if debug_folder:
                log_message(debug_folder, f"No places found for business name: {business_name}")
            else:
                print(f"No places found for business name: {business_name}")
            return None
        
        # Get the first candidate
        candidate = candidates[0]
        place_id = candidate.get('place_id')
        
        if place_id:
            if debug_folder:
                log_message(debug_folder, f"Found place ID: {place_id}")
                log_message(debug_folder, f"Place name: {candidate.get('name')}")
                log_message(debug_folder, f"Address: {candidate.get('formatted_address')}")
            else:
                print(f"Found place ID: {place_id}")
                print(f"Place name: {candidate.get('name')}")
                print(f"Address: {candidate.get('formatted_address')}")
            return place_id
        else:
            if debug_folder:
                log_message(debug_folder, "Place ID not found in API response")
            else:
                print("Place ID not found in API response")
            return None
    
    except Exception as e:
        if debug_folder:
            log_message(debug_folder, f"Error getting place ID from API: {str(e)}")
            log_message(debug_folder, traceback.format_exc())
        else:
            print(f"Error getting place ID from API: {str(e)}")
            print(traceback.format_exc())
        return None

def get_direct_review_url(place_id, debug_folder=None):
    """
    Generate a direct review URL from a place ID
    
    Args:
        place_id: The Google Maps place ID
        debug_folder: Path to debug folder for logging
        
    Returns:
        str: The direct review URL
    """
    if debug_folder:
        log_message(debug_folder, f"Generating direct review URL for place ID: {place_id}")
    else:
        print(f"Generating direct review URL for place ID: {place_id}")
    
    # The correct format for the direct review URL is:
    # https://search.google.com/local/writereview?placeid={place_id}
    return f"https://search.google.com/local/writereview?placeid={place_id}"

def initialize_chrome_driver():
    """Initialize Chrome driver with stealth mode"""
    try:
        print("Initializing Chrome driver...")
        
        # Create chrome_profile directory if it doesn't exist
        os.makedirs("chrome_profile", exist_ok=True)
        
        # Get the absolute path to the chrome_profile directory
        chrome_profile_path = os.path.abspath("chrome_profile")
        print(f"Using Chrome profile at: {chrome_profile_path}")
        
        # Try undetected-chromedriver first
        try:
            options = uc.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument(f"--user-data-dir={chrome_profile_path}")
            
            # Add version-specific options to avoid version mismatch
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Set page load strategy to eager to speed up loading
            options.page_load_strategy = 'eager'
            
            # Try with undetected-chromedriver
            driver = uc.Chrome(options=options, version_main=133)  # Specify your Chrome version
            print("✅ Successfully initialized undetected_chromedriver")
            return driver
        except Exception as e:
            print(f"❌ Error initializing undetected_chromedriver: {str(e)}")
            print("Falling back to standard Chrome driver...")
            
            try:
                # Fallback to standard Chrome driver
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_argument(f"--user-data-dir={chrome_profile_path}")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                
                # Set page load strategy to eager to speed up loading
                chrome_options.page_load_strategy = 'eager'
                
                # Add experimental options to avoid detection
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option("useAutomationExtension", False)
                
                # Use webdriver_manager to get the correct ChromeDriver version
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Execute CDP commands to avoid detection
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    """
                })
                
                print("✅ Successfully initialized standard Chrome driver")
                return driver
            except Exception as e2:
                print(f"❌ Error initializing standard Chrome driver: {str(e2)}")
                print("Could not initialize any Chrome driver")
                return None
    except Exception as e:
        print(f"❌ Error in initialize_chrome_driver: {str(e)}")
        return None

def main():
    """Main function"""
    # Create debug folder
    debug_folder = create_debug_folder()
    log_message(debug_folder, "[1/4] Starting Direct Review URL Generator")
    
    try:
        # Read business URL from file
        business_url_file = Path("business_url.txt")
        if not business_url_file.exists():
            log_message(debug_folder, "Error: business_url.txt not found")
            return
            
        with open(business_url_file, "r") as f:
            business_url = f.read().strip()
            
        if not business_url:
            log_message(debug_folder, "Error: business_url.txt is empty")
            return
            
        log_message(debug_folder, f"[2/4] Business URL: {business_url}")
        
        # Extract business name from URL without using Chrome
        business_name = None
        
        # Try to extract business name from URL path
        # Example: https://www.google.com/maps/place/Business+Name/@coordinates
        place_match = re.search(r'/place/([^/@]+)', business_url)
        if place_match:
            business_name = place_match.group(1)
            business_name = business_name.replace('+', ' ')
            log_message(debug_folder, f"[3/4] Extracted business name: {business_name}")
            
            # Get place ID from Google Places API
            place_id = get_place_id_from_api(business_name, debug_folder)
            
            if place_id:
                # Generate direct review URL
                direct_url = get_direct_review_url(place_id, debug_folder)
                log_message(debug_folder, f"[4/4] Direct review URL: {direct_url}")
                
                # Save direct review URL to file
                with open("direct_review_url.txt", "w") as f:
                    f.write(direct_url)
                    
                log_message(debug_folder, "Direct review URL saved to direct_review_url.txt")
                return
        
        # If we couldn't extract the business name or get the place ID, try the fallback method
        log_message(debug_folder, "Couldn't extract business name or get place ID from API, trying fallback method...")
        
        # Initialize Chrome driver
        try:
            log_message(debug_folder, "[3/4] Initializing Chrome browser...")
            driver = initialize_chrome_driver()
            
            try:
                # Extract place ID directly from URL
                place_id = extract_place_id_from_url(business_url, driver, debug_folder)
                
                if not place_id:
                    log_message(debug_folder, "Failed to extract place ID from URL")
                    return
                    
                # Generate direct review URL
                direct_url = get_direct_review_url(place_id, debug_folder)
                log_message(debug_folder, f"[4/4] Direct review URL: {direct_url}")
                
                # Save direct review URL to file
                with open("direct_review_url.txt", "w") as f:
                    f.write(direct_url)
                    
                log_message(debug_folder, "Direct review URL saved to direct_review_url.txt")
                
            finally:
                # Close the driver
                if driver:
                    driver.quit()
        except Exception as e:
            log_message(debug_folder, f"Error initializing Chrome: {str(e)}")
            log_message(debug_folder, "Trying direct API call with business URL as query...")
            
            # Try to use the business URL as a query for the Places API
            # Extract any meaningful text from the URL
            url_parts = business_url.split('/')
            query = None
            for part in url_parts:
                if part and not part.startswith('http') and not part.startswith('www.') and not part == 'maps' and not part == 'place' and not part == 'google.com':
                    query = part
                    break
            
            if not query:
                query = business_url
            
            log_message(debug_folder, f"Using URL part as query: {query}")
            place_id = get_place_id_from_api(query, debug_folder)
            
            if place_id:
                # Generate direct review URL
                direct_url = get_direct_review_url(place_id, debug_folder)
                log_message(debug_folder, f"[4/4] Direct review URL: {direct_url}")
                
                # Save direct review URL to file
                with open("direct_review_url.txt", "w") as f:
                    f.write(direct_url)
                    
                log_message(debug_folder, "Direct review URL saved to direct_review_url.txt")
            else:
                log_message(debug_folder, "Failed to get place ID from API using URL part as query")
                
    except Exception as e:
        log_message(debug_folder, f"Error: {str(e)}")
        log_message(debug_folder, traceback.format_exc())
        
    log_message(debug_folder, "Process completed")

if __name__ == "__main__":
    main() 