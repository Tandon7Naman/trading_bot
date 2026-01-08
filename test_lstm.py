import numpy as np
from src.models.lstm_signal import create_lstm_model

def test_lstm():
    print("\n" + "="*70)
    print("  🧠 LSTM NEURAL NETWORK TEST")
    print("="*70 + "\n")
    
    lstm = create_lstm_model(window_size=20, num_features=15)
    print(f"✅ LSTM model created")
    print(f"   Input: (batch, 20 timesteps, 15 features)")
    print(f"   Output: Probability of UP move (0-1)\n")
    
    print("Creating mock training data...")
    X_train = np.random.randn(100, 20, 15).astype(np.float32)
    y_train = np.random.randint(0, 2, 100)
    print(f"✅ Training data shape: {X_train.shape}")
    print(f"   Labels: {np.bincount(y_train)} (DOWN/UP counts)\n")
    
    print("Training LSTM (2 epochs for speed)...")
    lstm.train(X_train, y_train, epochs=2, batch_size=16, verbose=0)
    print("✅ Training complete\n")
    
    print("Testing predictions...")
    X_test = np.random.randn(5, 20, 15).astype(np.float32)
    
    for i, x in enumerate(X_test):
        signal = lstm.predict_signal(x)
        print(f"  Sample {i+1}: {signal['signal']:4s} | "
              f"Prob: {signal['probability']:.2%} | "
              f"Confidence: {signal['confidence']:.2%}")
    
    print("\n" + "-"*70)
    print("Batch Prediction Test:")
    probs = lstm.predict(X_test)
    print(f"Probabilities: {probs}")
    print(f"Shape: {probs.shape}")
    
    print("\n" + "="*70)
    print("  ✅ LSTM MODEL TEST PASSED")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_lstm()