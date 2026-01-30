from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import os
import joblib
from quality_model import extract_features
from ocr_model import read_meter
from database import (
    init_db, create_user, verify_user, save_quality_reading, 
    save_meter_reading, get_user_statistics, get_recent_readings,
    get_unread_alerts, mark_alert_read, get_db
)
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
import json

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = 'aquaguard_secret_key_2026_final_year_project'  # Change in production

# Load AI Model
MODEL_PATH = "../models/rf_model.pkl"
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

# Initialize database on startup
init_db()

# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        
        user_id = create_user(username, email, password, full_name)
        if user_id:
            return jsonify({'success': True, 'message': 'Registration successful'})
        else:
            return jsonify({'success': False, 'message': 'Username or email already exists'}), 400
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ============================================
# DASHBOARD & MAIN PAGES
# ============================================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    stats = get_user_statistics(session['user_id'])
    alerts = get_unread_alerts(session['user_id'])
    
    return render_template('dashboard.html', 
                         user=session, 
                         stats=stats, 
                         alerts=alerts)

@app.route('/quality')
def quality_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('quality.html', user=session)

@app.route('/meter')
def meter_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('meter.html', user=session)

@app.route('/history')
def history_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    quality_history = get_recent_readings(session['user_id'], limit=50, reading_type='quality')
    meter_history = get_recent_readings(session['user_id'], limit=50, reading_type='meter')
    
    return render_template('history.html', 
                         user=session,
                         quality_history=quality_history,
                         meter_history=meter_history)

@app.route('/analytics')
def analytics_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('analytics.html', user=session)

@app.route('/settings')
def settings_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM settings WHERE user_id = ?', (session['user_id'],))
    result = cursor.fetchone()
    settings = dict(result) if result else None
    conn.close()
    
    # Get user statistics for settings page
    stats = get_user_statistics(session['user_id'])
    
    return render_template('settings.html', user=session, settings=settings, stats=stats)

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/api/predict_quality', methods=['POST'])
def predict_quality():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    location = request.form.get('location', '')
    notes = request.form.get('notes', '')
    
    # Save temp file
    if not os.path.exists("../uploads"):
        os.makedirs("../uploads")
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"quality_{session['user_id']}_{timestamp}.jpg"
    path = os.path.join("../uploads", filename)
    file.save(path)

    try:
        features = extract_features(path)
        if features is None:
            return jsonify({'status': 'Error', 'message': 'Could not extract features'})
        
        # AI Prediction
        if model:
            prediction = model.predict([features])[0]
            probabilities = model.predict_proba([features])[0]
            confidence = max(probabilities) * 100
        else:
            prediction = 0 
            confidence = 50
        
        # Generate results (1 = Dirty/Unsafe, 0 = Clean/Safe)
        if prediction == 1:
            # UNSAFE water
            safety_status = 'UNSAFE'
            # Score is inverse of confidence (lower score = more unsafe)
            safety_score = int(100 - confidence)
            alert_level = 'HIGH'
            alert_msg = '⚠️ ALERT: BOIL WATER REQUIRED'
            insight = f'Contamination detected ({confidence:.1f}% confidence). Filtration and boiling recommended before consumption.'
        else:
            # SAFE water
            safety_status = 'SAFE'
            # Score is based on confidence (higher confidence = higher score)
            safety_score = int(confidence)
            alert_level = 'NONE'
            alert_msg = '✅ No Realtime Alerts'
            insight = f'Water quality is good ({confidence:.1f}% confidence). Safe for consumption.'
        
        # Save to database
        reading_id = save_quality_reading(
            session['user_id'], 
            safety_status, 
            safety_score, 
            features, 
            alert_level,
            filename,
            location,
            notes
        )
        
        result = {
            'reading_id': reading_id,
            'safety_status': safety_status,
            'safety_score': f'{safety_score}/100',
            'alert': alert_msg,
            'insight': insight,
            'confidence': f'{confidence:.1f}%',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/read_meter', methods=['POST'])
def api_read_meter():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    location = request.form.get('location', '')
    meter_id = request.form.get('meter_id', '')
    
    # Save with timestamp
    if not os.path.exists("../uploads"):
        os.makedirs("../uploads")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"meter_{session['user_id']}_{timestamp}_{file.filename}"
    path = os.path.join("../uploads", filename)
    file.save(path)

    try:
        # Get Reading from OCR Model
        reading_str = read_meter(path)
        
        if reading_str == "Retake Photo":
            return jsonify({'status': 'Error', 'message': 'Could not read digits'})

        try:
            usage_val = int(reading_str)
        except:
            usage_val = 0

        # Get user's eco limit from settings
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT eco_limit FROM settings WHERE user_id = ?', (session['user_id'],))
        result = cursor.fetchone()
        limit = result['eco_limit'] if result else 14500
        conn.close()

        if usage_val > limit:
            insight_msg = f"⚠️ Alert: Usage exceeds {limit}L limit!"
            cons_tip = "High consumption detected. Check for leaks immediately."
            is_high = True
        else:
            insight_msg = "✅ Normal Usage Pattern."
            cons_tip = "Great job! Your usage is within eco-limits."
            is_high = False
        
        # Save to database
        reading_id = save_meter_reading(
            session['user_id'],
            usage_val,
            is_high,
            cons_tip,
            filename,
            meter_id,
            location
        )
        
        result = {
            'reading_id': reading_id,
            'usage': f"{reading_str} Liters",
            'monthly_est': f"Eco Limit: {limit} L/Month", 
            'conservation': cons_tip,
            'insight': insight_msg,
            'is_high': is_high,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup temp file
        if os.path.exists(path):
            os.remove(path)

@app.route('/api/analytics_data')
def analytics_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    days = int(request.args.get('days', 30))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Quality trend data
    cursor.execute('''
        SELECT DATE(timestamp) as date, 
               AVG(safety_score) as avg_score,
               COUNT(*) as count
        FROM quality_readings 
        WHERE user_id = ? AND timestamp >= datetime('now', ?)
        GROUP BY DATE(timestamp)
        ORDER BY date
    ''', (session['user_id'], f'-{days} days'))
    
    quality_trend = [dict(row) for row in cursor.fetchall()]
    
    # Meter trend data
    cursor.execute('''
        SELECT DATE(timestamp) as date,
               AVG(reading_value) as avg_usage,
               COUNT(*) as count
        FROM meter_readings 
        WHERE user_id = ? AND timestamp >= datetime('now', ?)
        GROUP BY DATE(timestamp)
        ORDER BY date
    ''', (session['user_id'], f'-{days} days'))
    
    meter_trend = [dict(row) for row in cursor.fetchall()]
    
    # Safety status distribution
    cursor.execute('''
        SELECT safety_status, COUNT(*) as count
        FROM quality_readings
        WHERE user_id = ?
        GROUP BY safety_status
    ''', (session['user_id'],))
    
    safety_distribution = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'quality_trend': quality_trend,
        'meter_trend': meter_trend,
        'safety_distribution': safety_distribution
    })

@app.route('/api/export_report')
def export_report():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    report_type = request.args.get('type', 'csv')
    
    conn = get_db()
    
    # Get quality readings
    quality_df = pd.read_sql_query('''
        SELECT timestamp, safety_status, safety_score, alert_level, location
        FROM quality_readings
        WHERE user_id = ?
        ORDER BY timestamp DESC
    ''', conn, params=(session['user_id'],))
    
    # Get meter readings
    meter_df = pd.read_sql_query('''
        SELECT timestamp, reading_value, is_high_usage, location
        FROM meter_readings
        WHERE user_id = ?
        ORDER BY timestamp DESC
    ''', conn, params=(session['user_id'],))
    
    conn.close()
    
    if report_type == 'csv':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            quality_df.to_excel(writer, sheet_name='Water Quality', index=False)
            meter_df.to_excel(writer, sheet_name='Meter Readings', index=False)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'aquaguard_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    
    return jsonify({'error': 'Invalid report type'}), 400

@app.route('/api/alerts/mark_read/<int:alert_id>', methods=['POST'])
def api_mark_alert_read(alert_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    mark_alert_read(alert_id)
    return jsonify({'success': True})

@app.route('/api/settings/update', methods=['POST'])
def update_settings():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE settings 
        SET eco_limit = ?, alert_email = ?, alert_push = ?, theme = ?
        WHERE user_id = ?
    ''', (
        data.get('eco_limit'),
        data.get('alert_email'),
        data.get('alert_push'),
        data.get('theme'),
        session['user_id']
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9000)
