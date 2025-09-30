#!/usr/bin/env python3
"""Start all services for the Document Translation Web App"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_env_file():
    """Check if root .env file exists"""
    # Check in parent directory (project root)
    env_file = Path("../.env")
    if not env_file.exists():
        print("Error: .env file not found in project root!")
        print("Please create it from .env.example and add your API keys")
        print(f"Expected location: {env_file.resolve()}")
        return False

    # Verify it has required keys
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            if 'GEMINI_API_KEY' not in content:
                print("Warning: GEMINI_API_KEY not found in .env file")
                print("Please add your Gemini API key to the .env file")
                return False
    except Exception as e:
        print(f"Error reading .env file: {e}")
        return False

    return True

def install_dependencies():
    """Install dependencies for all services"""
    services = ["backend", "worker", "frontend"]

    print("Checking dependencies...")
    for service in services:
        print(f"Installing dependencies for {service}...")
        try:
            subprocess.run(
                ["npm", "install"],
                cwd=service,
                shell=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to install dependencies for {service}: {e}")
            return False
    return True

def start_services():
    """Start all services in separate processes"""
    processes = []

    services = [
        ("Backend Server", "backend", "npm start"),
        ("Worker Service", "worker", "npm start"),
        ("Frontend Dev Server", "frontend", "npm run dev")
    ]

    print("\nStarting services...")

    for name, directory, command in services:
        print(f"Starting {name}...")
        try:
            if sys.platform == "win32":
                # Windows: Use CREATE_NEW_CONSOLE flag
                process = subprocess.Popen(
                    command,
                    cwd=directory,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # Unix-like systems
                process = subprocess.Popen(
                    command.split(),
                    cwd=directory
                )
            processes.append((name, process))
            time.sleep(2)  # Give each service time to start
        except Exception as e:
            print(f"Failed to start {name}: {e}")
            # Terminate already started processes
            for _, p in processes:
                p.terminate()
            return None

    return processes

def main():
    """Main function to start all services"""
    # Check environment file
    if not check_env_file():
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        sys.exit(1)

    # Start services
    processes = start_services()

    if not processes:
        sys.exit(1)

    print("\n" + "="*50)
    print("Services started successfully!")
    print("="*50)
    print("\nAccess the application at:")
    print("  - Frontend: http://localhost:3000")
    print("  - Backend API: http://localhost:3001")
    print("\nPress Ctrl+C to stop all services")
    print("="*50 + "\n")

    # Wait for user interrupt
    try:
        # Keep the script running
        while True:
            time.sleep(1)
            # Check if any process has terminated
            for name, process in processes:
                if process.poll() is not None:
                    print(f"\nWarning: {name} has stopped unexpectedly!")
    except KeyboardInterrupt:
        print("\n\nStopping all services...")
        for name, process in processes:
            print(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("All services stopped.")

if __name__ == "__main__":
    main()