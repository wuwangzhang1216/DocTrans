#!/usr/bin/env python3
"""Start all services for the Document Translation Web App"""

import os
import sys
import subprocess
import time
import signal
import atexit
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

def kill_process_tree(pid):
    """Kill a process and all its children"""
    if sys.platform == "win32":
        # Windows: Use taskkill to kill process tree
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        except Exception:
            pass
    else:
        # Unix-like systems: Send SIGTERM to process group
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            pass

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
                # Windows: Don't use CREATE_NEW_CONSOLE, keep in same console
                process = subprocess.Popen(
                    command,
                    cwd=directory,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                # Unix-like systems: Create new process group
                process = subprocess.Popen(
                    command.split(),
                    cwd=directory,
                    start_new_session=True
                )
            processes.append((name, process))
            time.sleep(2)  # Give each service time to start
        except Exception as e:
            print(f"Failed to start {name}: {e}")
            # Terminate already started processes
            for pname, p in processes:
                print(f"Cleaning up {pname}...")
                kill_process_tree(p.pid)
            return None

    return processes

def cleanup_processes(processes):
    """Clean up all running processes"""
    if not processes:
        return

    print("\n\nStopping all services...")
    for name, process in processes:
        if process.poll() is None:  # Process is still running
            print(f"Stopping {name}...")
            kill_process_tree(process.pid)
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # Force kill if still running
                try:
                    process.kill()
                    process.wait(timeout=2)
                except Exception:
                    pass
    print("All services stopped.")

def main():
    """Main function to start all services"""
    processes = []

    def signal_handler(signum, frame):
        """Handle Ctrl+C signal"""
        cleanup_processes(processes)
        sys.exit(0)

    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, signal_handler)

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

    # Register cleanup to run on exit
    atexit.register(cleanup_processes, processes)

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
                    cleanup_processes(processes)
                    sys.exit(1)
    except KeyboardInterrupt:
        cleanup_processes(processes)

if __name__ == "__main__":
    main()