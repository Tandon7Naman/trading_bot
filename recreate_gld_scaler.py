#!/usr/bin/env python3
"""
Recreates and saves the scikit-learn scaler object for the GLD model
from the saved NumPy arrays.
"""

import os
import pickle
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def recreate_scaler():
    """
    Loads scaler parameters from .npy files and saves the scaler object.
    """
    model_dir = "models"
    min_path = os.path.join(model_dir, "lstm_gld_scaler_min.npy")
    scale_path = os.path.join(model_dir, "lstm_gld_scaler_scale.npy")
    output_path = os.path.join(model_dir, "gld_scaler.pkl")

    print("=" * 60)
    print("Recreating GLD Scaler Object")
    print("=" * 60)

    if not os.path.exists(min_path) or not os.path.exists(scale_path):
        print(f"✗ ERROR: Scaler parameter files not found in '{model_dir}'.")
        print("Please ensure 'lstm_gld_scaler_min.npy' and 'lstm_gld_scaler_scale.npy' exist.")
        return

    try:
        # Load the parameters
        scaler_min = np.load(min_path)
        scaler_scale = np.load(scale_path)
        print("✓ Loaded scaler parameters from .npy files.")

        # Create a new scaler instance and manually set its learned attributes
        scaler = MinMaxScaler()
        scaler.min_ = scaler_min
        scaler.scale_ = scaler_scale
        # The number of features seen during fit is also required
        scaler.n_features_in_ = scaler_min.shape[0]
        if hasattr(scaler, 'feature_names_in_'):
             scaler.feature_names_in_ = np.array([f'feature_{i}' for i in range(scaler.n_features_in_)], dtype=object)


        # Save the reconstituted scaler object using pickle
        with open(output_path, 'wb') as f:
            pickle.dump(scaler, f)
        
        print(f"✓ Scaler object successfully recreated and saved to:\n  {output_path}")
        print("=" * 60)

    except Exception as e:
        print(f"✗ ERROR: An error occurred during scaler recreation: {e}")
        print("=" * 60)

if __name__ == "__main__":
    recreate_scaler()
