import joblib
import os
import numpy as np
from sklearn.preprocessing import StandardScaler

# 1. Ensure directory exists
os.makedirs("models", exist_ok=True)

# 2. Create a 4-Feature Scaler (Matching: open, high, low, close)
# The test feeds exactly 4 columns, so the scaler must be fit on 4 columns.
dummy_data = np.random.rand(100, 4) 
scaler = StandardScaler()
scaler.fit(dummy_data)

# 3. Save the artifact
joblib.dump(scaler, "models/scaler.save")
print("✅ FIXED: models/scaler.save now expects 4 features.")
