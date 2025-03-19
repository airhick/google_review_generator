#!/usr/bin/env python3
"""
Web interface for Google Review Generator
"""

import os
import sys
import re
import json
import time
import random
import urllib.parse
import requests
from datetime import datetime
from pathlib import Path
import yaml
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, send_from_directory
from flask_session import Session
from werkzeug.utils import secure_filename
from background_runner import run_process_in_background

# Import core functionality
from simple_review import post_review, initialize_chrome_driver, login_to_google, create_debug_folder
from chrome_profiles import load_config, add_profile, import_accounts_to_profiles, run_batch_reviews

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "my_secret_key_12345")

# Configure server-side session
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_FILE_DIR"] = "flask_sessions"
Session(app)

# Context processor for adding variables to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Create necessary directories
os.makedirs("chrome_profiles", exist_ok=True)
os.makedirs("debug_files", exist_ok=True)
os.makedirs("flask_sessions", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)

# Utility functions
def get_business_url():
    """Get the currently set business URL"""
    if os.path.exists("business_url.txt"):
        with open("business_url.txt", "r") as f:
            return f.read().strip()
    return ""

def get_direct_review_url():
    """Get the currently set direct review URL"""
    if os.path.exists("direct_review_url.txt"):
        with open("direct_review_url.txt", "r") as f:
            return f.read().strip()
    return ""

def extract_place_id_from_url(url):
    """Extract place ID from a Google Maps URL"""
    # First check for standard place_id or placeid parameters
    place_id_patterns = [
        r'place_id=([^&]+)',
        r'placeid=([^&]+)'
    ]
    
    for pattern in place_id_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Check for CID pattern (0x...:0x...)
    cid_pattern = r'(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)'
    match = re.search(cid_pattern, url)
    if match:
        # For CID pattern, the entire match is the place ID
        return match.group(0)
    
    # Check for data patterns
    data_patterns = [
        r'data=!3m1!4b1!4m5!3m4!1s([^!]+)',
        r'data=!3m1!4b1!4m[0-9]+!3m[0-9]+!1s([^!]+)'
    ]
    
    for pattern in data_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Direct extraction from URL path for specific format
    try:
        # Parse the URL
        parsed_url = urllib.parse.urlparse(url)
        
        # Check if it's a Google Maps URL
        if 'google.com/maps' in parsed_url.netloc + parsed_url.path:
            # Look for the CID in the path or query
            path_and_query = parsed_url.path + '?' + parsed_url.query
            cid_match = re.search(r'!1s(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)', path_and_query)
            if cid_match:
                return cid_match.group(1)
    except:
        pass
    
    return None

def get_place_id_from_api(business_url):
    """Get place ID from Google Places API using the business URL"""
    try:
        # Get API key from environment variable
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            return None, "API key not found"
        
        # Extract business name and location from URL
        business_name = None
        location = None
        
        # Try different patterns to extract business name from URL
        patterns = [
            r'place/([^/@]+)/@',  # Standard format: place/BusinessName/@coordinates
            r'place/([^/]+)$',    # Format ending with business name
            r'place/([^/]+)/',    # Format with business name followed by more path
            r'place/([^?]+)',     # Format with query parameters
            r'q=([^&]+)'          # Format with q parameter
        ]
        
        for pattern in patterns:
            match = re.search(pattern, business_url)
            if match:
                business_name = match.group(1)
                business_name = business_name.replace('+', ' ')
                business_name = urllib.parse.unquote(business_name)
                break
        
        # If we still don't have a business name, try to extract it from the URL path
        if not business_name:
            # Parse the URL and extract the last part of the path
            parsed_url = urllib.parse.urlparse(business_url)
            path_parts = parsed_url.path.split('/')
            if len(path_parts) > 2:  # Ensure there's at least one part after /place/
                business_name = path_parts[-1]  # Get the last part of the path
                business_name = business_name.replace('+', ' ')
                business_name = urllib.parse.unquote(business_name)
        
        if not business_name:
            return None, "Could not extract business name from URL"
        
        # Clean up business name - remove any @ and following text
        if '@' in business_name:
            business_name = business_name.split('@')[0]
        
        # Try to extract location from URL
        location_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', business_url)
        if location_match:
            lat = location_match.group(1)
            lng = location_match.group(2)
            location = f"{lat},{lng}"
        
        # Use Google Places API to find the place ID
        # First try with text search
        search_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={urllib.parse.quote(business_name)}&inputtype=textquery&fields=place_id,name,formatted_address&key={api_key}"
        
        # Add location bias if available
        if location:
            search_url += f"&locationbias=circle:5000@{location}"
        
        response = requests.get(search_url)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('candidates'):
            place_id = data['candidates'][0]['place_id']
            place_name = data['candidates'][0].get('name', 'Unknown')
            place_address = data['candidates'][0].get('formatted_address', 'Unknown')
            
            return place_id, f"Found place ID for {place_name}"
        else:
            # If first method fails, try with nearby search
            if location:
                nearby_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius=500&keyword={urllib.parse.quote(business_name)}&key={api_key}"
                
                response = requests.get(nearby_url)
                data = response.json()
                
                if data.get('status') == 'OK' and data.get('results'):
                    place_id = data['results'][0]['place_id']
                    place_name = data['results'][0].get('name', 'Unknown')
                    
                    return place_id, f"Found place ID for {place_name}"
            
            return None, f"API Error: {data.get('status')}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def load_accounts():
    """Load accounts from accounts.yaml"""
    try:
        with open("accounts.yaml", "r") as f:
            data = yaml.safe_load(f)
            if isinstance(data, list):
                return data
            return data or []
    except:
        return []

def save_accounts(accounts):
    """Save accounts to accounts.yaml"""
    try:
        with open("accounts.yaml", "w") as f:
            yaml.dump(accounts, f)
        return True
    except:
        return False

def get_debug_folders():
    """Get a list of debug folders sorted by creation time (newest first)"""
    debug_folder_path = "debug_files"
    if not os.path.exists(debug_folder_path):
        return []
    
    folders = [f for f in os.listdir(debug_folder_path) if os.path.isdir(os.path.join(debug_folder_path, f))]
    return sorted(folders, key=lambda x: os.path.getctime(os.path.join(debug_folder_path, x)), reverse=True)

# Routes
@app.route('/')
def index():
    """Home page"""
    # Get basic information
    business_url = get_business_url()
    direct_review_url = get_direct_review_url()
    
    # Get Chrome profiles
    config = load_config()
    profiles = config.get("profiles", [])
    
    # Get accounts
    accounts = load_accounts()
    
    # Get debug folders
    debug_folders = get_debug_folders()
    
    return render_template(
        'index.html',
        business_url=business_url,
        direct_review_url=direct_review_url,
        profiles=profiles,
        accounts=accounts,
        debug_folders=debug_folders[:10]  # Show only the 10 most recent
    )

@app.route('/set_business_url', methods=['POST'])
def set_business_url():
    """Set the business URL"""
    url = request.form.get('business_url', '').strip()
    
    if not url:
        flash('Business URL cannot be empty', 'danger')
        return redirect(url_for('index'))
    
    # Save the URL to a file
    with open("business_url.txt", "w") as f:
        f.write(url)
    
    flash('Business URL saved successfully', 'success')
    return redirect(url_for('index'))

@app.route('/generate_review_url', methods=['POST'])
def generate_review_url():
    """Generate a direct review URL from a business URL"""
    business_url = request.form.get('business_url', '').strip()
    
    if not business_url:
        # Try to use the saved business URL
        if os.path.exists("business_url.txt"):
            with open("business_url.txt", "r") as f:
                business_url = f.read().strip()
        
        if not business_url:
            flash('Business URL cannot be empty', 'danger')
            return redirect(url_for('index'))
    
    # First try to get place ID using the Google Places API
    place_id, message = get_place_id_from_api(business_url)
    
    # If API fails, fall back to direct extraction
    if not place_id:
        place_id = extract_place_id_from_url(business_url)
    
    # Generate direct review URL if place ID was found
    if place_id:
        direct_url = f"https://search.google.com/local/writereview?placeid={place_id}"
        
        # Save the direct review URL to a file
        with open("direct_review_url.txt", "w") as f:
            f.write(direct_url)
        
        # Also save the business URL for reference
        with open("business_url.txt", "w") as f:
            f.write(business_url)
        
        flash(f'Direct Review URL generated successfully: {direct_url}', 'success')
    else:
        flash('Failed to generate direct review URL. Please try a different URL.', 'danger')
    
    return redirect(url_for('index'))

@app.route('/manage_accounts', methods=['GET', 'POST'])
def manage_accounts():
    """Manage Google accounts"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            if not username or not password:
                flash('Username and password cannot be empty', 'danger')
                return redirect(url_for('manage_accounts'))
            
            accounts = load_accounts()
            
            # Check if account already exists
            for account in accounts:
                if account.get('username') == username:
                    flash(f'Account {username} already exists', 'danger')
                    return redirect(url_for('manage_accounts'))
            
            # Add new account
            accounts.append({
                'username': username,
                'password': password
            })
            
            if save_accounts(accounts):
                flash(f'Account {username} added successfully', 'success')
            else:
                flash('Failed to save account', 'danger')
            
            return redirect(url_for('manage_accounts'))
        
        elif action == 'delete':
            index = request.form.get('index')
            
            try:
                index = int(index)
                accounts = load_accounts()
                
                if 0 <= index < len(accounts):
                    removed_account = accounts.pop(index)
                    
                    if save_accounts(accounts):
                        flash(f'Account {removed_account.get("username")} removed successfully', 'success')
                    else:
                        flash('Failed to save changes', 'danger')
                else:
                    flash('Invalid account index', 'danger')
            except:
                flash('Invalid request', 'danger')
            
            return redirect(url_for('manage_accounts'))
        
        elif action == 'import_to_profiles':
            success = import_accounts_to_profiles()
            
            if success:
                flash('Accounts imported to Chrome profiles successfully', 'success')
            else:
                flash('Failed to import accounts to Chrome profiles', 'danger')
            
            return redirect(url_for('manage_accounts'))
    
    # GET request - display accounts
    accounts = load_accounts()
    return render_template('accounts.html', accounts=accounts)

@app.route('/post_review', methods=['GET', 'POST'])
def post_review_route():
    """Post a review"""
    if request.method == 'POST':
        # Get form data
        rating = request.form.get('rating')
        review_text = request.form.get('review_text', '').strip()
        profile_index = request.form.get('profile')
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                flash('Rating must be between 1 and 5', 'danger')
                return redirect(url_for('post_review_route'))
        except:
            flash('Invalid rating', 'danger')
            return redirect(url_for('post_review_route'))
        
        # If review text is empty, set it to None to generate a random one
        if not review_text:
            review_text = None
        
        # Get profile if specified
        profile = None
        if profile_index:
            try:
                config = load_config()
                profiles = config.get("profiles", [])
                profile_index = int(profile_index)
                
                if 0 <= profile_index < len(profiles):
                    profile = profiles[profile_index]
            except:
                pass
        
        # Create a background process to post the review
        debug_folder = create_debug_folder()
        task_id = f"review_{int(time.time())}"
        
        # Start the review process in the background
        run_process_in_background(
            task_id=task_id,
            func_name='post_review',
            args={
                'profile': profile,
                'rating': rating,
                'review_text': review_text,
                'debug_folder': debug_folder
            }
        )
        
        flash(f'Review posting started in the background. Check the debug folder for progress: {os.path.basename(debug_folder)}', 'info')
        return redirect(url_for('index'))
    
    # GET request - display form
    config = load_config()
    profiles = config.get("profiles", [])
    
    # Check if business URL or direct review URL exists
    has_urls = os.path.exists("business_url.txt") or os.path.exists("direct_review_url.txt")
    
    return render_template('post_review.html', profiles=profiles, has_urls=has_urls)

@app.route('/batch_reviews', methods=['GET', 'POST'])
def batch_reviews():
    """Post batch reviews"""
    if request.method == 'POST':
        # Get form data
        num_reviews = request.form.get('num_reviews')
        rating_strategy = request.form.get('rating_strategy')
        fixed_rating = request.form.get('fixed_rating')
        delay = request.form.get('delay')
        
        try:
            num_reviews = int(num_reviews)
            rating_strategy = int(rating_strategy)
            delay = int(delay)
            
            if num_reviews <= 0:
                flash('Number of reviews must be positive', 'danger')
                return redirect(url_for('batch_reviews'))
            
            if rating_strategy < 1 or rating_strategy > 3:
                rating_strategy = 3  # Default to weighted random
            
            if delay < 0:
                flash('Delay cannot be negative', 'danger')
                return redirect(url_for('batch_reviews'))
        except:
            flash('Invalid input', 'danger')
            return redirect(url_for('batch_reviews'))
        
        # If fixed rating strategy, get the rating
        if rating_strategy == 1:
            try:
                fixed_rating = int(fixed_rating)
                if fixed_rating < 1 or fixed_rating > 5:
                    fixed_rating = 5  # Default to 5 stars
            except:
                fixed_rating = 5  # Default to 5 stars
        else:
            fixed_rating = None
        
        # Create a background process to run the batch reviews
        task_id = f"batch_{int(time.time())}"
        
        # Start the batch review process in the background
        run_process_in_background(
            task_id=task_id,
            func_name='run_batch_reviews',
            args={
                'num_reviews': num_reviews,
                'delay': delay,
                'rating_strategy': rating_strategy,
                'fixed_rating': fixed_rating
            }
        )
        
        flash(f'Batch review posting started in the background. {num_reviews} reviews will be posted.', 'info')
        return redirect(url_for('index'))
    
    # GET request - display form
    config = load_config()
    profiles = config.get("profiles", [])
    
    # Check if business URL or direct review URL exists
    has_urls = os.path.exists("business_url.txt") or os.path.exists("direct_review_url.txt")
    
    # Check if profiles exist
    if not profiles:
        flash('No Chrome profiles found. Please set up profiles first.', 'warning')
    
    return render_template('batch_reviews.html', profiles=profiles, has_urls=has_urls)

@app.route('/debug_logs')
def debug_logs():
    """View debug logs"""
    debug_folders = get_debug_folders()
    return render_template('debug_logs.html', debug_folders=debug_folders)

@app.route('/debug_folder/<folder_name>')
def debug_folder(folder_name):
    """View contents of a debug folder"""
    folder_path = os.path.join("debug_files", secure_filename(folder_name))
    
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        flash('Debug folder not found', 'danger')
        return redirect(url_for('debug_logs'))
    
    # Get files in the folder
    files = sorted(os.listdir(folder_path))
    
    # Prepare file information
    all_files = []
    image_files = []
    text_files = []
    
    for file in files:
        file_path = os.path.join(folder_path, file)
        if not os.path.isfile(file_path):
            continue
            
        # Get file size
        size_bytes = os.path.getsize(file_path)
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        
        file_info = {
            'name': file,
            'size': size_str,
            'path': file_path
        }
        
        all_files.append(file_info)
        
        # Categorize files
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            image_files.append(file_info)
        elif file.lower().endswith(('.txt', '.log', '.html', '.json')):
            # Read content for text files
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                file_info['content'] = content
            except:
                file_info['content'] = 'Error reading file'
            text_files.append(file_info)
    
    return render_template(
        'debug_folder.html',
        folder_name=folder_name,
        files=all_files,
        images=image_files,
        text_files=text_files
    )

@app.route('/debug_file/<folder_name>/<file_name>')
def debug_file(folder_name, file_name):
    """Serve a file from a debug folder"""
    folder_path = os.path.join("debug_files", secure_filename(folder_name))
    file_path = os.path.join(folder_path, secure_filename(file_name))
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return "File not found", 404
    
    # Check if the request wants the file content preview or the actual file
    preview = request.args.get('preview', 'false') == 'true'
    if not preview:
        return send_from_directory(folder_path, secure_filename(file_name))
    
    # Determine file type for preview
    file_type = 'other'
    file_content = None
    
    if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        file_type = 'image'
    elif file_name.lower().endswith(('.txt', '.log', '.html', '.json', '.py', '.js', '.css')):
        file_type = 'text'
        try:
            with open(file_path, 'r') as f:
                file_content = f.read()
        except:
            file_content = 'Error reading file'
    
    return render_template(
        'debug_file.html',
        folder_name=folder_name,
        file_name=file_name,
        file_type=file_type,
        file_content=file_content
    )

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get the status of a background task"""
    task_file = os.path.join('background_tasks', f"{task_id}.json")
    
    if not os.path.exists(task_file):
        return jsonify({'status': 'not_found'})
    
    try:
        with open(task_file, 'r') as f:
            task_data = json.load(f)
        return jsonify(task_data)
    except:
        return jsonify({'status': 'error', 'message': 'Error reading task data'})

# Run the app
if __name__ == "__main__":
    app.run(debug=True, port=5000) 