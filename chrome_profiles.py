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
from simple_review import post_review

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

def run_batch_reviews(num_reviews, delay=None):
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
    
    # Run reviews
    success_count = 0
    for i, profile in enumerate(selected_profiles):
        print(f"\nRunning review {i+1}/{num_reviews} with profile '{profile['name']}'...")
        
        # Post the review
        success = post_review(profile)
        
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
        print("6. Back to main menu")
        print()
        
        choice = input("Enter your choice (1-6): ").strip()
        
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
            # Back to main menu
            break
        
        else:
            print("❌ Invalid choice")
            input("Press Enter to continue...")

if __name__ == "__main__":
    manage_chrome_profiles() 