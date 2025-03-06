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
from simple_review import post_review
from chrome_profiles import manage_chrome_profiles, run_batch_reviews

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

def generate_direct_url():
    """Generate a direct review URL from the business URL"""
    print_header()
    
    # Check if business_url.txt exists
    if not os.path.exists("business_url.txt"):
        print("❌ Business URL not found. Please set the business URL first.")
        input("\nPress Enter to return to the menu...")
        return
    
    # Read the business URL
    with open("business_url.txt", "r") as f:
        business_url = f.read().strip()
    
    print(f"\nGenerating direct review URL for: {business_url}")
    print("\nUsing Google Places API to extract business information and get place ID...")
    
    try:
        # Run the direct_review_url.py script
        result = subprocess.run(["python", "direct_review_url.py"], 
                               capture_output=True, text=True, check=True)
        
        # Check if direct_review_url.txt was created
        if os.path.exists("direct_review_url.txt"):
            with open("direct_review_url.txt", "r") as f:
                direct_url = f.read().strip()
            
            print("\n✅ Direct review URL generated successfully!")
            print(f"\nDirect URL: {direct_url}")
            
            # Ask if user wants to open the URL
            open_url = input("\nOpen this URL in your browser? (y/n): ").lower()
            if open_url == 'y':
                webbrowser.open(direct_url)
        else:
            print("❌ Failed to generate direct review URL.")
            print(result.stderr)
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running direct_review_url.py: {e}")
        print(e.stderr)
    
    input("\nPress Enter to return to the menu...")

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

def set_direct_review_url():
    """Set the direct review URL"""
    print_header()
    print("SET DIRECT REVIEW URL")
    print("-" * 60)
    print("Enter the direct Google review URL for the business.")
    print("Example: https://search.google.com/local/writereview?placeid=ChIJ...")
    print()
    
    direct_url = input("Direct Review URL: ").strip()
    
    if not direct_url:
        print("❌ Direct Review URL cannot be empty")
        input("Press Enter to continue...")
        return
    
    # Save the direct review URL to a file
    with open("direct_review_url.txt", "w") as f:
        f.write(direct_url)
    
    print()
    print(f"✅ Direct Review URL saved: {direct_url}")
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
    
    print("Starting review process...")
    print()
    
    # Post the review
    success = post_review()
    
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
    
    # Get delay between reviews
    try:
        delay = int(input("Enter delay between reviews in seconds (0 for no delay): ").strip())
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
    print()
    
    # Run batch reviews
    success_count = run_batch_reviews(num_reviews, delay)
    
    print()
    print(f"✅ Successfully posted {success_count} out of {num_reviews} reviews")
    input("Press Enter to continue...")

def main_menu():
    """Display the main menu"""
    while True:
        print_header()
        print("MAIN MENU")
        print("-" * 60)
        print("1. Set Business URL")
        print("2. Set Direct Review URL")
        print("3. Manage Google Accounts")
        print("4. Manage Chrome Profiles")
        print("5. Post Single Review")
        print("6. Post Batch Reviews")
        print("7. Exit")
        print()
        
        choice = input("Enter your choice (1-7): ").strip()
        
        if choice == "1":
            set_business_url()
        elif choice == "2":
            set_direct_review_url()
        elif choice == "3":
            manage_accounts()
        elif choice == "4":
            manage_chrome_profiles()
        elif choice == "5":
            post_single_review()
        elif choice == "6":
            post_batch_reviews()
        elif choice == "7":
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