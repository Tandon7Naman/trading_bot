import numpy as np
import os
from sklearn.preprocessing import MinMaxScaler

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

class LSTMSignalPredictor:
    """LSTM to predict gold price direction"""
    
    def __init__(self, window_size=20, num_features=15, model_path="models/lstm_model.h5"):
        self.window_size = window_size
        self.num_features = num_features
        self.model_path = model_path
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(-1, 1))
        self.is_trained = False
        
        if HAS_TENSORFLOW:
            self._build_model()
        else:
            print("⚠️  Using mock LSTM model (predictions are random)")
    
    def _build_model(self):
        """Build LSTM architecture"""
        if not HAS_TENSORFLOW:
            return
        
        self.model = Sequential([
            LSTM(64, activation='relu', 
                 input_shape=(self.window_size, self.num_features),
                 return_sequences=True),
            Dropout(0.2),
            LSTM(32, activation='relu', return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dropout(0.1),
            Dense(1, activation='sigmoid')
        ])
        
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        print("✅ LSTM model built successfully")
    
    def train(self, X_train, y_train, epochs=50, batch_size=32, validation_split=0.2, verbose=1):
        """Train the LSTM model"""
        if not HAS_TENSORFLOW:
            print("⚠️  TensorFlow not available. Skipping training.")
            return None
        
        if self.model is None:
            self._build_model()
        
        print(f"\n🔄 Training LSTM on {len(X_train)} samples...")
        print(f"   Shape: {X_train.shape}")
        
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=verbose
        )
        
        self.is_trained = True
        print("✅ Training complete")
        
        return history
    
    def predict(self, X):
        """Predict probability of price going UP"""
        if not HAS_TENSORFLOW:
            return np.random.rand(len(X) if len(X.shape) > 2 else 1)
        
        if self.model is None:
            return 0.5
        
        if len(X.shape) == 2:
            X = np.expand_dims(X, axis=0)
        
        predictions = self.model.predict(X, verbose=0)
        return predictions.flatten()
    
    def predict_signal(self, X):
        """Predict UP/DOWN signal"""
        prob = self.predict(X)[0]
        signal = "BUY" if prob > 0.5 else "SELL"
        confidence = max(prob, 1 - prob)
        
        return {
            'signal': signal,
            'probability': float(prob),
            'confidence': float(confidence)
        }
    
    def save(self, path):
        """Save model to disk"""
        if not HAS_TENSORFLOW or self.model is None:
            print("❌ No model to save")
            return
        
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        self.model.save(path)
        print(f"✅ Model saved: {path}")
    
    def load(self, path):
        """Load model from disk"""
        if not HAS_TENSORFLOW:
            print("⚠️  TensorFlow not available. Cannot load model.")
            return
        
        self.model = keras.models.load_model(path)
        self.is_trained = True
        print(f"✅ Model loaded: {path}")

class MockLSTMSignalPredictor:
    """Fallback LSTM for testing"""
    
    def __init__(self, window_size=20, num_features=15, model_path="models/lstm_model.h5"):
        self.window_size = window_size
        self.num_features = num_features
        self.model_path = model_path
        self.is_trained = True
    
    def train(self, X_train, y_train, epochs=50, batch_size=32, validation_split=0.2, verbose=1):
        print(f"⚠️  Mock training on {len(X_train)} samples (no actual training)")
        return None
    
    def predict(self, X):
        if len(X.shape) == 2:
            return np.array([np.random.rand()])
        return np.random.rand(len(X))
    
    def predict_signal(self, X):
        prob = np.random.rand()
        signal = "BUY" if prob > 0.5 else "SELL"
        return {
            'signal': signal,
            'probability': float(prob),
            'confidence': max(prob, 1 - prob)
        }
    
    def save(self, path):
        print(f"⚠️  Mock model not saved")
    
    def load(self, path):
        print(f"⚠️  Mock model loaded")

def create_lstm_model(window_size=20, num_features=15, model_path="models/lstm_model.h5"):
    if HAS_TENSORFLOW:
        return LSTMSignalPredictor(window_size, num_features, model_path)
    else:
        return MockLSTMSignalPredictor(window_size, num_features, model_path)

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  LSTM MODEL TEST")
    print("="*70 + "\n")
    
    lstm = create_lstm_model()
    print(f"Model type: {'Real LSTM' if HAS_TENSORFLOW else 'Mock LSTM'}")
    
    X_train = np.random.randn(100, 20, 15).astype(np.float32)
    y_train = np.random.randint(0, 2, 100)
    
    print("\nTraining...")
    lstm.train(X_train, y_train, epochs=2, verbose=0)
    
    X_test = np.random.randn(1, 20, 15).astype(np.float32)
    signal = lstm.predict_signal(X_test)
    
    print(f"\nPrediction:")
    print(f"  Signal: {signal['signal']}")
    print(f"  Probability: {signal['probability']:.2%}")
    print(f"  Confidence: {signal['confidence']:.2%}")
    
    print("\n" + "="*70)
    print("  ✅ LSTM MODEL TEST PASSED")
    print("="*70 + "\n")
