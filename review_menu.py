#!/usr/bin/env python3
"""
Menu-driven interface for Google Review Generator
"""

import os
import subprocess
import webbrowser
from datetime import datetime
import yaml
import sys
import time
import re
import requests
import urllib.parse
from dotenv import load_dotenv
from simple_review import post_review
from chrome_profiles import manage_chrome_profiles, run_batch_reviews, initialize_all_profiles, open_multiple_profile_windows, load_config

# Load environment variables from .env file
load_dotenv()

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the application header"""
    clear_screen()
    print("=" * 60)
    print("                GOOGLE REVIEWS GENERATOR                ")
    print("=" * 60)
    print()

def get_business_url():
    """Get and save the business URL"""
    print_header()
    print("\nEnter the Google Maps URL for the business:")
    print("(e.g., https://maps.app.goo.gl/xxxxx or https://www.google.com/maps/place/...)")
    
    business_url = input("\nURL: ").strip()
    
    if not business_url:
        print("❌ No URL provided.")
        input("\nPress Enter to return to the menu...")
        return
    
    # Save the URL to a file
    with open("business_url.txt", "w") as f:
        f.write(business_url)
    
    print("✅ Business URL saved successfully.")
    input("\nPress Enter to return to the menu...")

def extract_place_id_from_url(url):
    """Extract place ID from a Google Maps URL"""
    # Try to extract place ID using regex patterns
    
    # First check for standard place_id or placeid parameters
    place_id_patterns = [
        r'place_id=([^&]+)',
        r'placeid=([^&]+)'
    ]
    
    for pattern in place_id_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Check for CID pattern (0x...:0x...)
    cid_pattern = r'(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)'
    match = re.search(cid_pattern, url)
    if match:
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
            return match.group(1)
    
    # Direct extraction from URL path for specific format
    # Example: https://www.google.com/maps/place/Business/@coordinates/data=!3m1!4b1!4m5!3m4!1s0x12345:0x67890!...
    try:
        # Parse the URL
        parsed_url = urllib.parse.urlparse(url)
        
        # Check if it's a Google Maps URL
        if 'google.com/maps' in parsed_url.netloc + parsed_url.path:
            # Look for the CID in the path or query
            path_and_query = parsed_url.path + '?' + parsed_url.query
            cid_match = re.search(r'!1s(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)', path_and_query)
            if cid_match:
                return cid_match.group(1)
    except:
        pass
    
    return None

def get_place_id_from_api(business_url):
    """Get place ID from Google Places API using the business URL"""
    try:
        # Get API key from environment variable
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            print("❌ Google Places API key not found in environment variables")
            return None
        
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

def set_direct_review_url():
    """Set the direct review URL by transforming a Google business page URL"""
    print_header()
    print("SET DIRECT REVIEW URL")
    print("-" * 60)
    print("Enter the Google Maps URL of the business you want to review.")
    print("The system will automatically extract the place ID and generate a direct review URL.")
    print("Example: https://www.google.com/maps/place/Business+Name")
    print()
    
    business_url = input("Business URL: ").strip()
    
    if not business_url:
        print("❌ Business URL cannot be empty")
        input("Press Enter to continue...")
        return
    
    print("\nProcessing URL...")
    
    # Set the API key directly
    api_key = "AIzaSyDl29jzOdfmgKKuoI-j5lgrCaCgp-A6ygo"
    os.environ["GOOGLE_PLACES_API_KEY"] = api_key
    
    # First try to get place ID using the Google Places API
    print("Trying to get place ID using Google Places API...")
    place_id = get_place_id_from_api(business_url)
    
    # If API fails, fall back to direct extraction
    if not place_id:
        print("Google Places API failed to get place ID")
        print("Trying to extract place ID directly from URL...")
        place_id = extract_place_id_from_url(business_url)
        if place_id:
            print(f"✅ Extracted place ID from URL: {place_id}")
    
    # Generate direct review URL if place ID was found
    if place_id:
        direct_url = get_direct_review_url(place_id)
        
        # Save the direct review URL to a file
        with open("direct_review_url.txt", "w") as f:
            f.write(direct_url)
        
        # Also save the business URL for reference
        with open("business_url.txt", "w") as f:
            f.write(business_url)
        
        print()
        print(f"✅ Direct Review URL generated and saved: {direct_url}")
        print(f"✅ Business URL also saved for reference")
    else:
        print()
        print("❌ Failed to generate direct review URL")
        print("Please try a different URL or manually set the direct review URL")
    
    input("Press Enter to continue...")

def post_simple_review():
    """Post a simple review"""
    print_header()
    print("\nPosting a simple review with random 4-5 star rating and positive text...")
    
    try:
        # Import the post_review function from simple_review.py
        from simple_review import post_review
        
        # Call the function directly to get the return value
        success = post_review()
        
        if not success:
            print("\n❌ Review posting failed or could not be verified")
        # No need for an else statement as post_review already prints success message
    except Exception as e:
        print(f"\n❌ Error running simple_review.py: {e}")
    
    input("\nPress Enter to return to the menu...")

def post_custom_review():
    """Post a custom review"""
    print_header()
    print("\nPosting a custom review where you can specify the rating and text...")
    
    try:
        # Import the post_custom_review function from custom_review.py
        from custom_review import post_custom_review as run_custom_review
        
        # Call the function directly to get the return value
        success = run_custom_review()
        
        if not success:
            print("\n❌ Custom review posting failed or could not be verified")
        # No need for an else statement as post_custom_review already prints success message
    except Exception as e:
        print(f"\n❌ Error running custom_review.py: {e}")
    
    input("\nPress Enter to return to the menu...")

def view_debug_logs():
    """View debug logs"""
    print_header()
    print("\nDebug Logs:")
    
    # Create debug_files directory if it doesn't exist
    os.makedirs("debug_files", exist_ok=True)
    
    # Check if debug_files directory is empty
    debug_folders = [f for f in os.listdir('debug_files') if os.path.isdir(os.path.join('debug_files', f))]
    
    if not debug_folders:
        print("No debug logs found")
        input("\nPress Enter to return to the menu...")
        return
    
    # Sort folders by creation time (newest first)
    debug_folders.sort(key=lambda x: os.path.getctime(os.path.join('debug_files', x)), reverse=True)
    
    # Display folders with creation time
    for i, folder in enumerate(debug_folders, 1):
        folder_path = os.path.join('debug_files', folder)
        creation_time = datetime.fromtimestamp(os.path.getctime(folder_path))
        print(f"{i}. {folder} - Created: {creation_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ask user which folder to view
    choice = input("\nEnter folder number to view logs (or press Enter to return): ")
    
    if not choice:
        return
    
    try:
        index = int(choice) - 1
        if 0 <= index < len(debug_folders):
            selected_folder = os.path.join('debug_files', debug_folders[index])
            
            # List log files in the folder
            log_files = [f for f in os.listdir(selected_folder) if f.endswith('.txt')]
            
            if log_files:
                print(f"\nLog files in {debug_folders[index]}:")
                for i, log_file in enumerate(log_files, 1):
                    print(f"{i}. {log_file}")
                
                # Ask user which log file to view
                log_choice = input("\nEnter log file number to view (or press Enter to return): ")
                
                if log_choice:
                    try:
                        log_index = int(log_choice) - 1
                        if 0 <= log_index < len(log_files):
                            log_path = os.path.join(selected_folder, log_files[log_index])
                            
                            # Display log file content
                            print(f"\nContents of {log_files[log_index]}:\n")
                            with open(log_path, 'r') as f:
                                print(f.read())
                    except (ValueError, IndexError):
                        print("Invalid selection.")
            else:
                print("No log files found in this folder.")
        else:
            print("Invalid selection.")
    except (ValueError, IndexError):
        print("Invalid selection.")
    
    input("\nPress Enter to return to the menu...")

def edit_accounts():
    """Edit Google accounts in accounts.yaml"""
    print_header()
    
    # Check if accounts.yaml exists
    if not os.path.exists("accounts.yaml"):
        # Create a default accounts.yaml file
        default_accounts = {
            "accounts": [
                {
                    "username": "your_email@gmail.com",
                    "password": "your_password"
                }
            ]
        }
        
        with open("accounts.yaml", "w") as f:
            yaml.dump(default_accounts, f, default_flow_style=False)
        
        print("✅ Created default accounts.yaml file.")
    
    # Load current accounts
    try:
        with open("accounts.yaml", "r") as f:
            data = yaml.safe_load(f)
            accounts = data.get("accounts", [])
    except Exception as e:
        print(f"❌ Error loading accounts: {str(e)}")
        accounts = []
    
    print("\nCurrent accounts:")
    if not accounts:
        print("No accounts found.")
    else:
        for i, account in enumerate(accounts):
            username = account.get("username", "N/A")
            password = "********" if account.get("password") else "N/A"
            print(f"{i+1}. {username} (Password: {password})")
    
    print("\nOptions:")
    print("1. Add a new account")
    print("2. Edit an existing account")
    print("3. Delete an account")
    print("4. Return to main menu")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        # Add a new account
        username = input("\nEnter Google email: ").strip()
        password = input("Enter password: ").strip()
        
        if not username or not password:
            print("❌ Username and password cannot be empty.")
            input("\nPress Enter to continue...")
            return
        
        if not accounts:
            accounts = []
        
        accounts.append({
            "username": username,
            "password": password
        })
        
        # Save to file
        with open("accounts.yaml", "w") as f:
            yaml.dump({"accounts": accounts}, f, default_flow_style=False)
        
        print("✅ Account added successfully.")
        
    elif choice == "2":
        # Edit an existing account
        if not accounts:
            print("❌ No accounts to edit.")
            input("\nPress Enter to continue...")
            return
        
        account_index = input(f"\nEnter account number to edit (1-{len(accounts)}): ").strip()
        try:
            account_index = int(account_index) - 1
            if account_index < 0 or account_index >= len(accounts):
                raise ValueError()
        except ValueError:
            print("❌ Invalid account number.")
            input("\nPress Enter to continue...")
            return
        
        username = input(f"\nEnter new Google email [{accounts[account_index].get('username', '')}]: ").strip()
        password = input("Enter new password (leave empty to keep current): ").strip()
        
        if username:
            accounts[account_index]["username"] = username
        if password:
            accounts[account_index]["password"] = password
        
        # Save to file
        with open("accounts.yaml", "w") as f:
            yaml.dump({"accounts": accounts}, f, default_flow_style=False)
        
        print("✅ Account updated successfully.")
        
    elif choice == "3":
        # Delete an account
        if not accounts:
            print("❌ No accounts to delete.")
            input("\nPress Enter to continue...")
            return
        
        account_index = input(f"\nEnter account number to delete (1-{len(accounts)}): ").strip()
        try:
            account_index = int(account_index) - 1
            if account_index < 0 or account_index >= len(accounts):
                raise ValueError()
        except ValueError:
            print("❌ Invalid account number.")
            input("\nPress Enter to continue...")
            return
        
        # Confirm deletion
        confirm = input(f"Are you sure you want to delete account {accounts[account_index].get('username', '')}? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Deletion cancelled.")
            input("\nPress Enter to continue...")
            return
        
        # Remove the account
        del accounts[account_index]
        
        # Save to file
        with open("accounts.yaml", "w") as f:
            yaml.dump({"accounts": accounts}, f, default_flow_style=False)
        
        print("✅ Account deleted successfully.")
    
    input("\nPress Enter to return to the menu...")

def set_business_url():
    """Set the business URL for reviews"""
    print_header()
    print("SET BUSINESS URL")
    print("-" * 60)
    print("Enter the Google Maps URL of the business you want to review.")
    print("Example: https://www.google.com/maps/place/Business+Name")
    print()
    
    business_url = input("Business URL: ").strip()
    
    if not business_url:
        print("❌ Business URL cannot be empty")
        input("Press Enter to continue...")
        return
    
    # Save the business URL to a file
    with open("business_url.txt", "w") as f:
        f.write(business_url)
    
    print()
    print(f"✅ Business URL saved: {business_url}")
    input("Press Enter to continue...")

def initialize_profiles():
    """Initialize all Chrome profiles and ensure they're logged in"""
    print_header()
    print("INITIALIZE CHROME PROFILES")
    print("-" * 60)
    
    # Check if chrome_profiles.yaml exists
    if not os.path.exists("chrome_profiles.yaml"):
        print("❌ No Chrome profiles found")
        print("Please set up Chrome profiles first")
        input("Press Enter to continue...")
        return
    
    print("This will open each Chrome profile and ensure it's logged in with the correct Google account.")
    print("This process may take some time, especially if you have many profiles.")
    print()
    
    proceed = input("Do you want to proceed? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Operation cancelled")
        input("Press Enter to continue...")
        return
    
    print("\nInitializing Chrome profiles...")
    success_count = initialize_all_profiles()
    
    print()
    if success_count > 0:
        print(f"✅ Successfully initialized {success_count} Chrome profiles")
    else:
        print("❌ Failed to initialize any Chrome profiles")
    
    input("Press Enter to continue...")

def open_profile_windows():
    """Open multiple Chrome profile windows for manual management"""
    print_header()
    print("OPEN CHROME PROFILE WINDOWS")
    print("-" * 60)
    
    # Check if chrome_profiles.yaml exists
    if not os.path.exists("chrome_profiles.yaml"):
        print("❌ No Chrome profiles found")
        print("Please set up Chrome profiles first")
        input("Press Enter to continue...")
        return
    
    print("This will open multiple Chrome windows, each with a different profile.")
    print("You can manually manage each profile (e.g., modify Google account settings).")
    print("Changes will be saved when you close the browser windows.")
    print()
    
    # Open multiple Chrome windows
    open_multiple_profile_windows()
    
    input("Press Enter to continue...")

def open_all_profiles_for_login():
    """Open all Chrome profiles for manual login"""
    print_header()
    print("OPEN ALL PROFILES FOR MANUAL LOGIN")
    print("-" * 60)
    
    # Check if chrome_profiles.yaml exists
    if not os.path.exists("chrome_profiles.yaml"):
        print("❌ No Chrome profiles found")
        print("Please set up Chrome profiles first")
        input("Press Enter to continue...")
        return
    
    print("This will open all Chrome profiles for manual login.")
    print("For each profile, you should:")
    print("1. Log in to the Google account if not already logged in")
    print("2. Verify that you can access Google services")
    print("3. Close the browser window when finished")
    print()
    print("IMPORTANT: This will help ensure that all profiles are properly logged in")
    print("before attempting to post reviews.")
    print()
    
    proceed = input("Do you want to proceed? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Operation cancelled")
        input("Press Enter to continue...")
        return
    
    # Get the number of profiles
    config = load_config()
    profiles = config["profiles"]
    
    if not profiles:
        print("❌ No Chrome profiles found")
        input("Press Enter to continue...")
        return
    
    print(f"\nFound {len(profiles)} Chrome profiles")
    
    # Ask if user wants to open all windows at once
    open_all_at_once = input("\nDo you want to open all browser windows at once? (y/n): ").strip().lower() == 'y'
    
    if open_all_at_once:
        print("\nWARNING: Opening all browser windows at once may cause performance issues.")
        print(f"You are about to open {len(profiles)} browser windows simultaneously.")
        confirm = input("Are you sure you want to continue? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled")
            input("Press Enter to continue...")
            return
        
        print("\nOpening all profiles for manual login...")
        print()
        
        # Open all Chrome profiles at once using the all_at_once parameter
        num_windows = len(profiles)
        open_count = open_multiple_profile_windows(num_windows=num_windows, random_order=False, all_at_once=True)
        
        print()
        if open_count > 0:
            print(f"✅ Successfully opened {open_count} Chrome profiles for manual login")
            print("Make sure to log in to each Google account before closing the windows")
            print("\nWaiting for all browser windows to be closed...")
            input("Press Enter when you have finished managing all profiles...")
        else:
            print("❌ Failed to open any Chrome profiles")
    else:
        print("\nOpening profiles in batches...")
        print()
        
        # Open all Chrome profiles in batches
        num_windows = len(profiles)
        open_count = open_multiple_profile_windows(num_windows=num_windows, random_order=False, all_at_once=False)
        
        print()
        if open_count > 0:
            print(f"✅ Successfully opened {open_count} Chrome profiles for manual login")
            print("Make sure to log in to each Google account before closing the windows")
        else:
            print("❌ Failed to open any Chrome profiles")
    
    input("Press Enter to continue...")

def post_single_review():
    """Post a single review"""
    print_header()
    print("POST SINGLE REVIEW")
    print("-" * 60)
    
    # Check if business URL or direct review URL exists
    if not (os.path.exists("business_url.txt") or os.path.exists("direct_review_url.txt")):
        print("❌ No business URL or direct review URL found")
        print("Please set a business URL or direct review URL first")
        input("Press Enter to continue...")
        return
    
    # Check if accounts.yaml exists
    if not os.path.exists("accounts.yaml"):
        print("❌ No Google accounts found")
        print("Please add at least one Google account first")
        input("Press Enter to continue...")
        return
    
    # Get star rating from user
    try:
        print("Choose star rating (1-5):")
        print("1 ⭐ - Very poor")
        print("2 ⭐⭐ - Poor")
        print("3 ⭐⭐⭐ - Average")
        print("4 ⭐⭐⭐⭐ - Good")
        print("5 ⭐⭐⭐⭐⭐ - Excellent")
        rating = int(input("Enter star rating (1-5): ").strip())
        
        if rating < 1 or rating > 5:
            print("❌ Invalid rating. Must be between 1 and 5.")
            input("Press Enter to continue...")
            return
    except ValueError:
        print("❌ Invalid input. Please enter a number between 1 and 5.")
        input("Press Enter to continue...")
        return
    
    # Get custom review text or use default
    print("\nEnter custom review text or leave blank for auto-generated text:")
    custom_text = input("Review text: ").strip()
    review_text = custom_text if custom_text else None
    
    print("\nStarting review process...")
    print(f"Star Rating: {rating} ⭐")
    if review_text:
        print(f"Review Text: {review_text}")
    else:
        print("Review Text: Auto-generated based on rating")
    print()
    
    # Post the review with specified rating and text
    success = post_review(profile=None, rating=rating, review_text=review_text)
    
    print()
    if success:
        print("✅ Review posted successfully")
    else:
        print("❌ Failed to post review")
    
    input("Press Enter to continue...")

def post_batch_reviews():
    """Post multiple reviews using different Chrome profiles"""
    print_header()
    print("POST BATCH REVIEWS")
    print("-" * 60)
    
    # Check if business URL or direct review URL exists
    if not (os.path.exists("business_url.txt") or os.path.exists("direct_review_url.txt")):
        print("❌ No business URL or direct review URL found")
        print("Please set a business URL or direct review URL first")
        input("Press Enter to continue...")
        return
    
    # Check if accounts.yaml exists
    if not os.path.exists("accounts.yaml"):
        print("❌ No Google accounts found")
        print("Please add at least one Google account first")
        input("Press Enter to continue...")
        return
    
    # Check if chrome_profiles.yaml exists
    if not os.path.exists("chrome_profiles.yaml"):
        print("❌ No Chrome profiles found")
        print("Please set up Chrome profiles first")
        input("Press Enter to continue...")
        return
    
    # Get number of reviews to post
    try:
        num_reviews = int(input("Enter number of reviews to post: ").strip())
        if num_reviews <= 0:
            print("❌ Number of reviews must be positive")
            input("Press Enter to continue...")
            return
    except ValueError:
        print("❌ Invalid input")
        input("Press Enter to continue...")
        return
    
    # Get star rating strategy
    print("\nStar Rating Strategy:")
    print("1. Fixed rating (same for all reviews)")
    print("2. Random rating (random for each review)")
    print("3. Weighted random (mostly 4-5 stars)")
    
    try:
        rating_strategy = int(input("Choose rating strategy (1-3): ").strip())
        if rating_strategy < 1 or rating_strategy > 3:
            print("❌ Invalid choice. Using weighted random strategy.")
            rating_strategy = 3
    except ValueError:
        print("❌ Invalid input. Using weighted random strategy.")
        rating_strategy = 3
    
    # If fixed rating, get the rating
    fixed_rating = None
    if rating_strategy == 1:
        try:
            fixed_rating = int(input("Enter star rating (1-5): ").strip())
            if fixed_rating < 1 or fixed_rating > 5:
                print("❌ Invalid rating. Must be between 1 and 5. Using 5 stars.")
                fixed_rating = 5
        except ValueError:
            print("❌ Invalid input. Using 5 stars.")
            fixed_rating = 5
    
    # Get delay between reviews
    try:
        delay = int(input("\nEnter delay between reviews in seconds (0 for no delay): ").strip())
        if delay < 0:
            print("❌ Delay cannot be negative")
            input("Press Enter to continue...")
            return
    except ValueError:
        print("❌ Invalid input")
        input("Press Enter to continue...")
        return
    
    print("\nStarting batch review process...")
    print(f"Posting {num_reviews} reviews with {delay} seconds delay between each")
    
    if rating_strategy == 1:
        print(f"Using fixed rating: {fixed_rating} stars for all reviews")
    elif rating_strategy == 2:
        print("Using random rating (1-5 stars) for each review")
    else:
        print("Using weighted random rating (mostly 4-5 stars) for each review")
    
    print()
    
    # Run batch reviews with the selected rating strategy
    success_count = run_batch_reviews(num_reviews, delay, rating_strategy, fixed_rating)
    
    print()
    print(f"✅ Successfully posted {success_count} out of {num_reviews} reviews")
    input("Press Enter to continue...")

def manage_accounts():
    """Manage Google accounts for reviews"""
    while True:
        print_header()
        print("MANAGE GOOGLE ACCOUNTS")
        print("-" * 60)
        
        # Check if accounts.yaml exists
        if os.path.exists("accounts.yaml"):
            try:
                with open("accounts.yaml", "r") as f:
                    accounts = yaml.safe_load(f)
                    if not accounts:
                        accounts = []
            except Exception:
                accounts = []
        else:
            accounts = []
        
        # Display current accounts
        print(f"Current accounts: {len(accounts)}")
        for i, account in enumerate(accounts, 1):
            print(f"{i}. {account.get('username', 'Unknown')}")
        
        print()
        print("Options:")
        print("1. Add account")
        print("2. Remove account")
        print("3. Back to main menu")
        print()
        
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            # Add account
            print()
            username = input("Enter Google email: ").strip()
            password = input("Enter password: ").strip()
            
            if not username or not password:
                print("❌ Email and password cannot be empty")
                input("Press Enter to continue...")
                continue
            
            # Check if account already exists
            account_exists = False
            for account in accounts:
                if account.get("username") == username:
                    account_exists = True
                    break
            
            if account_exists:
                print(f"❌ Account {username} already exists")
                input("Press Enter to continue...")
                continue
            
            # Add the account
            accounts.append({
                "username": username,
                "password": password
            })
            
            # Save the accounts to the file
            with open("accounts.yaml", "w") as f:
                yaml.dump(accounts, f)
            
            print(f"✅ Account {username} added successfully")
            input("Press Enter to continue...")
        
        elif choice == "2":
            # Remove account
            if not accounts:
                print("❌ No accounts to remove")
                input("Press Enter to continue...")
                continue
            
            print()
            index = input(f"Enter account number to remove (1-{len(accounts)}): ").strip()
            
            try:
                index = int(index)
                if 1 <= index <= len(accounts):
                    removed_account = accounts.pop(index - 1)
                    
                    # Save the accounts to the file
                    with open("accounts.yaml", "w") as f:
                        yaml.dump(accounts, f)
                    
                    print(f"✅ Account {removed_account.get('username', 'Unknown')} removed successfully")
                else:
                    print("❌ Invalid account number")
            except ValueError:
                print("❌ Invalid input")
            
            input("Press Enter to continue...")
        
        elif choice == "3":
            # Back to main menu
            break
        
        else:
            print("❌ Invalid choice")
            input("Press Enter to continue...")

def get_review_url():
    """Get review URL by running direct_review_url.py script"""
    print_header()
    print("GET REVIEW URL")
    print("-" * 60)
    print("This will run the direct_review_url.py script to generate a review URL.")
    print("The script will extract the place ID and create a direct review URL.")
    print()
    
    # Check if business_url.txt exists
    if not os.path.exists("business_url.txt"):
        print("❌ No business URL found.")
        print("Please set a business URL first using option 1.")
        input("Press Enter to continue...")
        return
    
    # Read the business URL
    with open("business_url.txt", "r") as f:
        business_url = f.read().strip()
    
    print(f"Using business URL: {business_url}")
    print("\nRunning direct_review_url.py script...")
    
    try:
        # Run the direct_review_url.py script
        result = subprocess.run(["python", "direct_review_url.py"], 
                               capture_output=True, text=True)
        
        # Check if the script ran successfully
        if result.returncode == 0:
            print("\n✅ direct_review_url.py script ran successfully")
            
            # Check if direct_review_url.txt was created
            if os.path.exists("direct_review_url.txt"):
                with open("direct_review_url.txt", "r") as f:
                    direct_url = f.read().strip()
                
                print(f"\nDirect Review URL: {direct_url}")
            else:
                print("\n❌ direct_review_url.txt was not created")
                print("Check the script output for errors:")
                print(result.stdout)
        else:
            print("\n❌ direct_review_url.py script failed")
            print("Error output:")
            print(result.stderr)
    except Exception as e:
        print(f"\n❌ Error running direct_review_url.py: {str(e)}")
    
    input("\nPress Enter to continue...")

def main_menu():
    """Display the main menu"""
    while True:
        print_header()
        print("MAIN MENU")
        print("-" * 60)
        print("1. Set Business URL")
        print("2. Get Review URL")
        print("3. Manage Google Accounts")
        print("4. Manage Chrome Profiles")
        print("5. Initialize Chrome Profiles")
        print("6. Open Chrome Profile Windows")
        print("7. Open All Profiles for Manual Login")
        print("8. Post Single Review")
        print("9. Post Batch Reviews")
        print("10. Exit")
        print()
        
        choice = input("Enter your choice (1-10): ").strip()
        
        if choice == "1":
            set_business_url()
        elif choice == "2":
            get_review_url()
        elif choice == "3":
            manage_accounts()
        elif choice == "4":
            manage_chrome_profiles()
        elif choice == "5":
            initialize_profiles()
        elif choice == "6":
            open_profile_windows()
        elif choice == "7":
            open_all_profiles_for_login()
        elif choice == "8":
            post_single_review()
        elif choice == "9":
            post_batch_reviews()
        elif choice == "10":
            print("Exiting...")
            sys.exit(0)
        else:
            print("❌ Invalid choice")
            input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0) 