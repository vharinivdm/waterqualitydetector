#!/usr/bin/env python3
"""
AquaGuard AI - Cross-Platform Startup Script
This script works on Windows, macOS, and Linux
"""

import os
import sys
import subprocess
import platform
import socket

def print_header():
    """Print the startup header"""
    print("=" * 70)
    print("🌊 AquaGuard AI - Smart Water Management System")
    print("=" * 70)
    print()

def check_python_version():
    """Check if Python version is 3.7 or higher"""
    version = sys.version_info
    print(f"✅ Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Error: Python 3.7 or higher is required!")
        sys.exit(1)
    print()

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def check_dependencies():
    """Check and install dependencies if needed"""
    print("📦 Checking dependencies...")
    
    try:
        import flask
        print("✅ Dependencies are installed")
    except ImportError:
        print("⚠️  Dependencies not found. Installing...")
        print()
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print()
        print("✅ Dependencies installed successfully")
    print()

def initialize_database():
    """Initialize database if it doesn't exist"""
    db_path = os.path.join("data", "aquaguard.db")
    
    if not os.path.exists(db_path):
        print("🗄️  Initializing database...")
        os.chdir("backend")
        subprocess.run([sys.executable, "database.py"])
        os.chdir("..")
        print()
    else:
        print("✅ Database exists")
        print()

def train_model():
    """Train ML model if it doesn't exist"""
    model_path = os.path.join("models", "rf_model.pkl")
    
    if not os.path.exists(model_path):
        print("🧠 Training ML model...")
        os.chdir("backend")
        subprocess.run([sys.executable, "train_model.py"])
        os.chdir("..")
        print()
    else:
        print("✅ ML model exists")
        print()

def create_directories():
    """Create necessary directories"""
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
        print("📁 Created uploads directory")
        print()

def start_server():
    """Start the Flask server"""
    print("=" * 70)
    print("🚀 Starting AquaGuard AI Server...")
    print("=" * 70)
    print()
    
    local_ip = get_local_ip()
    
    print("🌐 Server URLs:")
    print(f"   - Local:   http://localhost:9000")
    print(f"   - Network: http://{local_ip}:9000")
    print()
    print("👤 Demo Login Credentials:")
    print("   - Username: demo")
    print("   - Password: demo123")
    print()
    print("⚠️  Press CTRL+C to stop the server")
    print("=" * 70)
    print()
    
    # Start Flask app
    os.chdir("backend")
    subprocess.run([sys.executable, "app_enhanced.py"])

def main():
    """Main startup routine"""
    # Get project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print_header()
    print(f"📂 Project Directory: {os.getcwd()}")
    print(f"💻 Operating System: {platform.system()} {platform.release()}")
    print()
    
    check_python_version()
    check_dependencies()
    initialize_database()
    train_model()
    create_directories()
    
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n")
        print("=" * 70)
        print("🛑 Server stopped by user")
        print("=" * 70)
        sys.exit(0)

if __name__ == "__main__":
    main()
