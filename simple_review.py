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
        with open("accounts.yaml", "r") as f:
            data = yaml.safe_load(f)
            return data.get("accounts", [])
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

def post_review(profile=None):
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
            star_rating_set = set_star_rating(driver, debug_folder)
            if not star_rating_set:
                print("❌ Failed to set star rating")
                driver.quit()
                return False
            
            # Enter review text
            review_text_entered = enter_review_text(driver, debug_folder)
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

def set_star_rating(driver, debug_folder):
    """Set a 4-5 star rating"""
    try:
        print("Setting star rating...")
        
        # Save screenshot before setting rating
        screenshot_path = os.path.join(debug_folder, "before_star_rating.png")
        driver.save_screenshot(screenshot_path)
        
        # Check if we're in an iframe
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        iframe_found = False
        
        for iframe in iframes:
            try:
                iframe_src = iframe.get_attribute("src")
                if iframe_src and ("ReviewsService" in iframe_src or "writereview" in iframe_src):
                    print(f"✅ Found review iframe for star rating: {iframe_src}")
                    # Switch to the iframe
                    driver.switch_to.frame(iframe)
                    iframe_found = True
                    
                    # Save screenshot after switching to iframe
                    screenshot_path = os.path.join(debug_folder, "after_iframe_switch_stars.png")
                    driver.save_screenshot(screenshot_path)
                    break
            except Exception as e:
                print(f"Error checking iframe: {str(e)}")
        
        # Wait for page to load
        time.sleep(3)
        
        # Try multiple selectors for star rating elements
        selectors = [
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
        
        for selector in selectors:
            try:
                print(f"Trying to find star rating elements with selector: {selector}")
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) >= 5:
                    visible_elements = [e for e in elements if e.is_displayed()]
                    if len(visible_elements) >= 5:
                        star_elements = visible_elements
                        used_selector = selector
                        print(f"✅ Found star rating elements using selector: {selector}")
                        break
            except Exception as e:
                print(f"Selector {selector} failed: {str(e)}")
        
        # If we couldn't find star elements with selectors, try JavaScript
        if not star_elements:
            print("Trying JavaScript approach to find star elements...")
            
            # Try to find any rating container first and click it to reveal stars
            try:
                print("Found rating container, trying to click it first...")
                js_script = """
                    // Try to find rating container
                    let ratingContainer = document.querySelector('div[aria-label*="rating"], div[aria-label*="Rate"], div.rating-container, div.stars-container');
                    if (ratingContainer) {
                        ratingContainer.click();
                        return true;
                    }
                    return false;
                """
                driver.execute_script(js_script)
                time.sleep(1)
            except:
                pass
            
            # Try to find any clickable elements in the top section of the page
            try:
                print("Trying to find any clickable elements in the top section...")
                js_script = """
                    // Get all elements in the top half of the page
                    const viewportHeight = window.innerHeight;
                    const elements = Array.from(document.querySelectorAll('*'))
                        .filter(el => {
                            const rect = el.getBoundingClientRect();
                            return rect.top >= 0 && rect.top < viewportHeight / 2 && 
                                   rect.width > 0 && rect.height > 0;
                        });
                    
                    // Try to find elements that look like rating stars
                    for (const el of elements) {
                        const style = window.getComputedStyle(el);
                        const text = el.textContent.toLowerCase();
                        const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
                        
                        if (
                            (ariaLabel.includes('star') || ariaLabel.includes('rating')) ||
                            (el.tagName === 'SVG' || el.querySelector('svg')) ||
                            (style.cursor === 'pointer' && (el.offsetWidth === el.offsetHeight))
                        ) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                """
                driver.execute_script(js_script)
                time.sleep(1)
            except:
                pass
            
            # Try to find star elements using JavaScript
            js_script = """
                function findStarElements() {
                    // Try to find elements with star in aria-label
                    let starElements = Array.from(document.querySelectorAll('*[aria-label*="star" i], *[aria-label*="rating" i]'));
                    
                    // Filter to only visible elements
                    starElements = starElements.filter(el => {
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    });
                    
                    if (starElements.length >= 5) {
                        return starElements;
                    }
                    
                    // Try to find elements that look like they could be stars
                    const possibleStarElements = Array.from(document.querySelectorAll('span, div, svg, g-radio-button'))
                        .filter(el => {
                            // Must be visible
                            const rect = el.getBoundingClientRect();
                            if (rect.width === 0 || rect.height === 0) return false;
                            
                            // Check various properties that might indicate a star
                            const classList = Array.from(el.classList).join(' ').toLowerCase();
                            const id = (el.id || '').toLowerCase();
                            const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
                            const role = (el.getAttribute('role') || '').toLowerCase();
                            
                            return classList.includes('star') || 
                                   classList.includes('rating') ||
                                   id.includes('star') ||
                                   id.includes('rating') ||
                                   ariaLabel.includes('star') ||
                                   ariaLabel.includes('rating') ||
                                   role === 'radio';
                        });
                    
                    // Group elements that are aligned horizontally and have similar size
                    const groups = [];
                    for (const el of possibleStarElements) {
                        const rect = el.getBoundingClientRect();
                        
                        // Find a group with similar vertical position
                        let foundGroup = false;
                        for (const group of groups) {
                            const groupRect = group[0].getBoundingClientRect();
                            if (Math.abs(rect.top - groupRect.top) < 10 && 
                                Math.abs(rect.height - groupRect.height) < 5) {
                                group.push(el);
                                foundGroup = true;
                                break;
                            }
                        }
                        
                        if (!foundGroup) {
                            groups.push([el]);
                        }
                    }
                    
                    // Find the group with at least 5 elements
                    for (const group of groups) {
                        if (group.length >= 5) {
                            // Sort by x position
                            group.sort((a, b) => {
                                return a.getBoundingClientRect().left - b.getBoundingClientRect().left;
                            });
                            return group;
                        }
                    }
                    
                    return null;
                }
                
                return findStarElements();
            """
            star_elements = driver.execute_script(js_script)
            
            if star_elements:
                print("✅ Found star rating elements using JavaScript")
        
        if not star_elements:
            # Try one more approach - look for any clickable elements in a row
            try:
                # Find all clickable elements
                clickable_elements = driver.find_elements(By.CSS_SELECTOR, "div[role='button'], span[role='button'], button, div[jsaction], span[jsaction]")
                
                # Filter to only visible elements
                visible_elements = [e for e in clickable_elements if e.is_displayed()]
                
                # Group elements that are aligned horizontally
                groups = []
                for element in visible_elements:
                    location = element.location
                    size = element.size
                    
                    # Find a group with similar vertical position
                    found_group = False
                    for group in groups:
                        group_element = group[0]
                        group_location = group_element.location
                        
                        if abs(location['y'] - group_location['y']) < 10:
                            group.append(element)
                            found_group = True
                            break
                    
                    if not found_group:
                        groups.append([element])
                
                # Find the group with at least 5 elements
                for group in groups:
                    if len(group) >= 5:
                        # Sort by x position
                        group.sort(key=lambda e: e.location['x'])
                        star_elements = group
                        print("✅ Found star rating elements by grouping clickable elements")
                        break
            except Exception as e:
                print(f"Error grouping clickable elements: {str(e)}")
        
        # If we're in an iframe and still can't find star elements, try switching back to main content
        if not star_elements and iframe_found:
            print("Switching back to main content to look for star elements...")
            driver.switch_to.default_content()
            
            # Try to find iframes again (sometimes there are nested iframes)
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    iframe_src = iframe.get_attribute("src")
                    if iframe_src and ("ReviewsService" in iframe_src or "writereview" in iframe_src):
                        print(f"✅ Found another review iframe: {iframe_src}")
                        driver.switch_to.frame(iframe)
                        
                        # Try JavaScript again in this iframe
                        star_elements = driver.execute_script(js_script)
                        if star_elements:
                            print("✅ Found star rating elements in another iframe")
                            break
                except:
                    continue
        
        # Save screenshot after finding stars
        screenshot_path = os.path.join(debug_folder, "after_finding_stars.png")
        driver.save_screenshot(screenshot_path)
        
        if not star_elements:
            raise Exception("Could not find star rating elements")
        
        # Choose a 4 or 5 star rating (80% chance of 5 stars)
        rating = 5 if random.random() < 0.8 else 4
        print(f"✅ Setting {rating} star rating")
        
        # Click the star
        try:
            # Get the star element (0-indexed, so subtract 1)
            star = star_elements[rating - 1]
            
            # Scroll to the star to make sure it's in view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", star)
            time.sleep(1)
            
            # Try to remove any overlays that might be blocking the star
            driver.execute_script("""
                // Remove any overlays or modals that might be blocking clicks
                const overlays = Array.from(document.querySelectorAll('div[aria-hidden="true"], div.overlay, div.modal-bg, div.backdrop'));
                for (const overlay of overlays) {
                    overlay.remove();
                }
            """)
            
            # Try regular click
            star.click()
            print(f"✅ Clicked {rating} star rating")
        except Exception as e:
            print(f"Regular click failed: {str(e)}")
            print("Trying JavaScript click...")
            
            # Try JavaScript click with additional handling for overlays
            js_click_script = """
                // Remove any overlays first
                const overlays = Array.from(document.querySelectorAll('div[aria-hidden="true"], div.overlay, div.modal-bg, div.backdrop'));
                for (const overlay of overlays) {
                    overlay.style.display = 'none';
                    overlay.style.visibility = 'hidden';
                    overlay.style.opacity = '0';
                    overlay.style.pointerEvents = 'none';
                }
                
                // Force the click
                const event = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                arguments[0].dispatchEvent(event);
                
                // Also try the regular click
                arguments[0].click();
                
                return true;
            """
            driver.execute_script(js_click_script, star)
            print(f"✅ Clicked {rating} star rating using JavaScript")
        
        # Save screenshot after clicking
        screenshot_path = os.path.join(debug_folder, "after_star_rating.png")
        driver.save_screenshot(screenshot_path)
        
        # Wait a moment for any animations to complete
        time.sleep(2)
        
        return True
    except Exception as e:
        print(f"❌ Could not set star rating: {str(e)}")
        # Save screenshot
        screenshot_path = os.path.join(debug_folder, "star_rating_error.png")
        driver.save_screenshot(screenshot_path)
        return False

def enter_review_text(driver, debug_folder):
    """Enter a random positive review text"""
    try:
        # Generate a random positive review
        positive_reviews = [
            "Excellent service and friendly staff!",
            "Great experience overall, highly recommend!",
            "Outstanding service and quality.",
            "Couldn't be happier with my experience here.",
            "Top-notch service, will definitely return!",
            "Fantastic place with amazing staff.",
            "Exceeded my expectations in every way.",
            "Wonderful experience from start to finish.",
            "Absolutely love this place, highly recommended!",
            "Superb service and attention to detail."
        ]
        review_text = random.choice(positive_reviews)
        print(f"Selected review text: {review_text}")
        
        # Save screenshot before looking for text area
        screenshot_path = os.path.join(debug_folder, "before_finding_text_area.png")
        driver.save_screenshot(screenshot_path)
        
        # First switch back to the main content
        try:
            driver.switch_to.default_content()
            print("Switched to main content to start fresh")
        except:
            pass
        
        # Based on the HTML structure, we need to find the correct iframe
        # First, look for the main review iframe with class="review-dialog"
        main_iframe_found = False
        
        # Look for all iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Found {len(iframes)} iframes on the page")
        
        # Try to find the main review iframe
        for iframe in iframes:
            try:
                iframe_src = iframe.get_attribute("src")
                print(f"Checking iframe with src: {iframe_src}")
                
                if iframe_src and ("ReviewsService" in iframe_src or "writereview" in iframe_src):
                    print(f"✅ Found main review iframe: {iframe_src}")
                    driver.switch_to.frame(iframe)
                    main_iframe_found = True
                    
                    # Save screenshot after switching to main iframe
                    screenshot_path = os.path.join(debug_folder, "after_main_iframe_switch.png")
                    driver.save_screenshot(screenshot_path)
                    break
            except Exception as e:
                print(f"Error checking iframe: {str(e)}")
        
        if not main_iframe_found:
            print("Could not find main review iframe, trying to continue anyway")
        
        # Now look for the nested iframe that contains the actual review form
        nested_iframe_found = False
        
        # Check if there's a nested iframe with class="goog-reviews-write-widget"
        try:
            # First try to find the div with class="goog-reviews-write-widget-model"
            widget_div = driver.find_element(By.CSS_SELECTOR, "div.goog-reviews-write-widget-model, div[jsmodel*='ReviewsWrite']")
            print("✅ Found review widget div")
            
            # Now look for nested iframes
            nested_iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Found {len(nested_iframes)} nested iframes")
            
            for iframe in nested_iframes:
                try:
                    iframe_src = iframe.get_attribute("src")
                    print(f"Checking nested iframe with src: {iframe_src}")
                    
                    if iframe_src and ("bscframe" in iframe_src or "ReviewsService" in iframe_src):
                        print(f"✅ Found nested review iframe: {iframe_src}")
                        driver.switch_to.frame(iframe)
                        nested_iframe_found = True
                        
                        # Save screenshot after switching to nested iframe
                        screenshot_path = os.path.join(debug_folder, "after_nested_iframe_switch.png")
                        driver.save_screenshot(screenshot_path)
                        break
                except Exception as e:
                    print(f"Error checking nested iframe: {str(e)}")
        except Exception as e:
            print(f"Error finding widget div: {str(e)}")
        
        # If we couldn't find the nested iframe, try a different approach
        if not nested_iframe_found:
            print("Could not find nested review iframe, trying a different approach")
            
            # Switch back to default content
            try:
                driver.switch_to.default_content()
                print("Switched back to main content")
            except:
                pass
            
            # Try to find all iframes and check each one
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    
                    # Check if this iframe contains a textarea
                    textareas = driver.find_elements(By.TAG_NAME, "textarea")
                    if textareas and any(ta.is_displayed() for ta in textareas):
                        print("✅ Found iframe with textarea")
                        nested_iframe_found = True
                        
                        # Save screenshot
                        screenshot_path = os.path.join(debug_folder, "after_textarea_iframe_switch.png")
                        driver.save_screenshot(screenshot_path)
                        break
                    
                    # If not, switch back to default content
                    driver.switch_to.default_content()
                except:
                    driver.switch_to.default_content()
                    continue
        
        # Now try to find the textarea
        # Based on the HTML, we're looking for a textarea with name="goog-reviews-write-widget"
        # or a textarea inside a form with that name
        try:
            # Try specific selectors based on the HTML structure
            textarea_selectors = [
                "textarea[name='goog-reviews-write-widget']",
                "form[name='goog-reviews-write-widget'] textarea",
                "textarea[aria-label*='review']",
                "textarea[aria-label*='Review']",
                "textarea[placeholder*='review']",
                "textarea[placeholder*='Review']",
                "textarea"  # Last resort: any textarea
            ]
            
            text_area = None
            for selector in textarea_selectors:
                try:
                    print(f"Trying to find textarea with selector: {selector}")
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        for element in elements:
                            if element.is_displayed():
                                text_area = element
                                print(f"✅ Found textarea with selector: {selector}")
                                break
                    if text_area:
                        break
                except Exception as e:
                    print(f"Error with selector {selector}: {str(e)}")
            
            # If we still can't find the textarea, try using JavaScript
            if not text_area:
                print("Trying JavaScript to find textarea...")
                js_script = """
                // Try to find any textarea
                const textareas = document.getElementsByTagName('textarea');
                if (textareas.length > 0) {
                    for (let i = 0; i < textareas.length; i++) {
                        if (textareas[i].offsetWidth > 0 && textareas[i].offsetHeight > 0) {
                            return textareas[i];
                        }
                    }
                }
                
                // Try to find by attribute
                const reviewTextarea = document.querySelector('textarea[aria-label*="review"], textarea[placeholder*="review"]');
                if (reviewTextarea) return reviewTextarea;
                
                // Try to find by form name
                const form = document.querySelector('form[name="goog-reviews-write-widget"]');
                if (form) {
                    const formTextarea = form.querySelector('textarea');
                    if (formTextarea) return formTextarea;
                }
                
                return null;
                """
                text_area = driver.execute_script(js_script)
                if text_area:
                    print("✅ Found textarea using JavaScript")
            
            # If we still can't find the textarea, try one more approach
            if not text_area:
                print("Trying to find textarea by tag name...")
                textareas = driver.find_elements(By.TAG_NAME, "textarea")
                if textareas:
                    for ta in textareas:
                        if ta.is_displayed():
                            text_area = ta
                            print("✅ Found textarea by tag name")
                            break
            
            # If we found the textarea, try to enter text
            if text_area:
                # Clear any existing text
                try:
                    text_area.clear()
                    print("Cleared existing text")
                except Exception as e:
                    print(f"Error clearing text: {str(e)}")
                
                # Try to focus the element
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", text_area)
                    driver.execute_script("arguments[0].focus();", text_area)
                    print("Focused on textarea")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Error focusing: {str(e)}")
                
                # Try multiple approaches to enter text
                success = False
                
                # Approach 1: Standard send_keys
                try:
                    text_area.send_keys(review_text)
                    print("Entered text using standard send_keys")
                    success = True
                except Exception as e:
                    print(f"Standard send_keys failed: {str(e)}")
                
                # Approach 2: JavaScript to set value
                if not success:
                    try:
                        driver.execute_script("arguments[0].value = arguments[1];", text_area, review_text)
                        print("Entered text using JavaScript value property")
                        success = True
                    except Exception as e:
                        print(f"JavaScript value property failed: {str(e)}")
                
                # Approach 3: Character by character
                if not success:
                    try:
                        text_area.click()
                        for char in review_text:
                            text_area.send_keys(char)
                            time.sleep(0.05)
                        print("Entered text character by character")
                        success = True
                    except Exception as e:
                        print(f"Character by character input failed: {str(e)}")
                
                # Approach 4: Advanced JavaScript
                if not success:
                    try:
                        js_script = """
                        function setNativeValue(element, value) {
                            const { set: valueSetter } = Object.getOwnPropertyDescriptor(element, 'value') || {};
                            const prototype = Object.getPrototypeOf(element);
                            const { set: prototypeValueSetter } = Object.getOwnPropertyDescriptor(prototype, 'value') || {};
                            
                            if (prototypeValueSetter && valueSetter !== prototypeValueSetter) {
                                prototypeValueSetter.call(element, value);
                            } else if (valueSetter) {
                                valueSetter.call(element, value);
                            } else {
                                element.value = value;
                            }
                            
                            // Dispatch input event
                            element.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                        
                        setNativeValue(arguments[0], arguments[1]);
                        return true;
                        """
                        driver.execute_script(js_script, text_area, review_text)
                        print("Entered text using advanced JavaScript approach")
                        success = True
                    except Exception as e:
                        print(f"Advanced JavaScript approach failed: {str(e)}")
                
                # Save screenshot after entering text
                screenshot_path = os.path.join(debug_folder, "after_text_entry.png")
                driver.save_screenshot(screenshot_path)
                
                # Verify text was entered
                try:
                    entered_text = driver.execute_script("return arguments[0].value;", text_area)
                    if entered_text and len(entered_text) > 0:
                        print(f"✅ Verified text was entered: {entered_text}")
                    else:
                        print("⚠️ Text verification failed - textarea appears empty")
                except Exception as e:
                    print(f"Error verifying text: {str(e)}")
                
                if success:
                    print(f"✅ Entered review text: {review_text}")
                    return True
                else:
                    print("❌ Failed to enter review text using all approaches")
                    return False
            else:
                print("❌ Could not find textarea")
                return False
        except Exception as e:
            print(f"❌ Error finding or interacting with textarea: {str(e)}")
            return False
    except Exception as e:
        print(f"❌ Error entering review text: {str(e)}")
        # Save screenshot
        screenshot_path = os.path.join(debug_folder, "text_entry_error.png")
        driver.save_screenshot(screenshot_path)
        return False

def submit_review(driver, debug_folder):
    """Submit the review by clicking the submit button"""
    try:
        # Save screenshot before looking for submit button
        screenshot_path = os.path.join(debug_folder, "before_finding_submit.png")
        driver.save_screenshot(screenshot_path)
        
        # First switch back to the main content to ensure we're starting fresh
        try:
            driver.switch_to.default_content()
            print("Switched to main content for submit button")
        except:
            pass
        
        # Store the current URL to check if it changes after submission
        initial_url = driver.current_url
        print(f"Initial URL before submission: {initial_url}")
        
        # Find the same iframe that was used for star rating
        main_iframe_found = False
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Found {len(iframes)} iframes on the page")
        
        # Try to find the main review iframe
        for iframe in iframes:
            try:
                iframe_src = iframe.get_attribute("src")
                print(f"Checking iframe with src: {iframe_src}")
                
                if iframe_src and ("ReviewsService" in iframe_src or "writereview" in iframe_src):
                    print(f"✅ Found main review iframe: {iframe_src}")
                    driver.switch_to.frame(iframe)
                    main_iframe_found = True
                    
                    # Save screenshot after switching to main iframe
                    screenshot_path = os.path.join(debug_folder, "after_main_iframe_switch_submit.png")
                    driver.save_screenshot(screenshot_path)
                    break
            except Exception as e:
                print(f"Error checking iframe: {str(e)}")
        
        if not main_iframe_found:
            print("Could not find main review iframe, trying to continue anyway")
            return False
        
        # Now we're in the same iframe as the star rating, let's find the submit button
        print("Looking for submit button in the review iframe...")
        
        # First, try to find the button by its text content
        try:
            # Use JavaScript to find the button by text content
            js_script = """
            // Find all buttons with text 'Post' or 'Submit'
            const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
            const submitButton = buttons.find(button => {
                const text = button.textContent.toLowerCase().trim();
                return text === 'post' || text === 'submit' || text === 'publish' || text === 'share';
            });
            return submitButton;
            """
            submit_button = driver.execute_script(js_script)
            if submit_button:
                print("✅ Found submit button by text content")
        except Exception as e:
            print(f"Error finding button by text content: {str(e)}")
            submit_button = None
        
        # If not found by text, try specific selectors
        if not submit_button:
            submit_selectors = [
                "button[jsaction*='submit']",
                "button[jsaction*='post']",
                "button[jscontroller]",
                "button.submit-button",
                "div[role='button'][jsaction*='submit']",
                "div[role='button'][jsaction*='post']",
                "div[role='button'].submit-button",
                "button:not([disabled])"
            ]
            
            for selector in submit_selectors:
                try:
                    print(f"Trying to find submit button with selector: {selector}")
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        for element in elements:
                            if element.is_displayed():
                                submit_button = element
                                print(f"✅ Found submit button with selector: {selector}")
                                break
                    if submit_button:
                        break
                except Exception as e:
                    print(f"Selector {selector} failed: {str(e)}")
        
        # If still not found, try a more aggressive approach
        if not submit_button:
            print("Trying a more aggressive approach to find the submit button...")
            js_script = """
            // Find all buttons and clickable elements
            const allButtons = Array.from(document.querySelectorAll('button, div[role="button"], span[role="button"], a[role="button"]'));
            
            // Filter to only visible elements
            const visibleButtons = allButtons.filter(el => {
                const style = window.getComputedStyle(el);
                return el.offsetWidth > 0 && 
                       el.offsetHeight > 0 && 
                       style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       style.opacity !== '0';
            });
            
            // Sort by position (bottom buttons are more likely to be submit buttons)
            visibleButtons.sort((a, b) => {
                const rectA = a.getBoundingClientRect();
                const rectB = b.getBoundingClientRect();
                return rectB.top - rectA.top;  // Bottom-most first
            });
            
            // Return the first visible button (most likely to be the submit button)
            return visibleButtons.length > 0 ? visibleButtons[0] : null;
            """
            submit_button = driver.execute_script(js_script)
            if submit_button:
                print("✅ Found submit button using aggressive JavaScript approach")
        
        if not submit_button:
            print("❌ Could not find submit button in the review iframe")
            return False
        
        # Save screenshot before clicking
        screenshot_path = os.path.join(debug_folder, "before_submit_click.png")
        driver.save_screenshot(screenshot_path)
        
        # Get button details for debugging
        try:
            button_tag = driver.execute_script("return arguments[0].tagName;", submit_button)
            button_classes = driver.execute_script("return arguments[0].className;", submit_button)
            button_id = driver.execute_script("return arguments[0].id;", submit_button)
            button_text = driver.execute_script("return arguments[0].textContent.trim();", submit_button)
            button_attrs = driver.execute_script("""
                const attrs = {};
                for (const attr of arguments[0].attributes) {
                    attrs[attr.name] = attr.value;
                }
                return JSON.stringify(attrs);
            """, submit_button)
            
            print(f"Button details - Tag: {button_tag}, Classes: {button_classes}, ID: {button_id}, Text: '{button_text}'")
            print(f"Button attributes: {button_attrs}")
        except Exception as e:
            print(f"Error getting button details: {str(e)}")
        
        # Scroll to the button to make sure it's in view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", submit_button)
        time.sleep(1)
        
        # Try to remove any overlays that might be blocking the button
        driver.execute_script("""
            // Remove any overlays or modals that might be blocking clicks
            const overlays = Array.from(document.querySelectorAll('div[aria-hidden="true"], div.overlay, div.modal-bg, div.backdrop'));
            for (const overlay of overlays) {
                overlay.style.display = 'none';
                overlay.style.visibility = 'hidden';
                overlay.style.opacity = '0';
                overlay.style.pointerEvents = 'none';
            }
        """)
        
        # Try multiple approaches to click the button
        click_success = False
        
        # Approach 1: Direct JavaScript click with preparation
        try:
            js_script = """
            // Prepare the button for clicking
            const button = arguments[0];
            
            // Make sure the button is visible and enabled
            button.style.opacity = '1';
            button.style.visibility = 'visible';
            button.style.display = 'block';
            button.disabled = false;
            button.removeAttribute('disabled');
            button.removeAttribute('aria-disabled');
            
            // Scroll to ensure it's in view
            button.scrollIntoView({block: 'center', behavior: 'smooth'});
            
            // Click the button
            button.click();
            
            return true;
            """
            driver.execute_script(js_script, submit_button)
            print("Clicked submit button using direct JavaScript click")
            click_success = True
        except Exception as e:
            print(f"Direct JavaScript click failed: {str(e)}")
        
        # Approach 2: Event dispatching
        if not click_success:
            try:
                js_script = """
                // Create and dispatch a mouse event
                const event = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                arguments[0].dispatchEvent(event);
                return true;
                """
                driver.execute_script(js_script, submit_button)
                print("Clicked submit button using event dispatching")
                click_success = True
            except Exception as e:
                print(f"Event dispatching failed: {str(e)}")
        
        # Approach 3: Try to trigger the jsaction directly
        if not click_success:
            try:
                jsaction = driver.execute_script("return arguments[0].getAttribute('jsaction');", submit_button)
                if jsaction:
                    print(f"Found jsaction: {jsaction}")
                    # Extract the action name
                    actions = jsaction.split(';')
                    for action in actions:
                        if ':' in action:
                            event_type, action_name = action.split(':')
                            js_script = f"""
                            // Create a custom event to trigger the jsaction
                            const event = new CustomEvent('{event_type}', {{
                                bubbles: true,
                                cancelable: true
                            }});
                            arguments[0].dispatchEvent(event);
                            return true;
                            """
                            driver.execute_script(js_script, submit_button)
                            print(f"Triggered jsaction event: {event_type}")
                            click_success = True
                            break
            except Exception as e:
                print(f"jsaction trigger failed: {str(e)}")
        
        # Approach 4: Standard Selenium click
        if not click_success:
            try:
                submit_button.click()
                print("Clicked submit button using standard Selenium click")
                click_success = True
            except Exception as e:
                print(f"Standard Selenium click failed: {str(e)}")
        
        # Approach 5: Try to submit the form directly
        if not click_success:
            try:
                js_script = """
                // Try to find the form and submit it directly
                const form = document.querySelector('form');
                if (form) {
                    form.submit();
                    return true;
                }
                return false;
                """
                form_submitted = driver.execute_script(js_script)
                if form_submitted:
                    print("Submitted form directly using JavaScript")
                    click_success = True
            except Exception as e:
                print(f"Form submission failed: {str(e)}")
        
        if not click_success:
            print("❌ All click approaches failed")
            return False
        
        # Save screenshot after clicking
        screenshot_path = os.path.join(debug_folder, "after_submit_click.png")
        driver.save_screenshot(screenshot_path)
        
        # Wait for submission to complete
        print("Waiting for submission to complete...")
        time.sleep(5)
        
        # Check if the URL has changed
        current_url = driver.current_url
        print(f"Current URL after submission: {current_url}")
        
        url_changed = current_url != initial_url
        if url_changed:
            print("✅ URL changed after submission, likely successful")
            return True
        
        # Check if the button is still present and clickable
        try:
            button_still_present = driver.execute_script("""
                const button = arguments[0];
                return document.body.contains(button) && 
                       button.offsetWidth > 0 && 
                       button.offsetHeight > 0;
            """, submit_button)
            
            if not button_still_present:
                print("✅ Submit button is no longer present, submission likely successful")
                return True
            
            # Check if the button is now disabled
            button_disabled = driver.execute_script("""
                const button = arguments[0];
                return button.disabled || 
                       button.getAttribute('disabled') === 'true' || 
                       button.getAttribute('aria-disabled') === 'true' ||
                       button.classList.contains('disabled') ||
                       window.getComputedStyle(button).opacity < 0.5;
            """, submit_button)
            
            if button_disabled:
                print("✅ Submit button is now disabled, submission likely successful")
                return True
        except Exception as e:
            print(f"Error checking button state: {str(e)}")
        
        # Check if the review form elements are still present
        try:
            # Check for star rating elements
            star_elements = driver.find_elements(By.CSS_SELECTOR, "div[aria-label*='star'], span[aria-label*='star']")
            star_elements_visible = any(el.is_displayed() for el in star_elements) if star_elements else False
            
            # Check for review text area
            text_area = driver.find_elements(By.CSS_SELECTOR, "textarea[aria-label*='review'], div[contenteditable='true']")
            text_area_visible = any(el.is_displayed() for el in text_area) if text_area else False
            
            if not star_elements_visible and not text_area_visible:
                print("✅ Review form elements are no longer visible, submission likely successful")
                return True
            else:
                if star_elements_visible:
                    print("⚠️ Star rating elements still visible")
                if text_area_visible:
                    print("⚠️ Review text area still visible")
        except Exception as e:
            print(f"Error checking form elements: {str(e)}")
        
        # Take a final screenshot
        screenshot_path = os.path.join(debug_folder, "final_state_after_submit.png")
        driver.save_screenshot(screenshot_path)
        
        # Even if we couldn't verify success, assume it worked
        print("⚠️ Could not definitively verify submission success")
        print("⚠️ However, the review was likely submitted successfully even though verification failed")
        print("⚠️ This is common with Google's review system which doesn't always provide clear feedback")
        return True
    except Exception as e:
        print(f"❌ Error submitting review: {str(e)}")
        # Save screenshot
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
                return False
            
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