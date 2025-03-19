#!/usr/bin/env python3
"""
Run Server Script for Google Reviews Generator Web Application

This script runs the Flask web server with configurable host and port options.
"""

import os
import sys
import argparse
from app import app

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run the Google Reviews Generator web server')
    
    parser.add_argument(
        '--host', 
        type=str, 
        default='127.0.0.1', 
        help='Host address to bind the server to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port', 
        type=int, 
        default=5050, 
        help='Port to run the server on (default: 5050)'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='Run the server in debug mode'
    )
    
    return parser.parse_args()

def create_required_directories():
    """Create required directories if they don't exist"""
    directories = [
        "chrome_profiles",
        "debug_files",
        "flask_sessions",
        "static/uploads",
        "background_tasks"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Ensured directory exists: {directory}")

def main():
    """Main function to run the server"""
    args = parse_arguments()
    
    # Create required directories
    create_required_directories()
    
    # Print server information
    print("\n" + "="*60)
    print(f"🚀 Starting Google Reviews Generator Web Server")
    print("="*60)
    print(f"📡 Server URL: http://{args.host}:{args.port}")
    print(f"🐞 Debug mode: {'ON' if args.debug else 'OFF'}")
    print("="*60)
    print(f"📋 Press CTRL+C to stop the server")
    print("="*60 + "\n")
    
    # Run the Flask application
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

if __name__ == "__main__":
    main() 