import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import numpy as np
from quality_model import extract_features

# --- CONFIGURATION ---
DATASET_PATH = "../dataset" 
MODEL_PATH = "../models/rf_model.pkl"

def train():
    print("🚀 Starting AI Training...")
    
    data = []
    labels = [] # 0 = Safe/Clean, 1 = Unsafe/Dirty

    # 1. Load CLEAN Images (Label = 0)
    clean_folder = os.path.join(DATASET_PATH, "Clean")
    if not os.path.exists(clean_folder):
        print(f"❌ Error: Folder not found at {clean_folder}")
        return

    print(f"   📂 Loading Clean images from: {clean_folder}")
    clean_count = 0
    for filename in os.listdir(clean_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(clean_folder, filename)
            features = extract_features(filepath)
            if features:
                data.append(features)
                labels.append(0) # 0 means Safe/Clean
                clean_count += 1

    print(f"   ✅ Loaded {clean_count} clean water images")

    # 2. Load DIRTY Images (Label = 1)
    dirty_folder = os.path.join(DATASET_PATH, "Dirty")
    if not os.path.exists(dirty_folder):
        print(f"❌ Error: Folder not found at {dirty_folder}")
        return

    print(f"   📂 Loading Dirty images from: {dirty_folder}")
    dirty_count = 0
    for filename in os.listdir(dirty_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(dirty_folder, filename)
            features = extract_features(filepath)
            if features:
                data.append(features)
                labels.append(1) # 1 means Unsafe/Dirty
                dirty_count += 1

    print(f"   ✅ Loaded {dirty_count} dirty water images")
    print(f"   📊 Total Images: {len(data)} (Clean: {clean_count}, Dirty: {dirty_count})")

    if len(data) < 10:
        print("❌ Not enough images to train! You need at least 10 images total.")
        return

    # 3. Prepare Data for AI
    df = pd.DataFrame(data, columns=['Hue', 'Saturation', 'Value', 'Texture'])
    
    # Print feature statistics
    print("\n   📈 Feature Statistics:")
    print(f"   Clean - Mean: {df[np.array(labels)==0].mean().values}")
    print(f"   Dirty - Mean: {df[np.array(labels)==1].mean().values}")
    
    # Split: 80% for training, 20% for testing
    X_train, X_test, y_train, y_test = train_test_split(
        df, labels, test_size=0.2, random_state=42, stratify=labels
    )

    # 4. Train the Random Forest with better parameters
    print("\n   🧠 Training Random Forest Model...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight='balanced'  # Handle class imbalance
    )
    model.fit(X_train, y_train)

    # 5. Test Accuracy
    if len(X_test) > 0:
        predictions = model.predict(X_test)
        acc = accuracy_score(y_test, predictions)
        print(f"\n   ✅ Test Set Accuracy: {acc * 100:.2f}%")
        
        # Detailed classification report
        print("\n   📊 Classification Report:")
        print(classification_report(y_test, predictions, 
                                   target_names=['Clean', 'Dirty']))
        
        # Feature importance
        print("\n   🎯 Feature Importance:")
        feature_names = ['Hue', 'Saturation', 'Value', 'Texture']
        for name, importance in zip(feature_names, model.feature_importances_):
            print(f"   {name}: {importance:.3f}")
    else:
        print("   ⚠️ Warning: Not enough data to create a test set.")

    # 6. Test on a few samples
    print("\n   🧪 Testing on sample images...")
    
    # Test clean image
    clean_test = os.path.join(clean_folder, os.listdir(clean_folder)[0])
    if clean_test.lower().endswith(('.png', '.jpg', '.jpeg')):
        features = extract_features(clean_test)
        pred = model.predict([features])[0]
        prob = model.predict_proba([features])[0]
        print(f"   Clean sample: Predicted={['SAFE','UNSAFE'][pred]} (confidence: {max(prob)*100:.1f}%)")
    
    # Test dirty image
    dirty_test = os.path.join(dirty_folder, os.listdir(dirty_folder)[0])
    if dirty_test.lower().endswith(('.png', '.jpg', '.jpeg')):
        features = extract_features(dirty_test)
        pred = model.predict([features])[0]
        prob = model.predict_proba([features])[0]
        print(f"   Dirty sample: Predicted={['SAFE','UNSAFE'][pred]} (confidence: {max(prob)*100:.1f}%)")

    # 7. Save the Model
    joblib.dump(model, MODEL_PATH)
    print(f"\n   💾 Model saved successfully to: {MODEL_PATH}")
    print("   ✅ Training Complete!")

if __name__ == "__main__":
    train()
