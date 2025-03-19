#!/usr/bin/env python3
"""
Web Driver Installer for Google Reviews Generator

This module helps install and configure ChromeDriver for web use.
"""

import os
import sys
import subprocess
import platform
import zipfile
import tarfile
import shutil
import requests
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_driver_installer.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("WebDriverInstaller")

def get_chrome_version():
    """Get the installed Chrome version"""
    system = platform.system()
    
    try:
        if system == "Linux":
            # Linux
            process = subprocess.Popen(
                ["google-chrome", "--version"],
                stdout=subprocess.PIPE
            )
            version = process.communicate()[0].decode("utf-8").strip().split(" ")[-1]
        elif system == "Darwin":
            # macOS
            process = subprocess.Popen(
                ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                stdout=subprocess.PIPE
            )
            version = process.communicate()[0].decode("utf-8").strip().split(" ")[-1]
        elif system == "Windows":
            # Windows
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
            except:
                # Try alternative method
                process = subprocess.Popen(
                    ["reg", "query", "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon", "/v", "version"],
                    stdout=subprocess.PIPE
                )
                output = process.communicate()[0].decode("utf-8").strip()
                version = output.split()[-1]
        else:
            logger.error(f"Unsupported operating system: {system}")
            return None
        
        # Only keep the major version number
        major_version = version.split(".")[0]
        logger.info(f"Detected Chrome version: {version} (using major version: {major_version})")
        
        return major_version
    except Exception as e:
        logger.error(f"Error detecting Chrome version: {str(e)}")
        return None

def download_file(url, output_path):
    """Download a file with progress bar"""
    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f, tqdm(
            desc=os.path.basename(output_path),
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                bar.update(size)
        
        return True
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return False

def extract_zip(zip_path, extract_path):
    """Extract a zip file"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        return True
    except Exception as e:
        logger.error(f"Error extracting zip file: {str(e)}")
        return False

def extract_tar_gz(tar_path, extract_path):
    """Extract a tar.gz file"""
    try:
        with tarfile.open(tar_path, 'r:gz') as tar_ref:
            tar_ref.extractall(extract_path)
        return True
    except Exception as e:
        logger.error(f"Error extracting tar.gz file: {str(e)}")
        return False

def install_chromedriver():
    """Install ChromeDriver"""
    # Get Chrome version
    chrome_version = get_chrome_version()
    if not chrome_version:
        logger.error("Failed to detect Chrome version")
        return False
    
    # Create driver directory
    driver_dir = os.path.join(os.getcwd(), "drivers")
    os.makedirs(driver_dir, exist_ok=True)
    
    # Determine system and architecture
    system = platform.system()
    machine = platform.machine().lower()
    
    # Determine URL and file name based on system and architecture
    if system == "Linux":
        if "arm" in machine or "aarch64" in machine:
            url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version}"
            platform_name = "linux64_arm"
            driver_name = "chromedriver"
        else:
            url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version}"
            platform_name = "linux64"
            driver_name = "chromedriver"
    elif system == "Darwin":  # macOS
        if "arm" in machine or "aarch64" in machine:
            url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version}"
            platform_name = "mac_arm64"
            driver_name = "chromedriver"
        else:
            url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version}"
            platform_name = "mac64"
            driver_name = "chromedriver"
    elif system == "Windows":
        url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version}"
        platform_name = "win32"
        driver_name = "chromedriver.exe"
    else:
        logger.error(f"Unsupported operating system: {system}")
        return False
    
    try:
        # Get the exact version
        response = requests.get(url)
        driver_version = response.text.strip()
        
        # Download ChromeDriver
        download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_{platform_name}.zip"
        download_path = os.path.join(driver_dir, f"chromedriver_{platform_name}.zip")
        
        logger.info(f"Downloading ChromeDriver {driver_version} for Chrome {chrome_version}")
        if not download_file(download_url, download_path):
            logger.error("Failed to download ChromeDriver")
            return False
        
        # Extract ChromeDriver
        logger.info("Extracting ChromeDriver")
        if not extract_zip(download_path, driver_dir):
            logger.error("Failed to extract ChromeDriver")
            return False
        
        # Make ChromeDriver executable on Unix systems
        if system != "Windows":
            driver_path = os.path.join(driver_dir, driver_name)
            os.chmod(driver_path, 0o755)
        
        # Clean up
        os.remove(download_path)
        
        # Save the driver path for future use
        with open(os.path.join(driver_dir, "driver_path.txt"), "w") as f:
            f.write(os.path.join(driver_dir, driver_name))
        
        logger.info(f"ChromeDriver installed successfully at {os.path.join(driver_dir, driver_name)}")
        return True
    except Exception as e:
        logger.error(f"Error installing ChromeDriver: {str(e)}")
        return False

def get_chromedriver_path():
    """Get the installed ChromeDriver path"""
    driver_dir = os.path.join(os.getcwd(), "drivers")
    driver_path_file = os.path.join(driver_dir, "driver_path.txt")
    
    if os.path.exists(driver_path_file):
        with open(driver_path_file, "r") as f:
            driver_path = f.read().strip()
        
        if os.path.exists(driver_path):
            return driver_path
    
    # If path file doesn't exist or path is invalid, try to find driver directly
    if platform.system() == "Windows":
        driver_name = "chromedriver.exe"
    else:
        driver_name = "chromedriver"
    
    driver_path = os.path.join(driver_dir, driver_name)
    if os.path.exists(driver_path):
        return driver_path
    
    # If driver not found, install it
    if install_chromedriver():
        return get_chromedriver_path()
    
    return None

def ensure_chromedriver_installed():
    """Ensure ChromeDriver is installed"""
    driver_path = get_chromedriver_path()
    
    if not driver_path:
        logger.info("ChromeDriver not found. Installing...")
        if install_chromedriver():
            driver_path = get_chromedriver_path()
            logger.info(f"ChromeDriver installed at: {driver_path}")
            return driver_path
        else:
            logger.error("Failed to install ChromeDriver")
            return None
    
    logger.info(f"ChromeDriver already installed at: {driver_path}")
    return driver_path

if __name__ == "__main__":
    # If run directly, ensure ChromeDriver is installed
    driver_path = ensure_chromedriver_installed()
    if driver_path:
        print(f"ChromeDriver is installed at: {driver_path}")
    else:
        print("Failed to install ChromeDriver") 