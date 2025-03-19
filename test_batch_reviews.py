#!/usr/bin/env python3
"""
Test Batch Reviews

This script tests the batch review functionality by posting multiple reviews
using different Chrome profiles.
"""

import os
import sys
import time
from chrome_profiles import run_batch_reviews

def main():
    """Main function to test batch reviews"""
    print("=" * 60)
    print("                TEST BATCH REVIEWS                ")
    print("=" * 60)
    print()
    
    # Check if business URL or direct review URL exists
    if not (os.path.exists("business_url.txt") or os.path.exists("direct_review_url.txt")):
        print("❌ No business URL or direct review URL found")
        print("Please set a business URL or direct review URL first")
        return False
    
    # Check if accounts.yaml exists
    if not os.path.exists("accounts.yaml"):
        print("❌ No Google accounts found")
        print("Please add at least one Google account first")
        return False
    
    # Check if chrome_profiles.yaml exists
    if not os.path.exists("chrome_profiles.yaml"):
        print("❌ No Chrome profiles found")
        print("Please set up Chrome profiles first")
        return False
    
    # Get number of reviews to post
    try:
        num_reviews = int(input("Enter number of reviews to post: ").strip())
        if num_reviews <= 0:
            print("❌ Number of reviews must be positive")
            return False
    except ValueError:
        print("❌ Invalid input")
        return False
    
    # Get delay between reviews
    try:
        delay = int(input("Enter delay between reviews in seconds (0 for no delay): ").strip())
        if delay < 0:
            print("❌ Delay cannot be negative")
            return False
    except ValueError:
        print("❌ Invalid input")
        return False
    
    print("\nStarting batch review process...")
    print(f"Posting {num_reviews} reviews with {delay} seconds delay between each")
    print()
    
    # Run batch reviews
    success_count = run_batch_reviews(num_reviews, delay)
    
    print()
    print(f"✅ Successfully posted {success_count} out of {num_reviews} reviews")
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0) 