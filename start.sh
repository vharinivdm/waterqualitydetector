#!/bin/bash

###############################################################################
# AquaGuard AI - Startup Script for macOS/Linux
# This script starts the Flask application server
###############################################################################

echo "======================================================================"
echo "🌊 AquaGuard AI - Smart Water Management System"
echo "======================================================================"
echo ""

# Change to script directory
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

echo "📂 Project Directory: $PROJECT_ROOT"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed!"
    echo "   Please install Python 3.7 or higher and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ Found: $PYTHON_VERSION"
echo ""

# Check if required packages are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Dependencies not found. Installing..."
    echo ""
    pip3 install -r requirements.txt
    echo ""
fi

# Check if database exists, if not initialize it
if [ ! -f "data/aquaguard.db" ]; then
    echo "🗄️  Initializing database..."
    cd backend
    python3 database.py
    cd ..
    echo ""
fi

# Check if model exists, if not train it
if [ ! -f "models/rf_model.pkl" ]; then
    echo "🧠 Training ML model..."
    cd backend
    python3 train_model.py
    cd ..
    echo ""
fi

# Create uploads directory if it doesn't exist
if [ ! -d "uploads" ]; then
    mkdir -p uploads
    echo "📁 Created uploads directory"
fi

echo "======================================================================"
echo "🚀 Starting AquaGuard AI Server..."
echo "======================================================================"
echo ""
echo "🌐 Server URLs:"
echo "   - Local:   http://localhost:9000"
echo "   - Network: http://$(ipconfig getifaddr en0 2>/dev/null || hostname -I | awk '{print $1}'):9000"
echo ""
echo "👤 Demo Login Credentials:"
echo "   - Username: demo"
echo "   - Password: demo123"
echo ""
echo "⚠️  Press CTRL+C to stop the server"
echo "======================================================================"
echo ""

# Start the Flask application
cd backend
python3 app_enhanced.py
