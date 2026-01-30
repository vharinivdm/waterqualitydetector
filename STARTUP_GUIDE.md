# 🚀 Quick Start Guide

## Starting AquaGuard AI

We've provided multiple startup scripts for your convenience. Choose the one that matches your operating system:

---

## Option 1: Bash Script (macOS/Linux) - RECOMMENDED

```bash
./start.sh
```

**Features:**
- ✅ Automatic dependency installation
- ✅ Database initialization
- ✅ Model training (if needed)
- ✅ Shows server URLs
- ✅ Simple one-command startup

---

## Option 2: Python Script (Cross-Platform)

```bash
python3 start.py
```

**Features:**
- ✅ Works on Windows, macOS, and Linux
- ✅ Automatic setup and checks
- ✅ Clean output with status messages
- ✅ Best for Python developers

---

## Option 3: Windows Batch File

```cmd
start.bat
```

**Features:**
- ✅ Native Windows script
- ✅ Double-click to run
- ✅ Automatic dependency check
- ✅ Easy for non-technical users

---

## Option 4: Manual Start

If you prefer to start manually:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database (first time only)
cd backend
python3 database.py

# 3. Train model (first time only)
python3 train_model.py

# 4. Start server
python3 app_enhanced.py
```

---

## What the Startup Scripts Do

1. **Check Python Installation** - Verifies Python 3.7+ is installed
2. **Install Dependencies** - Automatically installs required packages
3. **Initialize Database** - Creates SQLite database with demo user
4. **Train ML Model** - Trains the water quality classifier
5. **Create Directories** - Sets up uploads folder
6. **Start Server** - Launches Flask on port 9000

---

## After Starting

Once the server starts, you'll see:

```
======================================================================
🚀 Starting AquaGuard AI Server...
======================================================================

🌐 Server URLs:
   - Local:   http://localhost:9000
   - Network: http://192.168.1.100:9000

👤 Demo Login Credentials:
   - Username: demo
   - Password: demo123

⚠️  Press CTRL+C to stop the server
======================================================================
```

**Next Steps:**
1. Open your browser
2. Navigate to `http://localhost:9000`
3. Login with demo/demo123
4. Start testing water quality!

---

## Troubleshooting

### "Permission Denied" Error (macOS/Linux)
```bash
chmod +x start.sh
./start.sh
```

### "Python not found" Error
Install Python 3.7+ from https://www.python.org/downloads/

### "Port 9000 already in use"
Kill the existing process:
```bash
# macOS/Linux
lsof -ti:9000 | xargs kill -9

# Windows
netstat -ano | findstr :9000
taskkill /PID <PID> /F
```

### Dependencies Installation Fails
Try manual installation:
```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

---

## First Time Setup

The first time you run any startup script, it will:
- Install all Python packages (~2-3 minutes)
- Create database and demo user (~5 seconds)
- Train ML model on 73 images (~30 seconds)

**Total first-time setup: ~3-4 minutes**

Subsequent starts take only **~2-3 seconds**!

---

## Stopping the Server

Press `CTRL+C` in the terminal where the server is running.

---

## System Requirements

- **Python:** 3.7 or higher
- **RAM:** 2GB minimum
- **Disk Space:** 500MB
- **OS:** Windows 10+, macOS 10.13+, or Linux

---

## Quick Commands Reference

```bash
# Start application
./start.sh              # macOS/Linux
python3 start.py        # All platforms
start.bat              # Windows

# Check if server is running
curl http://localhost:9000

# View logs
tail -f backend/logs/app.log  # If logging is enabled

# Restart server
CTRL+C, then ./start.sh
```

---

## Development Mode

For development with auto-reload:
```bash
cd backend
export FLASK_ENV=development
python3 app_enhanced.py
```

---

## Production Deployment

For production, use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:9000 app_enhanced:app
```

---

## Need Help?

- Check `PROJECT_DOCUMENTATION.md` for detailed documentation
- Review `ENHANCEMENT_SUMMARY.md` for feature overview
- Check the terminal output for error messages

---

**Ready to start? Run `./start.sh` and you're good to go! 🚀**
