#!/usr/bin/env python3
"""
Simple script to post a Google review by opening the business URL directly
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
import random
from pathlib import Path
import subprocess
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException

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
        if not os.path.exists("accounts.yaml"):
            print("❌ accounts.yaml file not found")
            return []
        
        with open("accounts.yaml", "r") as f:
            accounts_data = yaml.safe_load(f)
        
        # Handle different possible formats of accounts.yaml
        if isinstance(accounts_data, list):
            # Direct list of accounts
            return accounts_data
        elif isinstance(accounts_data, dict) and "accounts" in accounts_data:
            # Dictionary with "accounts" key
            return accounts_data["accounts"]
        else:
            print("❌ Invalid format in accounts.yaml")
            return []
    except Exception as e:
        print(f"❌ Error loading accounts: {str(e)}")
        return []

def login_to_google(driver, debug_folder, account_email=None):
    """Log in to Google account"""
    try:
        # Load accounts from accounts.yaml
        accounts = load_accounts()
        if not accounts:
            print("❌ No accounts found in accounts.yaml")
            return False
        
        # Use the specified account or the first one
        account = None
        if account_email:
            for acc in accounts:
                if acc["username"] == account_email:
                    account = acc
                    break
            if not account:
                print(f"❌ Account {account_email} not found in accounts.yaml")
                return False
        else:
            account = accounts[0]
        
        print(f"✅ Using account: {account['username']}")
        
        # Check if already logged in
        print("Checking if already logged in...")
        driver.get("https://accounts.google.com/")
        
        # Save screenshot
        screenshot_path = os.path.join(debug_folder, "login_check.png")
        driver.save_screenshot(screenshot_path)
        
        # Check if we're already logged in
        try:
            # Wait for the page to load
            time.sleep(2)
            
            # Check if we're on the account page (already logged in)
            if "myaccount.google.com" in driver.current_url or "accounts.google.com/signin/v2/identifier" not in driver.current_url:
                print("✅ Already logged in to Google account")
                
                # Save screenshot
                screenshot_path = os.path.join(debug_folder, "already_logged_in.png")
                driver.save_screenshot(screenshot_path)
                
                return True
            
            # If not logged in, proceed with login
            print("Not logged in. Proceeding with login...")
            
            # Enter email
            email_input = driver.find_element(By.ID, "identifierId")
            email_input.clear()
            email_input.send_keys(account["username"])
            
            # Click next
            next_button = driver.find_element(By.ID, "identifierNext")
            next_button.click()
            
            # Wait for password field
            time.sleep(2)
            
            # Enter password
            password_input = driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(account["password"])
            
            # Click next
            next_button = driver.find_element(By.ID, "passwordNext")
            next_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Save screenshot
            screenshot_path = os.path.join(debug_folder, "after_login.png")
            driver.save_screenshot(screenshot_path)
            
            print("✅ Successfully logged in to Google account")
            return True
        except Exception as e:
            print(f"❌ Error during login check: {str(e)}")
            
            # Try a more direct login approach
            try:
                print("Trying direct login approach...")
                
                # Go to the login page
                driver.get("https://accounts.google.com/signin")
                time.sleep(2)
                
                # Enter email
                email_input = driver.find_element(By.ID, "identifierId")
                email_input.clear()
                email_input.send_keys(account["username"])
                
                # Click next
                next_button = driver.find_element(By.ID, "identifierNext")
                next_button.click()
                
                # Wait for password field
                time.sleep(2)
                
                # Enter password
                password_input = driver.find_element(By.NAME, "password")
                password_input.clear()
                password_input.send_keys(account["password"])
                
                # Click next
                next_button = driver.find_element(By.ID, "passwordNext")
                next_button.click()
                
                # Wait for login to complete
                time.sleep(5)
                
                # Save screenshot
                screenshot_path = os.path.join(debug_folder, "after_direct_login.png")
                driver.save_screenshot(screenshot_path)
                
                print("✅ Successfully logged in using direct approach")
                return True
            except Exception as e2:
                print(f"❌ Error during direct login: {str(e2)}")
                return False
    except Exception as e:
        print(f"❌ Error in login_to_google: {str(e)}")
        return False

def post_review(profile=None, rating=None, review_text=None):
    """Post a review for a business"""
    # Create debug folder
    debug_folder = create_debug_folder()
    print(f"Debug files will be saved to: {debug_folder}")
    print()
    
    try:
        # Step 1: Initialize Chrome browser
        print("[1/6] Initializing Chrome browser...")
        
        # Use the profile path if provided
        chrome_profile_path = None
        if profile and "path" in profile:
            chrome_profile_path = profile["path"]
        
        driver = initialize_chrome_driver(chrome_profile_path)
        if not driver:
            print("❌ Failed to initialize Chrome browser")
            return False
        print("✅ Chrome browser initialized successfully")
        print()
        
        # Step 2: Log in to Google account
        print("[2/6] Logging in to Google account...")
        
        # Use the account from the profile if provided
        if profile and "account" in profile:
            account_email = profile["account"]
            login_success = login_to_google(driver, debug_folder, account_email)
        else:
            login_success = login_to_google(driver, debug_folder)
            
        if not login_success:
            print("❌ Failed to log in to Google account")
            driver.quit()
            return False
        print()
        
        # Step 3: Prepare review URL
        print("[3/6] Preparing review URL...")
        
        # Check if direct review URL exists
        direct_url_file = "direct_review_url.txt"
        if os.path.exists(direct_url_file):
            with open(direct_url_file, "r") as f:
                direct_url = f.read().strip()
                if direct_url:
                    print("✅ Using existing direct review URL")
                    driver.get(direct_url)
                    print(f"✅ Loaded URL: {direct_url}")
                else:
                    print("❌ Direct review URL file exists but is empty")
                    driver.quit()
                    return False
        else:
            # Check if business URL exists
            business_url_file = "business_url.txt"
            if os.path.exists(business_url_file):
                with open(business_url_file, "r") as f:
                    business_url = f.read().strip()
                    if business_url:
                        print(f"✅ Using business URL: {business_url}")
                        driver.get(business_url)
                        print(f"✅ Loaded URL: {business_url}")
                        
                        # Find and click the review button
                        print("[4/6] Finding and clicking review button...")
                        review_button_clicked = find_and_click_review_button(driver, debug_folder)
                        if not review_button_clicked:
                            print("❌ Failed to find and click review button")
                            driver.quit()
                            return False
                    else:
                        print("❌ Business URL file exists but is empty")
                        driver.quit()
                        return False
            else:
                print("❌ No business URL or direct review URL found")
                print("Please set a business URL first using the menu option")
                driver.quit()
                return False
        print()
        
        # Step 5: Wait for review form to load
        print("[5/6] Waiting for review form to load...")
        try:
            # Wait for the review form to load
            time.sleep(3)
            
            # Save screenshot of review form
            screenshot_path = os.path.join(debug_folder, "review_form.png")
            driver.save_screenshot(screenshot_path)
            
            # Set star rating
            print("Setting star rating...")
            star_rating_set = set_star_rating(driver, debug_folder, rating)
            if not star_rating_set:
                print("❌ Failed to set star rating")
                driver.quit()
                return False
            
            # Enter review text
            review_text_entered = enter_review_text(driver, debug_folder, review_text)
            if not review_text_entered:
                print("❌ Failed to enter review text")
                driver.quit()
                return False
        except Exception as e:
            print(f"❌ Error interacting with review form: {str(e)}")
            driver.quit()
            return False
        print()
        
        # Step 6: Submit review
        print("[6/6] Submitting review...")
        submit_success = submit_review(driver, debug_folder)
        
        # Take final screenshot
        screenshot_path = os.path.join(debug_folder, "after_submit.png")
        driver.save_screenshot(screenshot_path)
        
        # Close the browser
        driver.quit()
        
        if submit_success:
            print("\n✅ Review process completed successfully!")
            return True
        else:
            print("\n❌ Review submission failed or could not be verified")
            return False
    except Exception as e:
        print(f"\n❌ Error posting review: {str(e)}")
        return False

def set_star_rating(driver, debug_folder, rating=None):
    """Set star rating for the review"""
    try:
        # If rating is not provided, use a random 4 or 5 star rating
        if rating is None:
            rating = random.randint(4, 5)
        
        print(f"Setting star rating to {rating} stars...")
        
        # Take a screenshot before finding star rating
        screenshot_path = os.path.join(debug_folder, "before_star_rating.png")
        driver.save_screenshot(screenshot_path)
        
        # First, check if we need to switch to an iframe
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Found {len(iframes)} iframes on the page")
        
        # Store the main window handle
        main_window = driver.current_window_handle
        
        # Try to find the review iframe
        review_iframe = None
        for iframe in iframes:
            try:
                iframe_src = iframe.get_attribute("src") or ""
                if "ReviewsService" in iframe_src or "writereview" in iframe_src or "review" in iframe_src:
                    print(f"✅ Found review iframe for star rating: {iframe_src}")
                    review_iframe = iframe
                    break
            except:
                continue
        
        # Switch to the review iframe if found
        if review_iframe:
            driver.switch_to.frame(review_iframe)
            print("Switched to review iframe")
            
            # Take a screenshot after switching to iframe
            screenshot_path = os.path.join(debug_folder, "inside_review_iframe.png")
            driver.save_screenshot(screenshot_path)
        
        # Try multiple selectors to find star rating elements
        star_selectors = [
            "span[aria-label*='star']",
            "div[aria-label*='star']",
            "div[role='radio'][aria-label*='star']",
            "span[role='radio'][aria-label*='star']",
            "g-radio-button[aria-label*='star']",
            "div.rating-star",
            "div.star-rating",
            "div.stars span",
            "div[jsaction*='star']",
            "div[jsaction*='rating']"
        ]
        
        star_elements = None
        used_selector = None
        
        for selector in star_selectors:
            print(f"Trying to find star rating elements with selector: {selector}")
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements and len(elements) >= 5:
                star_elements = elements
                used_selector = selector
                print(f"✅ Found star rating elements using selector: {selector}")
                break
        
        # If we couldn't find star elements with CSS selectors, try JavaScript
        if not star_elements:
            print("Trying JavaScript approach to find star elements...")
            try:
                # Try to find the rating container first
                rating_container = driver.find_element(By.CSS_SELECTOR, "div[role='radiogroup'], div.rating-container, div.star-rating-container")
                print("Found rating container, trying to click it first...")
                try:
                    rating_container.click()
                except:
                    pass
                
                # Try to find any clickable elements in the top section
                print("Trying to find any clickable elements in the top section...")
                star_elements = driver.execute_script("""
                    // Find all elements that look like they could be star ratings
                    var possibleStars = [];
                    
                    // Look for elements with star-related attributes or classes
                    document.querySelectorAll('*').forEach(function(el) {
                        var text = (el.textContent || '').toLowerCase();
                        var classes = (el.className || '').toLowerCase();
                        var ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
                        var role = (el.getAttribute('role') || '').toLowerCase();
                        
                        if (
                            (ariaLabel.includes('star') || classes.includes('star') || role === 'radio') &&
                            el.offsetWidth > 0 && el.offsetHeight > 0 && // Visible elements only
                            (el.onclick || el.parentElement.onclick) // Clickable elements
                        ) {
                            possibleStars.push(el);
                        }
                    });
                    
                    // Group elements that are likely to be part of the same star rating component
                    var groups = [];
                    var currentGroup = [];
                    var lastTop = -1;
                    
                    // Sort by vertical position
                    possibleStars.sort(function(a, b) {
                        return a.getBoundingClientRect().top - b.getBoundingClientRect().top;
                    });
                    
                    // Group elements that are at similar vertical positions
                    possibleStars.forEach(function(el) {
                        var rect = el.getBoundingClientRect();
                        if (lastTop === -1 || Math.abs(rect.top - lastTop) < 10) {
                            currentGroup.push(el);
                        } else {
                            if (currentGroup.length >= 3) { // At least 3 elements to be considered a star rating
                                groups.push(currentGroup);
                            }
                            currentGroup = [el];
                        }
                        lastTop = rect.top;
                    });
                    
                    if (currentGroup.length >= 3) {
                        groups.push(currentGroup);
                    }
                    
                    // Return the largest group, which is likely to be the star rating
                    if (groups.length > 0) {
                        groups.sort(function(a, b) {
                            return b.length - a.length;
                        });
                        return groups[0];
                    }
                    
                    return [];
                """)
                
                if star_elements and len(star_elements) >= 3:
                    print("✅ Found star rating elements by grouping clickable elements")
                else:
                    # If we still can't find star elements, try to find any clickable elements in the top half of the page
                    star_elements = driver.execute_script("""
                        var clickableElements = [];
                        var middleY = window.innerHeight / 3;
                        
                        document.querySelectorAll('*').forEach(function(el) {
                            var rect = el.getBoundingClientRect();
                            if (rect.top < middleY && rect.top > 0 && rect.width > 10 && rect.height > 10) {
                                if (el.onclick || el.parentElement.onclick || 
                                    window.getComputedStyle(el).cursor === 'pointer' ||
                                    window.getComputedStyle(el.parentElement).cursor === 'pointer') {
                                    clickableElements.push(el);
                                }
                            }
                        });
                        
                        // Sort by horizontal position (left to right)
                        clickableElements.sort(function(a, b) {
                            return a.getBoundingClientRect().left - b.getBoundingClientRect().left;
                        });
                        
                        // Return elements that are likely to be in a row (similar vertical position)
                        var result = [];
                        var lastElement = null;
                        
                        for (var i = 0; i < clickableElements.length; i++) {
                            var el = clickableElements[i];
                            if (!lastElement || Math.abs(el.getBoundingClientRect().top - lastElement.getBoundingClientRect().top) < 10) {
                                result.push(el);
                                lastElement = el;
                            }
                            
                            if (result.length >= 5) {
                                break;
                            }
                        }
                        
                        return result;
                    """)
                    
                    if star_elements and len(star_elements) >= 3:
                        print("✅ Found potential star rating elements in the top section of the page")
            except Exception as e:
                print(f"Error during JavaScript star finding: {str(e)}")
        
        # If we still couldn't find star elements, try to find them in a nested iframe
        if not star_elements:
            # Switch back to main content
            driver.switch_to.default_content()
            print("Switched back to main content to look for nested iframes")
            
            # Look for nested iframes
            nested_iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in nested_iframes:
                try:
                    iframe_src = iframe.get_attribute("src") or ""
                    if "ReviewsService" in iframe_src or "writereview" in iframe_src or "review" in iframe_src:
                        print(f"Found nested review iframe: {iframe_src}")
                        driver.switch_to.frame(iframe)
                        
                        # Take a screenshot after switching to nested iframe
                        screenshot_path = os.path.join(debug_folder, "inside_nested_iframe.png")
                        driver.save_screenshot(screenshot_path)
                        
                        # Try to find star elements again
                        for selector in star_selectors:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements and len(elements) >= 5:
                                star_elements = elements
                                used_selector = selector
                                print(f"✅ Found star rating elements in nested iframe using selector: {selector}")
                                break
                        
                        if star_elements:
                            break
                        else:
                            # Switch back to main content
                            driver.switch_to.default_content()
                except:
                    # Switch back to main content
                    driver.switch_to.default_content()
                    continue
        
        # If we still couldn't find star elements, try one more approach
        if not star_elements:
            # Switch back to main content
            driver.switch_to.default_content()
            print("Switched back to main content for final attempt")
            
            # Try to find a button or element that might reveal the star rating
            try:
                reveal_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "button, div[role='button'], span[role='button'], div.rating-container, div.star-rating-container")
                
                for element in reveal_elements:
                    try:
                        element_text = element.text.lower()
                        if "rate" in element_text or "star" in element_text or "review" in element_text:
                            print(f"Clicking element that might reveal star rating: {element_text}")
                            element.click()
                            time.sleep(1)
                            
                            # Try to find star elements again
                            for selector in star_selectors:
                                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                if elements and len(elements) >= 5:
                                    star_elements = elements
                                    used_selector = selector
                                    print(f"✅ Found star rating elements after clicking reveal element, using selector: {selector}")
                                    break
                            
                            if star_elements:
                                break
                    except:
                        continue
            except:
                pass
        
        # If we found star elements, click the appropriate one
        if star_elements and len(star_elements) >= rating:
            print(f"✅ Setting {rating} star rating")
            
            # Take a screenshot before clicking
            screenshot_path = os.path.join(debug_folder, "before_clicking_star.png")
            driver.save_screenshot(screenshot_path)
            
            # Debug: Print information about the star elements
            print(f"Found {len(star_elements)} star elements")
            for i, star in enumerate(star_elements):
                try:
                    aria_label = star.get_attribute("aria-label") or ""
                    print(f"Star {i+1}: aria-label='{aria_label}'")
                except:
                    pass
            
            # Try standard click first
            try:
                # Adjust index based on the order of stars (0-indexed or 1-indexed)
                # Some sites have stars in reverse order
                if used_selector and "aria-label" in used_selector:
                    # For aria-label selectors, we can determine the correct star by the label
                    star_found = False
                    for star in star_elements:
                        aria_label = star.get_attribute("aria-label") or ""
                        # Look for exact match of the rating in the aria-label
                        if f"{rating} star" in aria_label.lower():
                            star.click()
                            print(f"✅ Clicked {rating} star rating by exact aria-label match")
                            star_found = True
                            break
                    
                    if not star_found:
                        # If we couldn't find by exact aria-label match, try by index
                        # Ensure we're clicking the correct star (rating is 1-5, but array is 0-indexed)
                        star_index = rating - 1
                        if star_index < len(star_elements):
                            star_elements[star_index].click()
                            print(f"✅ Clicked {rating} star rating by index (0-indexed)")
                else:
                    # Try to determine if stars are in reverse order
                    try:
                        first_star_rect = star_elements[0].rect
                        last_star_rect = star_elements[-1].rect
                        
                        # If the first star is to the right of the last star, they're in reverse order
                        if first_star_rect['x'] > last_star_rect['x']:
                            print("Stars appear to be in reverse order")
                            # For reverse order, we need to count from the end
                            # If rating is 5, we want the first element (index 0)
                            # If rating is 4, we want the second element (index 1), etc.
                            reverse_index = 5 - rating
                            if reverse_index < len(star_elements):
                                star_elements[reverse_index].click()
                                print(f"✅ Clicked {rating} star rating in reverse order (index: {reverse_index})")
                        else:
                            # Normal order (left to right)
                            # Ensure we're clicking the correct star (rating is 1-5, but array is 0-indexed)
                            star_index = rating - 1
                            if star_index < len(star_elements):
                                star_elements[star_index].click()
                                print(f"✅ Clicked {rating} star rating in normal order (index: {star_index})")
                    except Exception as order_error:
                        print(f"Error determining star order: {str(order_error)}")
                        # Fall back to assuming normal order
                        # Ensure we're clicking the correct star (rating is 1-5, but array is 0-indexed)
                        star_index = rating - 1
                        if star_index < len(star_elements):
                            star_elements[star_index].click()
                            print(f"✅ Clicked {rating} star rating (fallback, index: {star_index})")
                
                print(f"✅ Clicked {rating} star rating")
            except Exception as e:
                print(f"Error clicking star with standard method: {str(e)}")
                
                # Try JavaScript click as fallback
                try:
                    # Ensure we're clicking the correct star (rating is 1-5, but array is 0-indexed)
                    star_index = rating - 1
                    if star_index < len(star_elements):
                        driver.execute_script("arguments[0].click();", star_elements[star_index])
                        print(f"✅ Clicked {rating} star rating with JavaScript (index: {star_index})")
                except Exception as e2:
                    print(f"Error clicking star with JavaScript: {str(e2)}")
                    
                    # Try another JavaScript approach
                    try:
                        # Try a more robust JavaScript approach to find and click the exact star by rating
                        js_script = f"""
                        // Find all star elements
                        var allStars = document.querySelectorAll('[aria-label*="star"], [role="radio"], .rating-star, .star-rating, [jsaction*="star"], [jsaction*="rating"]');
                        console.log('Found ' + allStars.length + ' potential star elements');
                        
                        // Try to find the {rating}-star element
                        var targetStar = null;
                        
                        // First try: Look for exact aria-label match
                        for (var i = 0; i < allStars.length; i++) {{
                            var ariaLabel = allStars[i].getAttribute('aria-label') || '';
                            if (ariaLabel.toLowerCase().includes('{rating} star')) {{
                                targetStar = allStars[i];
                                console.log('Found star by exact aria-label match: ' + ariaLabel);
                                break;
                            }}
                        }}
                        
                        // Second try: If we have exactly 5 stars, use index
                        if (!targetStar) {{
                            // Group stars that are at the same vertical position
                            var starGroups = [];
                            var currentGroup = [];
                            var lastTop = -1;
                            
                            // Sort by vertical position
                            var sortedStars = Array.from(allStars).sort(function(a, b) {{
                                return a.getBoundingClientRect().top - b.getBoundingClientRect().top;
                            }});
                            
                            // Group elements that are at similar vertical positions
                            sortedStars.forEach(function(el) {{
                                var rect = el.getBoundingClientRect();
                                if (lastTop === -1 || Math.abs(rect.top - lastTop) < 10) {{
                                    currentGroup.push(el);
                                }} else {{
                                    if (currentGroup.length > 0) {{
                                        starGroups.push(currentGroup);
                                    }}
                                    currentGroup = [el];
                                }}
                                lastTop = rect.top;
                            }});
                            
                            if (currentGroup.length > 0) {{
                                starGroups.push(currentGroup);
                            }}
                            
                            // Find the group with 5 stars
                            for (var i = 0; i < starGroups.length; i++) {{
                                if (starGroups[i].length === 5) {{
                                    // Sort by horizontal position
                                    var horizontalSorted = starGroups[i].sort(function(a, b) {{
                                        return a.getBoundingClientRect().left - b.getBoundingClientRect().left;
                                    }});
                                    
                                    // Get the star at the specified rating (0-indexed)
                                    targetStar = horizontalSorted[{rating - 1}];
                                    console.log('Found star by position in group of 5');
                                    break;
                                }}
                            }}
                        }}
                        
                        // Click the target star if found
                        if (targetStar) {{
                            targetStar.click();
                            return true;
                        }}
                        
                        return false;
                        """
                        
                        success = driver.execute_script(js_script)
                        if success:
                            print(f"✅ Clicked {rating} star rating with advanced JavaScript selection")
                        else:
                            # Fall back to the original JavaScript event approach
                            star_index = rating - 1
                            if star_index < len(star_elements):
                                driver.execute_script("""
                                    var event = new MouseEvent('click', {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true
                                    });
                                    arguments[0].dispatchEvent(event);
                                """, star_elements[star_index])
                                print(f"✅ Clicked {rating} star rating with JavaScript event (index: {star_index})")
                    except Exception as e3:
                        print(f"Error clicking star with JavaScript event: {str(e3)}")
                        return False
            
            # Take a screenshot after clicking
            time.sleep(1)
            screenshot_path = os.path.join(debug_folder, "after_clicking_star.png")
            driver.save_screenshot(screenshot_path)
            
            # Verify that the star was selected
            try:
                # Check if any star has an attribute indicating it's selected
                selected = False
                for star in star_elements:
                    aria_checked = star.get_attribute("aria-checked")
                    aria_selected = star.get_attribute("aria-selected")
                    class_name = star.get_attribute("class") or ""
                    
                    if (aria_checked == "true" or aria_selected == "true" or 
                        "selected" in class_name or "checked" in class_name or
                        "active" in class_name):
                        selected = True
                        break
                
                if not selected:
                    print("Star selection not verified by attributes, trying again...")
                    # Try clicking again with JavaScript
                    # Ensure we're clicking the correct star (rating is 1-5, but array is 0-indexed)
                    star_index = rating - 1
                    if star_index < len(star_elements):
                        driver.execute_script("arguments[0].click();", star_elements[star_index])
                        time.sleep(1)
            except:
                pass
            
            return True
        else:
            print(f"❌ Could not find star rating elements (found {len(star_elements) if star_elements else 0})")
            
            # Take a screenshot of the failure
            screenshot_path = os.path.join(debug_folder, "star_rating_failure.png")
            driver.save_screenshot(screenshot_path)
            
            return False
    except Exception as e:
        print(f"❌ Error setting star rating: {str(e)}")
        
        # Take a screenshot of the error
        screenshot_path = os.path.join(debug_folder, "star_rating_error.png")
        driver.save_screenshot(screenshot_path)
        
        return False

def enter_review_text(driver, debug_folder, review_text=None):
    """Enter review text"""
    try:
        # Generate a review text based on rating if not provided
        if review_text is None:
            # Get the star rating from the page if possible
            try:
                star_elements = driver.find_elements(By.CSS_SELECTOR, "div[aria-checked='true'], span[aria-checked='true']")
                if star_elements:
                    # Try to determine the rating from the selected star
                    aria_label = star_elements[0].get_attribute("aria-label") or ""
                    if "1 star" in aria_label:
                        detected_rating = 1
                    elif "2 star" in aria_label:
                        detected_rating = 2
                    elif "3 star" in aria_label:
                        detected_rating = 3
                    elif "4 star" in aria_label:
                        detected_rating = 4
                    elif "5 star" in aria_label:
                        detected_rating = 5
                    else:
                        # Default to 5 stars if we can't determine
                        detected_rating = 5
                else:
                    # Default to 5 stars if we can't find selected stars
                    detected_rating = 5
            except:
                # Default to 5 stars if there's an error
                detected_rating = 5
            
            # Generate review text based on rating
            if detected_rating == 1:
                negative_reviews = [
                    "Very disappointed with the service.",
                    "Would not recommend this place at all.",
                    "Had a terrible experience here.",
                    "Service was extremely poor.",
                    "Will not be returning after this experience."
                ]
                review_text = random.choice(negative_reviews)
            elif detected_rating == 2:
                poor_reviews = [
                    "Below average experience overall.",
                    "Several issues with the service provided.",
                    "Not what I expected for the price.",
                    "Staff could be more helpful.",
                    "Needs significant improvement."
                ]
                review_text = random.choice(poor_reviews)
            elif detected_rating == 3:
                average_reviews = [
                    "Average experience, nothing special.",
                    "Some good points but also some issues.",
                    "Decent service but room for improvement.",
                    "Met basic expectations but didn't exceed them.",
                    "Okay for the price, but wouldn't go out of my way to return."
                ]
                review_text = random.choice(average_reviews)
            elif detected_rating == 4:
                good_reviews = [
                    "Good experience overall, would recommend.",
                    "Very satisfied with the service provided.",
                    "Professional staff and good quality.",
                    "Above average experience, will return.",
                    "Impressed with most aspects of the service."
                ]
                review_text = random.choice(good_reviews)
            else:  # 5 stars
                excellent_reviews = [
                    "Excellent service and friendly staff!",
                    "Outstanding experience from start to finish!",
                    "Couldn't be happier with my experience here.",
                    "Absolutely top-notch service, highly recommend!",
                    "Fantastic experience, will definitely return!",
                    "Exceeded my expectations in every way.",
                    "Wonderful staff and excellent service!",
                    "Best experience I've had in a long time.",
                    "Absolutely love this place, 5 stars well deserved!",
                    "Perfect in every way, highly recommended!"
                ]
                review_text = random.choice(excellent_reviews)
        
        print(f"Selected review text: {review_text}")
        
        # Take a screenshot before attempting to locate the review text area
        screenshot_path = os.path.join(debug_folder, "before_review_text.png")
        driver.save_screenshot(screenshot_path)
        
        # Switch to main content to start fresh
        driver.switch_to.default_content()
        print("Switched to main content to start fresh")
        
        # Find all iframes on the page
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Found {len(iframes)} iframes on the page")
        
        # First, check if we're in a review iframe
        review_iframe = None
        for iframe in iframes:
            try:
                iframe_src = iframe.get_attribute("src") or ""
                print(f"Checking iframe with src: {iframe_src}")
                if "ReviewsService" in iframe_src or "writereview" in iframe_src or "review" in iframe_src:
                    review_iframe = iframe
                    print(f"✅ Found main review iframe: {iframe_src}")
                    break
            except:
                continue
        
        # Switch to the review iframe if found
        if review_iframe:
            driver.switch_to.frame(review_iframe)
            print("Switched to review iframe for text input")
            
            # Take a screenshot after switching to iframe
            screenshot_path = os.path.join(debug_folder, "inside_review_iframe_text.png")
            driver.save_screenshot(screenshot_path)
        
        # Try to find the review widget div
        try:
            widget_div = driver.find_element(By.CSS_SELECTOR, "div.goog-reviews-write-widget-model, div[jsmodel*='ReviewsWrite']")
            print("Found review widget div")
        except Exception as e:
            print(f"Error finding widget div: {str(e)}")
            
            # If we couldn't find the widget div, try to find a nested iframe
            nested_iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in nested_iframes:
                try:
                    iframe_src = iframe.get_attribute("src") or ""
                    if "ReviewsService" in iframe_src or "writereview" in iframe_src or "review" in iframe_src:
                        print(f"Found nested review iframe: {iframe_src}")
                        driver.switch_to.frame(iframe)
                        break
                except:
                    continue
        
        # Try to find the textarea with multiple selectors
        textarea = None
        textarea_selectors = [
            "textarea[name='goog-reviews-write-widget']",
            "form[name='goog-reviews-write-widget'] textarea",
            "textarea[aria-label*='review']",
            "textarea[aria-label*='Review']",
            "textarea[placeholder*='review']",
            "textarea[placeholder*='Review']",
            "textarea"
        ]
        
        for selector in textarea_selectors:
            print(f"Trying to find textarea with selector: {selector}")
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                textarea = elements[0]
                print(f"✅ Found textarea with selector: {selector}")
                break
        
        # If we couldn't find the textarea, try JavaScript
        if not textarea:
            print("Trying JavaScript to find textarea...")
            try:
                textarea = driver.execute_script("""
                    // Try to find textarea by various methods
                    var textarea = document.querySelector('textarea');
                    if (textarea) return textarea;
                    
                    // Try to find by aria-label
                    var elements = document.querySelectorAll('[aria-label]');
                    for (var i = 0; i < elements.length; i++) {
                        var el = elements[i];
                        var label = el.getAttribute('aria-label').toLowerCase();
                        if (label.includes('review') || label.includes('comment') || label.includes('feedback')) {
                            if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT' || el.getAttribute('contenteditable') === 'true') {
                                return el;
                            }
                        }
                    }
                    
                    // Try to find contenteditable div
                    var editables = document.querySelectorAll('[contenteditable="true"]');
                    if (editables.length > 0) return editables[0];
                    
                    // Try to find any input that looks like it could be for reviews
                    var inputs = document.querySelectorAll('input[type="text"], input:not([type])');
                    for (var i = 0; i < inputs.length; i++) {
                        var input = inputs[i];
                        if (input.offsetWidth > 200) { // Likely a text input field
                            return input;
                        }
                    }
                    
                    return null;
                """)
                
                if textarea:
                    print("✅ Found textarea using JavaScript")
            except Exception as e:
                print(f"Error finding textarea with JavaScript: {str(e)}")
        
        # If we still couldn't find the textarea, try to find it by tag name
        if not textarea:
            print("Trying to find textarea by tag name...")
            try:
                textareas = driver.find_elements(By.TAG_NAME, "textarea")
                if textareas:
                    textarea = textareas[0]
                    print("✅ Found textarea by tag name")
            except Exception as e:
                print(f"Error finding textarea by tag name: {str(e)}")
        
        # If we still couldn't find the textarea, try switching to a different iframe
        if not textarea:
            # Switch back to main content
            driver.switch_to.default_content()
            print("Switched back to main content")
            
            # Try each iframe
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    print(f"Checking iframe for textarea")
                    
                    # Take a screenshot
                    screenshot_path = os.path.join(debug_folder, f"checking_iframe_for_textarea.png")
                    driver.save_screenshot(screenshot_path)
                    
                    # Try to find textarea
                    textareas = driver.find_elements(By.TAG_NAME, "textarea")
                    if textareas:
                        textarea = textareas[0]
                        print("✅ Found iframe with textarea")
                        break
                    
                    # Try contenteditable divs
                    editables = driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
                    if editables:
                        textarea = editables[0]
                        print("✅ Found iframe with contenteditable div")
                        break
                    
                    # Switch back to main content
                    driver.switch_to.default_content()
                except:
                    # Switch back to main content
                    driver.switch_to.default_content()
                    continue
        
        # If we still couldn't find the textarea, try clicking on form elements to reveal it
        if not textarea:
            # Switch back to main content
            driver.switch_to.default_content()
            print("Switched back to main content")
            
            # Try to find and click elements that might reveal the textarea
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, 
                    "div.review-form, div.review-dialog, div[role='dialog'], div.modal-content")
                
                for element in elements:
                    try:
                        element.click()
                        print("Clicked on potential review form container")
                        
                        # Try to find textarea again
                        textareas = driver.find_elements(By.TAG_NAME, "textarea")
                        if textareas:
                            textarea = textareas[0]
                            print("✅ Found textarea after clicking container")
                            break
                    except:
                        continue
            except:
                pass
        
        # If we still couldn't find the textarea, try using tab key to navigate to it
        if not textarea:
            print("Trying to use tab key to navigate to textarea...")
            try:
                # First, try to click somewhere in the form
                try:
                    form_elements = driver.find_elements(By.CSS_SELECTOR, 
                        "div.review-form, div.review-dialog, div[role='dialog'], div.modal-content, form")
                    
                    if form_elements:
                        form_elements[0].click()
                        print("Clicked on form element")
                except:
                    # If we couldn't click a form element, click on the body
                    driver.find_element(By.TAG_NAME, "body").click()
                    print("Clicked on body")
                
                # Press tab key multiple times to try to reach the textarea
                body = driver.find_element(By.TAG_NAME, "body")
                for _ in range(10):
                    body.send_keys(Keys.TAB)
                    time.sleep(0.5)
                    
                    # Check if we've focused a textarea
                    active_element = driver.execute_script("return document.activeElement;")
                    tag_name = driver.execute_script("return arguments[0].tagName.toLowerCase();", active_element)
                    
                    if tag_name == "textarea":
                        textarea = active_element
                        print("✅ Found textarea using tab navigation")
                        break
                    
                    if tag_name == "div" and driver.execute_script("return arguments[0].getAttribute('contenteditable') === 'true';", active_element):
                        textarea = active_element
                        print("✅ Found contenteditable div using tab navigation")
                        break
            except Exception as e:
                print(f"Error using tab navigation: {str(e)}")
        
        # If we found the textarea, enter the review text
        if textarea:
            try:
                # Clear any existing text
                textarea.clear()
                print("Cleared existing text")
                
                # Focus on the textarea
                driver.execute_script("arguments[0].focus();", textarea)
                print("Focused on textarea")
                
                # Try standard send_keys first
                textarea.send_keys(review_text)
                print("Entered text using standard send_keys")
                
                # Verify that the text was entered
                entered_text = driver.execute_script("return arguments[0].value || arguments[0].textContent;", textarea)
                if entered_text:
                    print(f"✅ Verified text was entered: {entered_text}")
                else:
                    # If standard send_keys didn't work, try JavaScript
                    print("Standard send_keys didn't work, trying JavaScript...")
                    
                    # Try setting value property
                    driver.execute_script("arguments[0].value = arguments[1];", textarea, review_text)
                    
                    # Try setting textContent for contenteditable elements
                    driver.execute_script("""
                        if (arguments[0].getAttribute('contenteditable') === 'true') {
                            arguments[0].textContent = arguments[1];
                        }
                    """, textarea, review_text)
                    
                    # Dispatch input event
                    driver.execute_script("""
                        var event = new Event('input', {
                            bubbles: true,
                            cancelable: true
                        });
                        arguments[0].dispatchEvent(event);
                    """, textarea)
                    
                    print("Entered text using JavaScript")
                
                # Take a screenshot after entering text
                screenshot_path = os.path.join(debug_folder, "after_entering_text.png")
                driver.save_screenshot(screenshot_path)
                
                print(f"✅ Entered review text: {review_text}")
                return True
            except Exception as e:
                print(f"Error entering review text: {str(e)}")
                
                # Take a screenshot of the error
                screenshot_path = os.path.join(debug_folder, "text_entry_error.png")
                driver.save_screenshot(screenshot_path)
                
                return False
        else:
            print("❌ Could not find textarea")
            
            # Take a screenshot of the failure
            screenshot_path = os.path.join(debug_folder, "textarea_not_found.png")
            driver.save_screenshot(screenshot_path)
            
            return False
    except Exception as e:
        print(f"❌ Error entering review text: {str(e)}")
        
        # Take a screenshot of the error
        screenshot_path = os.path.join(debug_folder, "review_text_error.png")
        driver.save_screenshot(screenshot_path)
        
        return False

def submit_review(driver, debug_folder):
    """Submit the review"""
    try:
        print("Submitting review...")
        
        # Take a screenshot before submission
        screenshot_path = os.path.join(debug_folder, "before_submit.png")
        driver.save_screenshot(screenshot_path)
        
        # Store the initial URL for comparison later
        initial_url = driver.current_url
        print(f"Initial URL before submission: {initial_url}")
        
        # Switch to main content for submit button
        driver.switch_to.default_content()
        print("Switched to main content for submit button")
        
        # Find all iframes on the page
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Found {len(iframes)} iframes on the page")
        
        # First, check if we're in a review iframe
        review_iframe = None
        for iframe in iframes:
            try:
                iframe_src = iframe.get_attribute("src") or ""
                if "ReviewsService" in iframe_src or "writereview" in iframe_src or "review" in iframe_src:
                    review_iframe = iframe
                    print(f"✅ Found main review iframe: {iframe_src}")
                    break
            except:
                continue
        
        # Switch to the review iframe if found
        if review_iframe:
            driver.switch_to.frame(review_iframe)
            print("Switched to review iframe for submit button")
            
            # Take a screenshot after switching to iframe
            screenshot_path = os.path.join(debug_folder, "inside_review_iframe_submit.png")
            driver.save_screenshot(screenshot_path)
        
        # Look for submit button in the review iframe
        print("Looking for submit button in the review iframe...")
        
        # Try to find the submit button using various selectors
        submit_button = None
        submit_button_selectors = [
            "button[jsname='LgbsSe']",
            "button.goog-buttonset-default",
            "button.submit-button",
            "button[type='submit']",
            "button.VfPpkd-LgbsSe",
            "button.mdc-button",
            "button.gmat-mdc-button",
            "button.gm-submit-button",
            "button.g-button",
            "input[type='submit']"
        ]
        
        for selector in submit_button_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    try:
                        button_text = button.text.lower()
                        if "post" in button_text or "submit" in button_text or "publish" in button_text or "share" in button_text:
                            submit_button = button
                            print(f"✅ Found submit button with selector: {selector}, text: {button.text}")
                            break
                    except:
                        continue
                
                if submit_button:
                    break
            except:
                continue
        
        # If we couldn't find the submit button with selectors, try JavaScript
        if not submit_button:
            print("Trying to find submit button by text content...")
            try:
                submit_button = driver.execute_script("""
                    // Find buttons by text content
                    var buttons = document.querySelectorAll('button, input[type="submit"], div[role="button"]');
                    for (var i = 0; i < buttons.length; i++) {
                        var button = buttons[i];
                        var text = button.textContent.toLowerCase();
                        if (text.includes('post') || text.includes('submit') || text.includes('publish') || text.includes('share')) {
                            return button;
                        }
                    }
                    
                    // If no button found by text, look for buttons in the bottom section of the form
                    var forms = document.querySelectorAll('form, div[role="dialog"], div.review-dialog, div.modal-content');
                    if (forms.length > 0) {
                        var form = forms[0];
                        var formRect = form.getBoundingClientRect();
                        var formBottom = formRect.bottom;
                        var formHeight = formRect.height;
                        
                        // Look for buttons in the bottom 20% of the form
                        var bottomButtons = [];
                        buttons.forEach(function(button) {
                            var rect = button.getBoundingClientRect();
                            if (rect.top > formBottom - (formHeight * 0.2)) {
                                bottomButtons.push(button);
                            }
                        });
                        
                        // Return the rightmost button (usually the submit button)
                        if (bottomButtons.length > 0) {
                            bottomButtons.sort(function(a, b) {
                                return b.getBoundingClientRect().right - a.getBoundingClientRect().right;
                            });
                            return bottomButtons[0];
                        }
                    }
                    
                    // Last resort: find any button that looks like a primary action
                    var primaryButtons = document.querySelectorAll('button.primary, button.submit, button[type="submit"], button.mdc-button--raised, button.mdc-button--unelevated');
                    if (primaryButtons.length > 0) {
                        return primaryButtons[0];
                    }
                    
                    return null;
                """)
                
                if submit_button:
                    print("✅ Found submit button by text content")
                    
                    # Get button details for debugging
                    button_tag = driver.execute_script("return arguments[0].tagName;", submit_button)
                    button_classes = driver.execute_script("return arguments[0].className;", submit_button)
                    button_id = driver.execute_script("return arguments[0].id;", submit_button)
                    button_text = driver.execute_script("return arguments[0].textContent;", submit_button)
                    
                    print(f"Button details - Tag: {button_tag}, Classes: {button_classes}, ID: {button_id}, Text: '{button_text}'")
                    
                    # Get button attributes for debugging
                    button_attributes = driver.execute_script("""
                        var attributes = {};
                        var attrs = arguments[0].attributes;
                        for (var i = 0; i < attrs.length; i++) {
                            attributes[attrs[i].name] = attrs[i].value;
                        }
                        return JSON.stringify(attributes);
                    """, submit_button)
                    
                    print(f"Button attributes: {button_attributes}")
            except Exception as e:
                print(f"Error finding submit button with JavaScript: {str(e)}")
        
        # If we found the submit button, click it
        if submit_button:
            # Take a screenshot before clicking
            screenshot_path = os.path.join(debug_folder, "before_clicking_submit.png")
            driver.save_screenshot(screenshot_path)
            
            # Store the button text for verification later
            try:
                button_text_before = driver.execute_script("return arguments[0].textContent;", submit_button)
                print(f"Button text before clicking: '{button_text_before}'")
            except:
                button_text_before = None
            
            # Try standard click first
            try:
                # Scroll to the button to make sure it's in view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
                time.sleep(0.5)
                
                # Try to remove any overlays that might be blocking the button
                driver.execute_script("""
                    // Remove any overlays or modals that might be blocking clicks
                    var overlays = document.querySelectorAll('div[aria-hidden="true"], div.overlay, div.modal-bg, div.backdrop');
                    for (var i = 0; i < overlays.length; i++) {
                        var overlay = overlays[i];
                        overlay.style.display = 'none';
                        overlay.style.visibility = 'hidden';
                        overlay.style.opacity = '0';
                        overlay.style.pointerEvents = 'none';
                    }
                """)
                
                # Click the button
                submit_button.click()
                print("Clicked submit button using standard click")
            except Exception as e:
                print(f"Standard click failed: {str(e)}")
                
                # Try JavaScript click as fallback
                try:
                    driver.execute_script("arguments[0].click();", submit_button)
                    print("Clicked submit button using direct JavaScript click")
                except Exception as e2:
                    print(f"JavaScript click failed: {str(e2)}")
                    
                    # Try another JavaScript approach
                    try:
                        driver.execute_script("""
                            var event = new MouseEvent('click', {
                                view: window,
                                bubbles: true,
                                cancelable: true
                            });
                            arguments[0].dispatchEvent(event);
                        """, submit_button)
                        print("Clicked submit button using JavaScript event")
                    except Exception as e3:
                        print(f"JavaScript event click failed: {str(e3)}")
                        return False
            
            # Wait for submission to complete
            print("Waiting for submission to complete...")
            time.sleep(3)
            
            # Take a screenshot after clicking
            screenshot_path = os.path.join(debug_folder, "after_clicking_submit.png")
            driver.save_screenshot(screenshot_path)
            
            # Check if URL changed (indication of successful submission)
            current_url = driver.current_url
            print(f"Current URL after submission: {current_url}")
            
            url_changed = current_url != initial_url
            if url_changed:
                print("✅ URL changed after submission, likely successful")
            
            # Check if button state changed
            button_state_changed = False
            try:
                button_text_after = driver.execute_script("return arguments[0].textContent;", submit_button)
                print(f"Button text after clicking: '{button_text_after}'")
                
                if button_text_before and button_text_after and button_text_before != button_text_after:
                    print("✅ Button text changed after clicking, likely successful")
                    button_state_changed = True
                
                # Check if button is disabled
                button_disabled = driver.execute_script("return arguments[0].disabled === true || arguments[0].getAttribute('aria-disabled') === 'true';", submit_button)
                if button_disabled:
                    print("✅ Button is now disabled, likely successful")
                    button_state_changed = True
            except Exception as e:
                print(f"Error checking button state: {str(e)}")
                # If we get a stale element reference, the page has changed, which is good
                if "stale element reference" in str(e):
                    print("✅ Button is now stale, page has changed, likely successful")
                    button_state_changed = True
            
            # Check for confirmation elements
            confirmation_found = False
            try:
                # Switch back to default content
                driver.switch_to.default_content()
                
                # Look for confirmation messages or elements
                confirmation_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "div.confirmation-message, div.success-message, div.thank-you-message, div[role='alert']")
                
                for element in confirmation_elements:
                    try:
                        element_text = element.text.lower()
                        if "thank" in element_text or "success" in element_text or "submitted" in element_text:
                            print(f"✅ Found confirmation message: {element_text}")
                            confirmation_found = True
                            break
                    except:
                        continue
            except:
                pass
            
            # Check if review form elements are no longer visible
            form_elements_gone = False
            try:
                # Switch back to default content
                driver.switch_to.default_content()
                
                # Try to find the review form elements
                star_elements = driver.find_elements(By.CSS_SELECTOR, "div[aria-label*='star'], span[aria-label*='star']")
                textarea_elements = driver.find_elements(By.TAG_NAME, "textarea")
                
                if len(star_elements) == 0 and len(textarea_elements) == 0:
                    print("✅ Review form elements are no longer visible, submission likely successful")
                    form_elements_gone = True
            except:
                pass
            
            # Determine if submission was successful based on all checks
            submission_successful = url_changed or button_state_changed or confirmation_found or form_elements_gone
            
            if submission_successful:
                print("✅ Review submission appears to be successful")
                return True
            else:
                print("❌ Could not verify successful submission")
                return False
        else:
            print("❌ Could not find submit button")
            return False
    except Exception as e:
        print(f"❌ Error submitting review: {str(e)}")
        
        # Take a screenshot of the error
        screenshot_path = os.path.join(debug_folder, "submit_error.png")
        driver.save_screenshot(screenshot_path)
        
        return False

def find_and_click_review_button(driver, debug_folder):
    """Find and click the review button"""
    try:
        # Try different selectors for the review button
        selectors = [
            "a[href*='review'], a[data-href*='review']",
            "button[aria-label*='review'], button[jsaction*='review']",
            "div[aria-label*='review'], div[jsaction*='review']",
            "span[aria-label*='review'], span[jsaction*='review']",
            "button:contains('Review')",
            "div[role='button']:contains('Review')",
            "a:contains('Review')"
        ]
        
        for selector in selectors:
            try:
                if ':contains' in selector:
                    # Handle jQuery-like selectors with JavaScript
                    element_type = selector.split(':contains')[0]
                    text = selector.split(':contains(')[1].replace("')", "").replace('")', '')
                    js_script = f"""
                        return Array.from(document.querySelectorAll('{element_type}')).find(el => 
                            el.textContent.toLowerCase().includes('{text.lower()}')
                        );
                    """
                    review_button = driver.execute_script(js_script)
                else:
                    review_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                if review_button:
                    # Save screenshot before clicking
                    screenshot_path = os.path.join(debug_folder, "review_button_found.png")
                    driver.save_screenshot(screenshot_path)
                    
                    print(f"✅ Found review button using selector: {selector}")
                    
                    # Try to click the button
                    try:
                        # Try regular click
                        review_button.click()
                        print("✅ Clicked review button")
                    except:
                        # Try JavaScript click
                        print("Regular click failed, trying JavaScript click...")
                        driver.execute_script("arguments[0].click();", review_button)
                        print("✅ Clicked review button using JavaScript")
                    
                    # Wait for the review form to load
                    time.sleep(3)
                    
                    # Save screenshot after clicking
                    screenshot_path = os.path.join(debug_folder, "after_review_button_click.png")
                    driver.save_screenshot(screenshot_path)
                    
                    return True
            except:
                continue
        
        # If we couldn't find the review button with selectors, try JavaScript
        print("Trying JavaScript approach to find review button...")
        
        # Save screenshot
        screenshot_path = os.path.join(debug_folder, "before_js_review_button.png")
        driver.save_screenshot(screenshot_path)
        
        # Use JavaScript to find review button
        js_script = """
            // Try to find by text content
            let elements = Array.from(document.querySelectorAll('a, button, div[role="button"], span[role="button"]'));
            
            // First try exact matches
            let reviewButton = elements.find(el => 
                el.textContent.trim().toLowerCase() === 'review' || 
                el.textContent.trim().toLowerCase() === 'write a review' ||
                el.textContent.trim().toLowerCase() === 'write review'
            );
            
            if (reviewButton) return reviewButton;
            
            // Then try contains
            reviewButton = elements.find(el => 
                el.textContent.toLowerCase().includes('review') || 
                el.textContent.toLowerCase().includes('write a review')
            );
            
            if (reviewButton) return reviewButton;
            
            // Try by aria-label
            reviewButton = Array.from(document.querySelectorAll('*')).find(el => {
                const ariaLabel = el.getAttribute('aria-label');
                return ariaLabel && (
                    ariaLabel.toLowerCase().includes('review') || 
                    ariaLabel.toLowerCase().includes('write a review')
                );
            });
            
            if (reviewButton) return reviewButton;
            
            // Try by href
            reviewButton = Array.from(document.querySelectorAll('a')).find(el => {
                const href = el.getAttribute('href');
                return href && href.includes('review');
            });
            
            return reviewButton;
        """
        review_button = driver.execute_script(js_script)
        
        if review_button:
            print("✅ Found review button using JavaScript")
            
            # Save screenshot before clicking
            screenshot_path = os.path.join(debug_folder, "js_review_button_found.png")
            driver.save_screenshot(screenshot_path)
            
            # Try to click the button
            try:
                driver.execute_script("arguments[0].click();", review_button)
                print("✅ Clicked review button using JavaScript")
            except:
                print("❌ JavaScript click failed")
            
            # Wait for the review form to load
            time.sleep(3)
            
            # Save screenshot after clicking
            screenshot_path = os.path.join(debug_folder, "after_js_review_button_click.png")
            driver.save_screenshot(screenshot_path)
            
            return True
        
        # If we still couldn't find the review button, check if we're already on a review page
        if "writereview" in driver.current_url or "placeid" in driver.current_url:
            print("✅ Already on a review page based on URL")
            return True
        
        print("❌ Could not find review button")
        
        # Save screenshot
        screenshot_path = os.path.join(debug_folder, "review_button_not_found.png")
        driver.save_screenshot(screenshot_path)
        
        return False
        
    except Exception as e:
        print(f"❌ Error finding review button: {str(e)}")
        
        # Save screenshot
        screenshot_path = os.path.join(debug_folder, "review_button_error.png")
        driver.save_screenshot(screenshot_path)
        
        return False

def initialize_chrome_driver(chrome_profile_path=None):
    """Initialize Chrome driver with the specified profile path"""
    try:
        # Use the provided profile path or default to 'chrome_profile'
        if chrome_profile_path is None:
            chrome_profile_path = os.path.join(os.getcwd(), "chrome_profile")
        elif not os.path.isabs(chrome_profile_path):
            chrome_profile_path = os.path.join(os.getcwd(), chrome_profile_path)
        
        print(f"Using Chrome profile at: {chrome_profile_path}")
        
        # Ensure the profile directory exists
        os.makedirs(chrome_profile_path, exist_ok=True)
        
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
                
                # Add script to remove navigator.webdriver flag
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

if __name__ == "__main__":
    post_review() 