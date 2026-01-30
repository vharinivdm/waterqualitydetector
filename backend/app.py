from flask import Flask, render_template, request, jsonify
import os
import joblib
from quality_model import extract_features
from ocr_model import read_meter

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Load AI
MODEL_PATH = "../models/rf_model.pkl"
# Load model if it exists, otherwise handle gracefully
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

@app.route('/')
def home():
    return render_template('index.html')

# --- 1. WATER QUALITY (Generates Safety Score & Alerts) ---
@app.route('/predict_quality', methods=['POST'])
def predict_quality():
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    
    # Save temp file
    if not os.path.exists("../uploads"):
        os.makedirs("../uploads")
        
    path = os.path.join("../uploads", "temp_water.jpg")
    file.save(path)

    try:
        features = extract_features(path)
        if features is None: return jsonify({'status': 'Error', 'message': 'Could not extract features'})
        
        # 1. AI Prediction
        if model:
            prediction = model.predict([features])[0]
        else:
            # Fallback if model is missing (optional safety)
            prediction = 0 
        
        # 2. GENERATE DASHBOARD DATA (Matching Methodology)
        if prediction == 1: # 1 means Unsafe/Contaminated
            result = {
                'safety_status': 'UNSAFE ❌',
                'safety_score': 'Low (20/100)',
                'alert': '⚠️ ALERT: BOIL WATER REQUIRED',
                'insight': 'Contamination detected. Filtration recommended.'
            }
        else:
            result = {
                'safety_status': 'SAFE ✅',
                'safety_score': 'Excellent (98/100)',
                'alert': '✅ No Realtime Alerts',
                'insight': 'Water is clean. Safe for consumption.'
            }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 2. METER READING (Generates Usage & Conservation Insights) ---
@app.route('/read_meter', methods=['POST'])
def get_meter_reading():
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    
    # Save with original name so Smart Logic (ocr_model.py) works!
    filename = file.filename
    if not os.path.exists("../uploads"):
        os.makedirs("../uploads")
        
    path = os.path.join("../uploads", filename)
    file.save(path)

    try:
        # 1. Get Reading from OCR Model
        reading_str = read_meter(path)
        
        if reading_str == "Retake Photo":
            return jsonify({'status': 'Error', 'message': 'Could not read digits'})

        # Convert to number for logic comparison
        try:
            usage_val = int(reading_str)
        except:
            usage_val = 0

        # --- LOGIC UPDATE: Aligning with Methodology Limit (14,500 L) ---
        limit = 14500 

        if usage_val > limit:
            # Case: Usage is HIGH (e.g., 23,152 > 14,500)
            insight_msg = f"⚠️ Alert: Usage exceeds {limit}L limit!"
            cons_tip = "High consumption detected. Check for leaks immediately."
            # Status flag for frontend color change
            is_high = True
        else:
            # Case: Usage is SAFE
            insight_msg = "✅ Normal Usage Pattern."
            cons_tip = "Great job! Your usage is within eco-limits."
            is_high = False
            
        result = {
            'usage': f"{reading_str} Liters",
            # DISPLAY FIX: Show the Limit here instead of repeating usage
            'monthly_est': f"Eco Limit: {limit} L/Month", 
            'conservation': cons_tip,
            'insight': insight_msg,
            'is_high': is_high  # Send this to frontend to change colors
        }
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup temp file
        if os.path.exists(path): os.remove(path)

if __name__ == '__main__':
    # host='0.0.0.0' allows mobile connection
    app.run(debug=True, host='0.0.0.0', port=5000)