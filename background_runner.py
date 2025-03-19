#!/usr/bin/env python3
"""
Background task runner for the Google Reviews Generator web application
"""

import os
import sys
import json
import time
import importlib
import threading
import traceback
from datetime import datetime
import multiprocessing

# Ensure the background_tasks directory exists
os.makedirs("background_tasks", exist_ok=True)

def run_function_and_update_status(task_id, module_name, func_name, args):
    """Run a function and update its status in a JSON file"""
    # Initialize task status
    task_status = {
        "task_id": task_id,
        "status": "running",
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "result": None,
        "error": None,
        "progress": 0
    }
    
    # Save initial status
    task_file = os.path.join("background_tasks", f"{task_id}.json")
    with open(task_file, "w") as f:
        json.dump(task_status, f)
    
    try:
        # Import the module
        if module_name:
            module = importlib.import_module(module_name)
        else:
            # Default module names based on function name
            module_name_mappings = {
                "post_review": "simple_review",
                "run_batch_reviews": "chrome_profiles"
            }
            module_name = module_name_mappings.get(func_name)
            if not module_name:
                raise ImportError(f"Could not determine module for function: {func_name}")
            
            module = importlib.import_module(module_name)
        
        # Get the function
        func = getattr(module, func_name)
        
        # Run the function
        result = func(**args)
        
        # Update task status
        task_status["status"] = "completed"
        task_status["end_time"] = datetime.now().isoformat()
        task_status["result"] = str(result)
        task_status["progress"] = 100
    except Exception as e:
        # Update task status with error
        error_info = {
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        
        task_status["status"] = "failed"
        task_status["end_time"] = datetime.now().isoformat()
        task_status["error"] = error_info
    
    # Save final status
    with open(task_file, "w") as f:
        json.dump(task_status, f)
    
    return task_status

def run_process_in_background(task_id, func_name, args, module_name=None):
    """Run a process in the background"""
    # Start a new process for the function
    process = multiprocessing.Process(
        target=run_function_and_update_status,
        args=(task_id, module_name, func_name, args)
    )
    
    process.daemon = True
    process.start()
    
    return {
        "task_id": task_id,
        "status": "started",
        "pid": process.pid
    }

def update_task_progress(task_id, progress, status=None, message=None):
    """Update the progress of a task"""
    task_file = os.path.join("background_tasks", f"{task_id}.json")
    
    if not os.path.exists(task_file):
        return False
    
    try:
        with open(task_file, "r") as f:
            task_status = json.load(f)
        
        task_status["progress"] = progress
        
        if status:
            task_status["status"] = status
        
        if message:
            if "messages" not in task_status:
                task_status["messages"] = []
            
            task_status["messages"].append({
                "time": datetime.now().isoformat(),
                "message": message
            })
        
        with open(task_file, "w") as f:
            json.dump(task_status, f)
        
        return True
    except:
        return False

def get_task_status(task_id):
    """Get the status of a task"""
    task_file = os.path.join("background_tasks", f"{task_id}.json")
    
    if not os.path.exists(task_file):
        return None
    
    try:
        with open(task_file, "r") as f:
            task_status = json.load(f)
        
        return task_status
    except:
        return None

def cleanup_old_tasks(max_age_hours=48):
    """Clean up old task files"""
    task_dir = "background_tasks"
    
    if not os.path.exists(task_dir):
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for filename in os.listdir(task_dir):
        if not filename.endswith(".json"):
            continue
        
        file_path = os.path.join(task_dir, filename)
        
        # Skip if file is too new
        file_age = current_time - os.path.getmtime(file_path)
        if file_age < max_age_seconds:
            continue
        
        try:
            os.remove(file_path)
        except:
            pass

# Run cleanup as a background thread
def start_cleanup_thread():
    """Start a background thread to periodically clean up old task files"""
    def cleanup_thread():
        while True:
            cleanup_old_tasks()
            # Sleep for 1 hour
            time.sleep(3600)
    
    thread = threading.Thread(target=cleanup_thread)
    thread.daemon = True
    thread.start()

# Start the cleanup thread when the module is imported
start_cleanup_thread() 