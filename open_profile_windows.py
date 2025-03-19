#!/usr/bin/env python3
"""
Open Chrome Profile Windows

This script opens multiple Chrome windows, each with a different profile,
for manual management of Google accounts and settings.
"""

import os
import sys
import yaml
from chrome_profiles import open_multiple_profile_windows, load_config

def main():
    """Main function to open multiple Chrome profile windows"""
    print("=" * 60)
    print("                OPEN CHROME PROFILE WINDOWS                ")
    print("=" * 60)
    print()
    
    # Check if chrome_profiles.yaml exists
    if not os.path.exists("chrome_profiles.yaml"):
        print("❌ No Chrome profiles found")
        print("Please set up Chrome profiles first")
        return False
    
    # Load profiles
    config = load_config()
    profiles = config["profiles"]
    
    if not profiles:
        print("❌ No Chrome profiles found")
        return False
    
    # Display profiles
    print(f"Found {len(profiles)} Chrome profiles:")
    for i, profile in enumerate(profiles, 1):
        print(f"{i}. {profile['name']} - Account: {profile['account']}")
    
    print()
    print("This will open multiple Chrome windows, each with a different profile.")
    print("You can manually manage each profile (e.g., modify Google account settings).")
    print("Changes will be saved when you close the browser windows.")
    print()
    
    # Get number of windows to open
    try:
        num_windows = int(input(f"Enter number of Chrome windows to open (1-{len(profiles)}): ").strip())
        if num_windows <= 0:
            print("❌ Number of windows must be positive")
            return False
        elif num_windows > len(profiles):
            print(f"Only {len(profiles)} profiles available. Opening all of them.")
            num_windows = len(profiles)
    except ValueError:
        print("❌ Invalid input")
        return False
    
    # Get random order preference
    random_order = input("Randomize the order of profiles? (y/n): ").strip().lower() == 'y'
    
    # Open the windows
    success_count = open_multiple_profile_windows(num_windows, random_order)
    
    print()
    if success_count > 0:
        print(f"✅ Successfully opened and managed {success_count} Chrome windows")
    else:
        print("❌ Failed to open any Chrome windows")
    
    return success_count > 0

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0) 