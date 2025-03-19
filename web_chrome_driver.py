#!/usr/bin/env python3
"""
Web-compatible Chrome driver for Google Reviews Generator

This module provides a web-compatible version of the Chrome driver initialization function.
It's designed to work in a web application context where the driver needs to be more configurable
and less dependent on local user profiles.
"""

import os
import sys
import time
import shutil
import logging
import tempfile
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
from web_driver_installer import ensure_chromedriver_installed, get_chromedriver_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_chrome_driver.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("WebChromeDriver")

def initialize_web_chrome_driver(chrome_profile_path=None, headless=False, proxy=None):
    """
    Initialize a web-compatible Chrome driver
    
    Args:
        chrome_profile_path (str, optional): Path to Chrome profile directory. Defaults to None.
        headless (bool, optional): Whether to run Chrome in headless mode. Defaults to False.
        proxy (str, optional): Proxy server to use. Defaults to None.
        
    Returns:
        webdriver.Chrome: Initialized Chrome driver
    """
    try:
        logger.info("Initializing web Chrome driver...")
        
        # Ensure ChromeDriver is installed
        driver_path = ensure_chromedriver_installed()
        if not driver_path:
            logger.error("Failed to initialize ChromeDriver: driver not found")
            return None
        
        # Create a temporary directory for the Chrome user data if not provided
        if not chrome_profile_path:
            chrome_profile_path = os.path.join(tempfile.gettempdir(), f"chrome_profile_{int(time.time())}")
        
        # Create the profile directory if it doesn't exist
        os.makedirs(chrome_profile_path, exist_ok=True)
        logger.info(f"Using Chrome profile at: {chrome_profile_path}")
        
        # Try undetected-chromedriver first
        try:
            # Set up options for undetected-chromedriver
            options = uc.ChromeOptions()
            
            # Add user data directory
            options.add_argument(f"--user-data-dir={chrome_profile_path}")
            
            # Add version-specific options to avoid version mismatch
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Set window size and position
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--window-position=0,0")
            
            # Add proxy if specified
            if proxy:
                options.add_argument(f"--proxy-server={proxy}")
            
            # Set headless mode if requested
            if headless:
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
                
                # Additional options for headless mode stability
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-setuid-sandbox")
                options.add_argument("--no-zygote")
                options.add_argument("--single-process")
                options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Set page load strategy to eager to speed up loading
            options.page_load_strategy = 'eager'
            
            # Get Chrome version
            chrome_version = None
            try:
                if platform.system() == "Windows":
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                    chrome_version, _ = winreg.QueryValueEx(key, "version")
                    chrome_version = chrome_version.split(".")[0]  # Only major version
                else:
                    # Assume Linux or macOS
                    cmd = "google-chrome --version" if platform.system() == "Linux" else "/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version"
                    chrome_version = os.popen(cmd).read().strip().split(" ")[-1].split(".")[0]
            except:
                logger.warning("Could not determine Chrome version, using default")
            
            # Try to create the driver with specified Chrome version if available
            if chrome_version:
                driver = uc.Chrome(
                    options=options,
                    driver_executable_path=driver_path,
                    version_main=int(chrome_version)
                )
            else:
                # Let undetected-chromedriver determine the version
                driver = uc.Chrome(
                    options=options,
                    driver_executable_path=driver_path
                )
            
            logger.info("✅ Successfully initialized undetected_chromedriver")
            return driver
        except Exception as e:
            logger.error(f"❌ Error initializing undetected_chromedriver: {str(e)}")
            logger.info("Falling back to standard Chrome driver...")
            
            try:
                # Fallback to standard Chrome driver
                chrome_options = webdriver.ChromeOptions()
                
                # Add standard options
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_argument(f"--user-data-dir={chrome_profile_path}")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                
                # Set window size and position
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--window-position=0,0")
                
                # Add proxy if specified
                if proxy:
                    chrome_options.add_argument(f"--proxy-server={proxy}")
                
                # Set headless mode if requested
                if headless:
                    chrome_options.add_argument("--headless=new")
                    chrome_options.add_argument("--disable-gpu")
                    
                    # Additional options for headless mode stability
                    chrome_options.add_argument("--disable-extensions")
                    chrome_options.add_argument("--disable-setuid-sandbox")
                    chrome_options.add_argument("--no-zygote")
                    chrome_options.add_argument("--single-process")
                    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
                
                # Set page load strategy to eager to speed up loading
                chrome_options.page_load_strategy = 'eager'
                
                # Add experimental options to avoid detection
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option("useAutomationExtension", False)
                
                # Create the service with the ChromeDriver path
                service = Service(driver_path)
                
                # Create the driver
                driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Execute CDP commands to avoid detection
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    """
                })
                
                logger.info("✅ Successfully initialized standard Chrome driver")
                return driver
            except Exception as e2:
                logger.error(f"❌ Error initializing standard Chrome driver: {str(e2)}")
                logger.error("Could not initialize any Chrome driver")
                return None
    except Exception as e:
        logger.error(f"❌ Error in initialize_web_chrome_driver: {str(e)}")
        return None

def clean_up_chrome_profile(chrome_profile_path):
    """
    Clean up a Chrome profile directory
    
    Args:
        chrome_profile_path (str): Path to Chrome profile directory
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if os.path.exists(chrome_profile_path) and os.path.isdir(chrome_profile_path):
            shutil.rmtree(chrome_profile_path)
            logger.info(f"Removed Chrome profile directory: {chrome_profile_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error cleaning up Chrome profile: {str(e)}")
        return False

if __name__ == "__main__":
    # If run directly, test the driver initialization
    chrome_profile_path = os.path.join(tempfile.gettempdir(), f"chrome_profile_test_{int(time.time())}")
    
    print(f"Testing Chrome driver initialization with profile: {chrome_profile_path}")
    driver = initialize_web_chrome_driver(chrome_profile_path)
    
    if driver:
        print("✅ Chrome driver initialized successfully")
        driver.get("https://www.google.com")
        print(f"Current URL: {driver.current_url}")
        time.sleep(3)
        driver.quit()
        
        # Clean up the test profile
        clean_up_chrome_profile(chrome_profile_path)
    else:
        print("❌ Failed to initialize Chrome driver") 