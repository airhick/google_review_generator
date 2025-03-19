#!/usr/bin/env python3
"""
Module to manage Chrome profiles for batch review creation
"""

import os
import yaml
import time
import random
from pathlib import Path
from datetime import datetime
from simple_review import post_review, initialize_chrome_driver, login_to_google, create_debug_folder

# Default configuration file
CONFIG_FILE = "chrome_profiles.yaml"

def create_default_config():
    """Create a default configuration file if it doesn't exist"""
    default_config = {
        "profiles": [],
        "batch_settings": {
            "delay_between_reviews": 30,  # seconds
            "randomize_delay": True,
            "max_random_delay": 60,  # seconds
            "randomize_order": True
        }
    }
    
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(default_config, f)
    
    return default_config

def load_config():
    """Load the configuration from the YAML file"""
    if not os.path.exists(CONFIG_FILE):
        return create_default_config()
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = yaml.safe_load(f)
            
            # Ensure the config has the required structure
            if not config:
                return create_default_config()
            
            if "profiles" not in config:
                config["profiles"] = []
            
            if "batch_settings" not in config:
                config["batch_settings"] = {
                    "delay_between_reviews": 30,
                    "randomize_delay": True,
                    "max_random_delay": 60,
                    "randomize_order": True
                }
            
            return config
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        return create_default_config()

def save_config(config):
    """Save the configuration to the YAML file"""
    try:
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(config, f)
        return True
    except Exception as e:
        print(f"Error saving configuration: {str(e)}")
        return False

def add_profile(name, path, account):
    """Add a new Chrome profile to the configuration"""
    config = load_config()
    
    # Check if profile with the same name already exists
    for profile in config["profiles"]:
        if profile["name"] == name:
            print(f"Profile '{name}' already exists")
            return False
    
    # Ensure the profile directory exists
    try:
        os.makedirs(path, exist_ok=True)
        print(f"Created profile directory: {path}")
    except Exception as e:
        print(f"Error creating profile directory: {str(e)}")
        # Continue anyway, as the directory might be created later
    
    # Add the new profile
    config["profiles"].append({
        "name": name,
        "path": path,
        "account": account,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # Save the updated configuration
    return save_config(config)

def remove_profile(name):
    """Remove a Chrome profile from the configuration"""
    config = load_config()
    
    # Find the profile to remove
    for i, profile in enumerate(config["profiles"]):
        if profile["name"] == name:
            # Remove the profile
            config["profiles"].pop(i)
            
            # Save the updated configuration
            return save_config(config)
    
    print(f"Profile '{name}' not found")
    return False

def import_accounts_to_profiles():
    """Import accounts from accounts.yaml and create profiles for each"""
    if not os.path.exists("accounts.yaml"):
        print("accounts.yaml file not found")
        return False
    
    try:
        with open("accounts.yaml", "r") as f:
            accounts = yaml.safe_load(f)
            if not accounts:
                print("No accounts found in accounts.yaml")
                return False
            
            # Create the chrome_profiles directory if it doesn't exist
            chrome_profiles_dir = os.path.join(os.getcwd(), "chrome_profiles")
            try:
                os.makedirs(chrome_profiles_dir, exist_ok=True)
                print(f"Created chrome_profiles directory: {chrome_profiles_dir}")
            except Exception as e:
                print(f"Error creating chrome_profiles directory: {str(e)}")
                # Continue anyway, as individual profile directories might still be created
            
            # Create a profile for each account
            success_count = 0
            for i, account in enumerate(accounts):
                username = account.get("username")
                if not username:
                    continue
                
                # Create a profile name based on the username
                profile_name = f"profile_{username.split('@')[0]}"
                profile_path = os.path.join(os.getcwd(), f"chrome_profiles/{profile_name}")
                
                # Add the profile
                if add_profile(profile_name, profile_path, username):
                    success_count += 1
            
            print(f"Successfully imported {success_count} profiles from accounts.yaml")
            return success_count > 0
    except Exception as e:
        print(f"Error importing accounts: {str(e)}")
        return False

def update_batch_settings(settings):
    """Update the batch settings in the configuration"""
    config = load_config()
    
    # Update the batch settings
    config["batch_settings"].update(settings)
    
    # Save the updated configuration
    return save_config(config)

def run_batch_reviews(num_reviews, delay=None, rating_strategy=3, fixed_rating=None):
    """Run batch reviews using multiple Chrome profiles"""
    config = load_config()
    profiles = config["profiles"]
    
    if not profiles:
        print("No Chrome profiles found")
        return 0
    
    # Use the provided delay or the one from the configuration
    if delay is None:
        delay = config["batch_settings"]["delay_between_reviews"]
    
    # Get batch settings
    randomize_delay = config["batch_settings"]["randomize_delay"]
    max_random_delay = config["batch_settings"]["max_random_delay"]
    randomize_order = config["batch_settings"]["randomize_order"]
    
    # Determine which profiles to use
    if num_reviews <= len(profiles):
        # Use a subset of profiles
        selected_profiles = profiles[:num_reviews]
    else:
        # Use all profiles and repeat some if needed
        selected_profiles = profiles * (num_reviews // len(profiles) + 1)
        selected_profiles = selected_profiles[:num_reviews]
    
    # Randomize the order if specified
    if randomize_order:
        random.shuffle(selected_profiles)
    
    # Check if profiles need to be initialized first
    print("Checking if profiles need to be initialized...")
    profiles_to_initialize = []
    for profile in selected_profiles:
        profile_path = profile["path"]
        if not os.path.exists(profile_path) or not os.listdir(profile_path):
            print(f"Profile {profile['name']} needs to be initialized")
            profiles_to_initialize.append(profile)
    
    if profiles_to_initialize:
        print(f"\nFound {len(profiles_to_initialize)} profiles that need to be initialized")
        initialize = input("Do you want to initialize these profiles now? (y/n): ").strip().lower()
        
        if initialize == 'y':
            for profile in profiles_to_initialize:
                print(f"\nInitializing profile: {profile['name']}")
                initialize_profile(profile)
        else:
            print("Continuing without initializing profiles. Some reviews may fail.")
    
    # Run reviews
    success_count = 0
    for i, profile in enumerate(selected_profiles):
        print(f"\nRunning review {i+1}/{num_reviews} with profile '{profile['name']}'...")
        
        # Determine the star rating for this review
        if rating_strategy == 1:
            # Fixed rating
            rating = fixed_rating
        elif rating_strategy == 2:
            # Random rating (1-5 stars)
            rating = random.randint(1, 5)
        else:
            # Weighted random (mostly 4-5 stars)
            weights = [5, 10, 15, 35, 35]  # Weights for 1-5 stars
            rating = random.choices([1, 2, 3, 4, 5], weights=weights)[0]
        
        print(f"Using {rating} star rating for this review")
        
        # Post the review with the determined rating
        success = post_review(profile, rating=rating)
        
        if success:
            success_count += 1
            print(f"✅ Review {i+1}/{num_reviews} posted successfully")
        else:
            print(f"❌ Failed to post review {i+1}/{num_reviews}")
        
        # Delay before the next review (except for the last one)
        if i < len(selected_profiles) - 1:
            actual_delay = delay
            if randomize_delay and max_random_delay > 0:
                actual_delay += random.randint(0, max_random_delay)
            
            print(f"Waiting {actual_delay} seconds before the next review...")
            time.sleep(actual_delay)
    
    return success_count

def list_profiles():
    """List all Chrome profiles"""
    config = load_config()
    profiles = config["profiles"]
    
    if not profiles:
        print("No Chrome profiles found")
        return
    
    print(f"Found {len(profiles)} Chrome profiles:")
    for i, profile in enumerate(profiles, 1):
        print(f"{i}. {profile['name']} - Account: {profile['account']}")
        print(f"   Path: {profile['path']}")
        print(f"   Created: {profile.get('created_at', 'Unknown')}")
        print()

def manage_chrome_profiles():
    """Menu for managing Chrome profiles"""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 60)
        print("                MANAGE CHROME PROFILES                ")
        print("=" * 60)
        print()
        
        config = load_config()
        profiles = config["profiles"]
        batch_settings = config["batch_settings"]
        
        print(f"Current profiles: {len(profiles)}")
        for i, profile in enumerate(profiles, 1):
            print(f"{i}. {profile['name']} - Account: {profile['account']}")
        
        print("\nBatch settings:")
        print(f"- Delay between reviews: {batch_settings['delay_between_reviews']} seconds")
        print(f"- Randomize delay: {'Yes' if batch_settings['randomize_delay'] else 'No'}")
        print(f"- Max random delay: {batch_settings['max_random_delay']} seconds")
        print(f"- Randomize order: {'Yes' if batch_settings['randomize_order'] else 'No'}")
        
        print("\nOptions:")
        print("1. List profiles")
        print("2. Add profile")
        print("3. Remove profile")
        print("4. Import accounts from accounts.yaml")
        print("5. Update batch settings")
        print("6. Initialize all profiles")
        print("7. Open profile windows")
        print("8. Back to main menu")
        print()
        
        choice = input("Enter your choice (1-8): ").strip()
        
        if choice == "1":
            # List profiles
            print()
            list_profiles()
            input("Press Enter to continue...")
        
        elif choice == "2":
            # Add profile
            print()
            name = input("Enter profile name: ").strip()
            path = input("Enter profile path (or leave empty for default): ").strip()
            account = input("Enter Google account email: ").strip()
            
            if not name or not account:
                print("❌ Profile name and account email cannot be empty")
                input("Press Enter to continue...")
                continue
            
            if not path:
                path = os.path.join(os.getcwd(), f"chrome_profiles/{name}")
            
            if add_profile(name, path, account):
                print(f"✅ Profile '{name}' added successfully")
            else:
                print(f"❌ Failed to add profile '{name}'")
            
            input("Press Enter to continue...")
        
        elif choice == "3":
            # Remove profile
            if not profiles:
                print("❌ No profiles to remove")
                input("Press Enter to continue...")
                continue
            
            print()
            index = input(f"Enter profile number to remove (1-{len(profiles)}): ").strip()
            
            try:
                index = int(index)
                if 1 <= index <= len(profiles):
                    profile = profiles[index - 1]
                    if remove_profile(profile["name"]):
                        print(f"✅ Profile '{profile['name']}' removed successfully")
                    else:
                        print(f"❌ Failed to remove profile '{profile['name']}'")
                else:
                    print("❌ Invalid profile number")
            except ValueError:
                print("❌ Invalid input")
            
            input("Press Enter to continue...")
        
        elif choice == "4":
            # Import accounts from accounts.yaml
            print()
            if import_accounts_to_profiles():
                print("✅ Accounts imported successfully")
            else:
                print("❌ Failed to import accounts")
            
            input("Press Enter to continue...")
        
        elif choice == "5":
            # Update batch settings
            print()
            try:
                delay = int(input("Enter delay between reviews in seconds: ").strip())
                randomize_delay = input("Randomize delay? (y/n): ").strip().lower() == "y"
                max_random_delay = int(input("Enter max random delay in seconds: ").strip())
                randomize_order = input("Randomize order? (y/n): ").strip().lower() == "y"
                
                settings = {
                    "delay_between_reviews": delay,
                    "randomize_delay": randomize_delay,
                    "max_random_delay": max_random_delay,
                    "randomize_order": randomize_order
                }
                
                if update_batch_settings(settings):
                    print("✅ Batch settings updated successfully")
                else:
                    print("❌ Failed to update batch settings")
            except ValueError:
                print("❌ Invalid input")
            
            input("Press Enter to continue...")
        
        elif choice == "6":
            # Initialize all profiles
            print()
            if initialize_all_profiles():
                print("✅ All profiles initialized successfully")
            else:
                print("❌ Failed to initialize all profiles")
            
            input("Press Enter to continue...")
        
        elif choice == "7":
            # Open profile windows
            print()
            if open_multiple_profile_windows():
                print("✅ Successfully opened and managed Chrome profile windows")
            else:
                print("❌ Failed to open Chrome profile windows")
            
            input("Press Enter to continue...")
        
        elif choice == "8":
            # Back to main menu
            break
        
        else:
            print("❌ Invalid choice")
            input("Press Enter to continue...")

def initialize_profile(profile):
    """Initialize a Chrome profile and ensure it's logged in with the correct account"""
    print(f"\nInitializing profile: {profile['name']} for account: {profile['account']}")
    
    # Create debug folder
    debug_folder = create_debug_folder()
    print(f"Debug files will be saved to: {debug_folder}")
    
    try:
        # Initialize Chrome browser with the profile
        print("Initializing Chrome browser...")
        driver = initialize_chrome_driver(profile["path"])
        if not driver:
            print(f"❌ Failed to initialize Chrome browser for profile: {profile['name']}")
            return False
        
        print(f"✅ Chrome browser initialized successfully for profile: {profile['name']}")
        
        # Log in to Google account
        print(f"Logging in to Google account: {profile['account']}...")
        login_success = login_to_google(driver, debug_folder, profile['account'])
        
        if not login_success:
            print(f"❌ Failed to log in to Google account for profile: {profile['name']}")
            driver.quit()
            return False
        
        print(f"✅ Successfully logged in to Google account for profile: {profile['name']}")
        
        # Visit Google homepage to ensure cookies are saved
        driver.get("https://www.google.com")
        print("Visited Google homepage to save cookies")
        
        # Take a screenshot
        screenshot_path = os.path.join(debug_folder, f"profile_{profile['name']}_logged_in.png")
        driver.save_screenshot(screenshot_path)
        
        # Close the browser
        driver.quit()
        
        return True
    except Exception as e:
        print(f"❌ Error initializing profile {profile['name']}: {str(e)}")
        return False

def initialize_all_profiles():
    """Initialize all Chrome profiles and ensure they're logged in"""
    config = load_config()
    profiles = config["profiles"]
    
    if not profiles:
        print("No Chrome profiles found")
        return 0
    
    print(f"Found {len(profiles)} Chrome profiles to initialize")
    
    success_count = 0
    for i, profile in enumerate(profiles, 1):
        print(f"\n[{i}/{len(profiles)}] Initializing profile: {profile['name']}")
        
        if initialize_profile(profile):
            success_count += 1
            print(f"✅ Successfully initialized profile: {profile['name']}")
        else:
            print(f"❌ Failed to initialize profile: {profile['name']}")
        
        # Wait a bit between profiles
        if i < len(profiles):
            delay = 5
            print(f"Waiting {delay} seconds before initializing the next profile...")
            time.sleep(delay)
    
    print(f"\n✅ Successfully initialized {success_count} out of {len(profiles)} profiles")
    return success_count

def open_profile_window(profile):
    """Open a Chrome window with the specified profile for manual management"""
    from simple_review import initialize_chrome_driver
    
    print(f"\nOpening Chrome window for profile: {profile['name']} ({profile['account']})")
    
    try:
        # Initialize Chrome browser with the profile
        driver = initialize_chrome_driver(profile["path"])
        if not driver:
            print(f"❌ Failed to open Chrome window for profile: {profile['name']}")
            return False
        
        print(f"✅ Chrome window opened for profile: {profile['name']}")
        
        # Navigate to Google account login page
        driver.get("https://accounts.google.com/")
        print(f"Navigated to Google Account login page for profile: {profile['name']}")
        
        # Display instructions
        print(f"\n--- MANUAL LOGIN INSTRUCTIONS FOR {profile['name']} ---")
        print(f"1. Check if you're already logged in as {profile['account']}")
        print("2. If not logged in, enter the credentials:")
        print(f"   Username: {profile['account']}")
        print("   Password: [Use the password from accounts.yaml]")
        print("3. Complete any verification steps if required")
        print("4. Verify you can access Google services")
        print("5. Close the browser window when finished")
        print("----------------------------------------------")
        
        # Keep the window open until user closes it
        try:
            # This will throw an exception when the window is closed
            while True:
                # Check if window is still open every 5 seconds
                time.sleep(5)
                driver.current_url  # This will throw an exception if the window is closed
        except:
            print(f"Chrome window for profile {profile['name']} was closed.")
            return True
    except Exception as e:
        print(f"❌ Error opening Chrome window for profile {profile['name']}: {str(e)}")
        return False

def open_multiple_profile_windows(num_windows=None, random_order=None, all_at_once=False):
    """Open multiple Chrome profile windows for manual management"""
    config = load_config()
    profiles = config["profiles"]
    
    if not profiles:
        print("No Chrome profiles found")
        return 0
    
    # Ask for number of windows if not provided
    if num_windows is None:
        try:
            num_windows = int(input(f"Enter number of Chrome windows to open (1-{len(profiles)}): ").strip())
            if num_windows <= 0:
                print("❌ Number of windows must be positive")
                return 0
        except ValueError:
            print("❌ Invalid input")
            return 0
    
    # Limit the number of windows to the number of profiles
    if num_windows > len(profiles):
        print(f"Only {len(profiles)} profiles available. Opening all of them.")
        num_windows = len(profiles)
    
    # Ask for random order if not provided
    if random_order is None:
        random_order = input("Randomize the order of profiles? (y/n): ").strip().lower() == 'y'
    
    # Determine which profiles to open
    selected_profiles = profiles[:num_windows]
    
    # Randomize the order if specified
    if random_order:
        random.shuffle(selected_profiles)
    
    print(f"\nPreparing to open {len(selected_profiles)} Chrome windows...")
    print("IMPORTANT: For each profile, make sure to:")
    print("1. Log in to the Google account if not already logged in")
    print("2. Verify that you can access Google services")
    print("3. Close the browser window when finished")
    print()
    
    # Create the chrome_profiles directory if it doesn't exist
    for profile in selected_profiles:
        profile_path = profile["path"]
        try:
            os.makedirs(profile_path, exist_ok=True)
        except Exception as e:
            print(f"Error creating profile directory {profile_path}: {str(e)}")
    
    # If all_at_once is True, open all windows at once
    if all_at_once:
        print("\nOpening all windows at once...")
        
        open_count = 0
        for i, profile in enumerate(selected_profiles, 1):
            print(f"\n[{i}/{len(selected_profiles)}] Opening Chrome window for profile: {profile['name']}")
            
            if open_profile_window(profile):
                open_count += 1
        
        return open_count
    
    # Otherwise, ask how many windows to open at once
    max_concurrent = 3
    try:
        max_concurrent = int(input(f"How many windows to open at once? (1-{min(5, len(selected_profiles))}): ").strip())
        if max_concurrent <= 0:
            max_concurrent = 1
        elif max_concurrent > 5:
            print("Opening more than 5 windows at once may cause performance issues.")
            print("Limiting to 5 windows at once.")
            max_concurrent = 5
    except ValueError:
        max_concurrent = 3
    
    # Open Chrome windows in batches
    open_count = 0
    for i in range(0, len(selected_profiles), max_concurrent):
        batch = selected_profiles[i:i+max_concurrent]
        
        print(f"\nOpening batch {i//max_concurrent + 1} ({len(batch)} profiles)...")
        
        # Open windows in this batch
        batch_open_count = 0
        for j, profile in enumerate(batch, 1):
            print(f"\n[{i+j}/{len(selected_profiles)}] Opening Chrome window for profile: {profile['name']}")
            
            if open_profile_window(profile):
                batch_open_count += 1
                open_count += 1
        
        # Wait for all windows in this batch to be closed
        if i + max_concurrent < len(selected_profiles):
            print("\nPlease close all browser windows in this batch before continuing...")
            input("Press Enter when all browser windows in this batch are closed...")
    
    print(f"\n✅ Successfully opened and managed {open_count} out of {len(selected_profiles)} Chrome windows")
    return open_count

if __name__ == "__main__":
    manage_chrome_profiles() 