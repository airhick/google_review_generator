#!/usr/bin/env python3
"""
Script to post a custom Google review by opening the business URL directly
"""

import time
import traceback
import os
import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
from datetime import datetime
from pathlib import Path

def create_debug_folder():
    """Create a debug folder with timestamp"""
    # Create debug_files directory if it doesn't exist
    os.makedirs("debug_files", exist_ok=True)
    
    # Create a timestamped folder for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_folder = os.path.join("debug_files", f"debug_{timestamp}")
    os.makedirs(debug_folder, exist_ok=True)
    
    print(f"Debug files will be saved to: {debug_folder}")
    return debug_folder

def load_accounts():
    """Load accounts from accounts.yaml"""
    try:
        with open("accounts.yaml", "r") as f:
            data = yaml.safe_load(f)
            return data.get("accounts", [])
    except Exception as e:
        print(f"❌ Error loading accounts: {str(e)}")
        return []

def login_to_google(driver, debug_folder):
    """Log in to Google account"""
    print("\n[2/6] Logging in to Google account...")
    
    # Load accounts from accounts.yaml
    accounts = load_accounts()
    if not accounts:
        print("❌ No accounts found in accounts.yaml")
        # Save screenshot
        screenshot_path = os.path.join(debug_folder, "no_accounts.png")
        driver.save_screenshot(screenshot_path)
        return False
    
    # Use the first account
    account = accounts[0]
    username = account.get("username")
    password = account.get("password")
    
    if not username or not password:
        print("❌ Invalid account credentials")
        return False
    
    print(f"✅ Using account: {username}")
    
    try:
        # First check if already logged in
        print("Checking if already logged in...")
        driver.get("https://accounts.google.com/ServiceLogin?passive=1209600&continue=https://myaccount.google.com/")
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Save screenshot
        screenshot_path = os.path.join(debug_folder, "login_check.png")
        driver.save_screenshot(screenshot_path)
        
        # Check if we're already logged in
        if "myaccount.google.com" in driver.current_url:
            print("✅ Already logged in to Google account")
            
            # Save screenshot
            screenshot_path = os.path.join(debug_folder, "already_logged_in.png")
            driver.save_screenshot(screenshot_path)
            
            return True
        
        # Not logged in, proceed with login
        print("Not logged in, proceeding with login...")
        
        # Navigate to Google login page
        driver.get("https://accounts.google.com/signin")
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Save screenshot
        screenshot_path = os.path.join(debug_folder, "login_page.png")
        driver.save_screenshot(screenshot_path)
        
        # Enter email
        try:
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            email_input.clear()
            email_input.send_keys(username)
            
            # Click Next
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[jsname='LgbsSe']"))
            )
            next_button.click()
            
            # Save screenshot
            screenshot_path = os.path.join(debug_folder, "email_entered.png")
            driver.save_screenshot(screenshot_path)
            
            # Wait for password field
            time.sleep(3)
            
            # Enter password
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_input.clear()
            password_input.send_keys(password)
            
            # Click Next
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[jsname='LgbsSe']"))
            )
            next_button.click()
            
            # Save screenshot
            screenshot_path = os.path.join(debug_folder, "password_entered.png")
            driver.save_screenshot(screenshot_path)
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            if "myaccount.google.com" in driver.current_url or "accounts.google.com/signin/v2/challenge" in driver.current_url:
                print("✅ Successfully logged in to Google account")
                
                # Save screenshot
                screenshot_path = os.path.join(debug_folder, "login_successful.png")
                driver.save_screenshot(screenshot_path)
                
                return True
            else:
                print("❌ Login failed")
                
                # Save screenshot
                screenshot_path = os.path.join(debug_folder, "login_failed.png")
                driver.save_screenshot(screenshot_path)
                
                return False
                
        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
            
            # Save screenshot
            screenshot_path = os.path.join(debug_folder, "login_error.png")
            driver.save_screenshot(screenshot_path)
            
            return False
            
    except Exception as e:
        print(f"❌ Error navigating to login page: {str(e)}")
        
        # Save screenshot
        screenshot_path = os.path.join(debug_folder, "login_page_error.png")
        driver.save_screenshot(screenshot_path)
        
        return False

def initialize_chrome_driver():
    """Initialize Chrome driver with undetected-chromedriver or standard Chrome driver"""
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

def post_custom_review():
    """
    Post a custom review by opening the business URL directly
    """
    driver = None
    debug_folder = create_debug_folder()
    
    try:
        print("\n[1/6] Initializing Chrome browser...")
        # Initialize Chrome driver with undetected_chromedriver
        driver = initialize_chrome_driver()
        
        # Log in to Google account
        if not login_to_google(driver, debug_folder):
            print("❌ Failed to log in to Google account")
            return
        
        # Load the business URL
        print("\n[3/6] Loading business page...")
        
        # Check if business_url.txt exists
        if os.path.exists("business_url.txt"):
            with open("business_url.txt", "r") as f:
                business_url = f.read().strip()
        else:
            print("❌ business_url.txt not found. Please run the menu to set up the business URL first.")
            return
        
        # Check if direct_review_url.txt exists and use it if available
        if os.path.exists("direct_review_url.txt"):
            with open("direct_review_url.txt", "r") as f:
                direct_url = f.read().strip()
                if direct_url:
                    business_url = direct_url
                    print("✅ Using direct review URL")
        
        driver.get(business_url)
        print(f"✅ Loaded URL: {business_url}")
        
        # Wait for page to load
        time.sleep(5)
        
        # Check if we're already on a review page based on URL
        if "writereview" in driver.current_url or "review" in driver.current_url:
            print("✅ Already on a review page based on URL")
        else:
            # Look for the review button
            print("\n[4/6] Looking for review button...")
            
            try:
                # Try different selectors for the review button
                selectors = [
                    "a[href*='review'], a[data-href*='review']",
                    "button[aria-label*='review'], button[jsaction*='review']",
                    "div[aria-label*='review'], div[jsaction*='review']",
                    "span[aria-label*='review'], span[jsaction*='review']"
                ]
                
                for selector in selectors:
                    try:
                        review_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        
                        if review_button:
                            # Click the button
                            review_button.click()
                            print("✅ Clicked review button")
                            break
                    except:
                        continue
                
                # Wait for the review form to load
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Could not find review button: {str(e)}")
                return
        
        # Wait for review form to load
        print("\n[5/6] Waiting for review form to load...")
        time.sleep(5)
        
        # Get star rating from user
        star_rating = input("\nEnter star rating (1-5): ")
        try:
            star_rating = int(star_rating)
            if star_rating < 1 or star_rating > 5:
                print("❌ Invalid star rating. Please enter a number between 1 and 5.")
                return
        except ValueError:
            print("❌ Invalid star rating. Please enter a number between 1 and 5.")
            return
        
        # Get review text from user
        review_text = input("\nEnter review text: ")
        if not review_text:
            print("❌ Review text cannot be empty.")
            return
        
        # Set star rating
        try:
            # Try to find star rating elements
            star_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span[aria-label*='star']"))
            )
            
            if not star_elements:
                print("❌ Could not find star rating elements")
                return
            
            # Click the star
            star_elements[star_rating - 1].click()
            print(f"✅ Set {star_rating} star rating")
            
        except Exception as e:
            print(f"❌ Could not set star rating: {str(e)}")
            return
        
        # Enter review text
        try:
            # Try to find the review text area
            review_textarea = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[aria-label*='review'], textarea[placeholder*='review'], textarea.review-text"))
            )
            
            if not review_textarea:
                print("❌ Could not find review text area")
                return
            
            # Enter the review text
            review_textarea.clear()
            review_textarea.send_keys(review_text)
            print("✅ Entered review text")
            
        except Exception as e:
            print(f"❌ Could not enter review text: {str(e)}")
            return
        
        # Submit the review
        print("\n[6/6] Submitting review...")
        try:
            # Try different methods to find the submit button
            selectors = [
                "button[aria-label*='Post'], button[aria-label*='Submit'], button.submit-button",
                "div[role='button'][jsaction*='submit']",
                "span[role='button'][jsaction*='submit']"
            ]
            
            for selector in selectors:
                try:
                    submit_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    if submit_button:
                        # Click the button
                        submit_button.click()
                        print("✅ Clicked submit button")
                        break
                except:
                    continue
            
            # Wait to see if the review was submitted successfully
            print("Waiting to see if review was submitted successfully...")
            time.sleep(5)
            
            # Check for success message or redirect
            if "thank" in driver.page_source.lower() or "success" in driver.page_source.lower():
                print("✅ Review submitted successfully!")
            else:
                print("⚠️ Review may not have been submitted. Check manually.")
            
        except Exception as e:
            print(f"❌ Could not submit review: {str(e)}")
            return
        
        print("\n✅ Process completed! Check the debug logs for more information.")
        
        # Wait for user to press Enter before closing
        input("\nPress Enter to close the browser...")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        
        # Log the error to a file
        with open(os.path.join(debug_folder, "error_log.txt"), "w") as f:
            f.write(f"Error: {str(e)}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Include traceback if available
            import traceback
            traceback.print_exc(file=f)
        
    finally:
        # Close the driver if it was initialized
        if driver:
            driver.quit()

def get_star_rating():
    """Get custom star rating from user"""
    while True:
        try:
            rating = int(input("\nEnter star rating (1-5): "))
            if 1 <= rating <= 5:
                return rating
            else:
                print("Please enter a number between 1 and 5.")
        except ValueError:
            print("Please enter a valid number.")

def get_review_text():
    """Get custom review text from user"""
    print("\nEnter your review text (press Enter twice to finish):")
    lines = []
    while True:
        line = input()
        if not line and (not lines or not lines[-1]):
            break
        lines.append(line)
    return "\n".join(lines)

if __name__ == "__main__":
    post_custom_review() 