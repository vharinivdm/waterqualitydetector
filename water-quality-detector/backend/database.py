import sqlite3
import os
from datetime import datetime
import hashlib

DATABASE_PATH = "../data/aquaguard.db"

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with all required tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Water quality readings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quality_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            safety_status TEXT NOT NULL,
            safety_score INTEGER NOT NULL,
            mean_hue REAL,
            mean_saturation REAL,
            mean_value REAL,
            texture_score REAL,
            alert_level TEXT,
            image_path TEXT,
            location TEXT,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Meter readings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meter_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reading_value INTEGER NOT NULL,
            is_high_usage BOOLEAN,
            monthly_usage INTEGER,
            conservation_tip TEXT,
            image_path TEXT,
            meter_id TEXT,
            location TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            alert_type TEXT NOT NULL,
            alert_message TEXT NOT NULL,
            severity TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            related_reading_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            eco_limit INTEGER DEFAULT 14500,
            alert_email BOOLEAN DEFAULT 1,
            alert_push BOOLEAN DEFAULT 1,
            language TEXT DEFAULT 'en',
            theme TEXT DEFAULT 'dark',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, email, password, full_name):
    """Create a new user"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, full_name))
        
        user_id = cursor.lastrowid
        
        # Create default settings
        cursor.execute('''
            INSERT INTO settings (user_id) VALUES (?)
        ''', (user_id,))
        
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def verify_user(username, password):
    """Verify user credentials"""
    conn = get_db()
    cursor = conn.cursor()
    password_hash = hash_password(password)
    
    cursor.execute('''
        SELECT * FROM users WHERE username = ? AND password_hash = ?
    ''', (username, password_hash))
    
    user = cursor.fetchone()
    
    if user:
        # Update last login
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now(), user['id']))
        conn.commit()
    
    conn.close()
    return dict(user) if user else None

def save_quality_reading(user_id, safety_status, safety_score, features, alert_level, image_path=None, location=None, notes=None):
    """Save water quality reading"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO quality_readings 
        (user_id, safety_status, safety_score, mean_hue, mean_saturation, mean_value, 
         texture_score, alert_level, image_path, location, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, safety_status, safety_score, features[0], features[1], 
          features[2], features[3], alert_level, image_path, location, notes))
    
    reading_id = cursor.lastrowid
    
    # Create alert if unsafe
    if safety_status == "UNSAFE":
        cursor.execute('''
            INSERT INTO alerts (user_id, alert_type, alert_message, severity, related_reading_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 'WATER_QUALITY', 'Unsafe water detected! Boil water before use.', 'HIGH', reading_id))
    
    conn.commit()
    conn.close()
    return reading_id

def save_meter_reading(user_id, reading_value, is_high_usage, conservation_tip, image_path=None, meter_id=None, location=None):
    """Save meter reading"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO meter_readings 
        (user_id, reading_value, is_high_usage, conservation_tip, image_path, meter_id, location)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, reading_value, is_high_usage, conservation_tip, image_path, meter_id, location))
    
    reading_id = cursor.lastrowid
    
    # Create alert if high usage
    if is_high_usage:
        cursor.execute('''
            INSERT INTO alerts (user_id, alert_type, alert_message, severity, related_reading_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 'HIGH_USAGE', f'Usage exceeds eco-limit! Current: {reading_value}L', 'MEDIUM', reading_id))
    
    conn.commit()
    conn.close()
    return reading_id

def get_user_statistics(user_id):
    """Get user statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Quality readings stats
    cursor.execute('''
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN safety_status = 'SAFE' THEN 1 ELSE 0 END) as safe_count,
               SUM(CASE WHEN safety_status = 'UNSAFE' THEN 1 ELSE 0 END) as unsafe_count,
               AVG(safety_score) as avg_score
        FROM quality_readings WHERE user_id = ?
    ''', (user_id,))
    quality_stats = dict(cursor.fetchone())
    
    # Meter readings stats
    cursor.execute('''
        SELECT COUNT(*) as total_readings,
               AVG(reading_value) as avg_usage,
               MAX(reading_value) as max_usage,
               MIN(reading_value) as min_usage
        FROM meter_readings WHERE user_id = ?
    ''', (user_id,))
    meter_stats = dict(cursor.fetchone())
    
    # Recent alerts
    cursor.execute('''
        SELECT COUNT(*) as unread_alerts
        FROM alerts WHERE user_id = ? AND is_read = 0
    ''', (user_id,))
    alert_stats = dict(cursor.fetchone())
    
    conn.close()
    
    return {
        'quality': quality_stats,
        'meter': meter_stats,
        'alerts': alert_stats
    }

def get_recent_readings(user_id, limit=10, reading_type='quality'):
    """Get recent readings for user"""
    conn = get_db()
    cursor = conn.cursor()
    
    if reading_type == 'quality':
        cursor.execute('''
            SELECT * FROM quality_readings 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
    else:
        cursor.execute('''
            SELECT * FROM meter_readings 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
    
    readings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return readings

def get_unread_alerts(user_id):
    """Get unread alerts for user"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM alerts 
        WHERE user_id = ? AND is_read = 0
        ORDER BY timestamp DESC
    ''', (user_id,))
    
    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return alerts

def mark_alert_read(alert_id):
    """Mark alert as read"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE alerts SET is_read = 1 WHERE id = ?', (alert_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Create demo user
    user_id = create_user('demo', 'demo@aquaguard.com', 'demo123', 'Demo User')
    if user_id:
        print(f"✅ Demo user created with ID: {user_id}")
    else:
        print("ℹ️ Demo user already exists")
