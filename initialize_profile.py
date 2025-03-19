#!/usr/bin/env python3
"""
Initialize Chrome Profile

This script initializes a specific Chrome profile and ensures it's logged in
with the correct Google account.
"""

import os
import sys
import yaml
from chrome_profiles import initialize_profile, load_config

def main():
    """Main function to initialize a Chrome profile"""
    print("=" * 60)
    print("                INITIALIZE CHROME PROFILE                ")
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
    
    # Get profile to initialize
    try:
        index = int(input(f"Enter profile number to initialize (1-{len(profiles)}): ").strip())
        if 1 <= index <= len(profiles):
            selected_profile = profiles[index - 1]
        else:
            print("❌ Invalid profile number")
            return False
    except ValueError:
        print("❌ Invalid input")
        return False
    
    print(f"\nInitializing profile: {selected_profile['name']} for account: {selected_profile['account']}")
    
    # Initialize the profile
    success = initialize_profile(selected_profile)
    
    print()
    if success:
        print(f"✅ Successfully initialized profile: {selected_profile['name']}")
    else:
        print(f"❌ Failed to initialize profile: {selected_profile['name']}")
    
    return success

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0) 