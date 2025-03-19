# Running the Google Reviews Generator Web Application

This guide explains how to run the Google Reviews Generator web application on your local machine.

## Prerequisites

- Python 3.6 or later
- Required Python packages installed (see `requirements.txt`)
- Chrome browser installed

## Installation

1. Ensure all requirements are installed:

```bash
pip install -r requirements.txt
```

2. Make sure you have Chrome installed on your system. The application uses ChromeDriver to automate Chrome.

## Running the Web Server

You can run the web application using the `run_server.py` script:

```bash
python run_server.py
```

This will start the server on `127.0.0.1:5050` by default.

### Command-Line Options

The `run_server.py` script supports several command-line options:

- `--host`: Specify the host address to bind the server to (default: 127.0.0.1)
- `--port`: Specify the port to run the server on (default: 5050)
- `--debug`: Run the server in debug mode (provides detailed error messages and auto-reloads on code changes)

Examples:

```bash
# Run on a specific port
python run_server.py --port 8080

# Run on all network interfaces (accessible from other devices on the network)
python run_server.py --host 0.0.0.0

# Run in debug mode
python run_server.py --debug
```

## Accessing the Web Application

Once the server is running, you can access the web application by opening a web browser and navigating to:

- http://127.0.0.1:5050 (or the host/port you specified)

## Stopping the Server

To stop the server, press `Ctrl+C` in the terminal where the server is running.

## Troubleshooting

If you encounter any issues:

1. Check that all required Python packages are installed
2. Ensure Chrome is properly installed on your system
3. Check the console output for any error messages
4. Look in the `debug_files` directory for detailed logs