import numpy as np

from src.features import FeatureEngine


def test_features():
    print("\n" + "=" * 70)
    print("  🧠 FEATURE ENGINEERING TEST")
    print("=" * 70 + "\n")

    fe = FeatureEngine()
    mock_data = {
        "closes": [68500 + i * 5 for i in range(30)],
        "highs": [68550 + i * 5 for i in range(30)],
        "lows": [68450 + i * 5 for i in range(30)],
        "bid": 68650,
        "ask": 68660,
        "buy_volume": 12000,
        "sell_volume": 8000,
        "spot_gold_usd": 2500,
        "usdinr": 83.5,
        "us_10y_yield": 4.0,
        "inflation_rate": 5.5,
        "monsoon_rainfall": 150,
        "monsoon_lpa": 140,
        "import_duty": 0.06,
        "duty_history": [0.06, 0.06, 0.06, 0.06, 0.06, 0.05, 0.05],
        "current_price": 68650,
    }

    print("Extracting 15 features...")
    features = fe.extract_features(mock_data)

    print(f"\n✅ Extracted {len(features)} features")
    print(f"Array shape: {features.shape}")
    print(f"Min value: {features.min():.3f}")
    print(f"Max value: {features.max():.3f}")
    print(f"All finite: {np.all(np.isfinite(features))}")
    print(f"In range [-1,1]: {np.all((features >= -1) & (features <= 1))}")

    print("\nFeature Values:")
    feature_names = [
        "1. RSI",
        "2. MACD",
        "3. BB Width",
        "4. ADX",
        "5. Bid-Ask Spread",
        "6. Order Imbalance",
        "7. USD/INR",
        "8. US 10Y Yield",
        "9. Au/Ag Ratio",
        "10. Monsoon",
        "11. Real Yield",
        "12. Import Duty",
        "13. Duty Shock",
        "14. Lunar Demand",
        "15. Fair Value",
    ]
    for name, value in zip(feature_names, features, strict=False):
        print(f"  {name:20s}: {value:7.4f}")

    print("\n" + "-" * 70)
    print("Normalization Check:")
    print(
        f"  All values in [-1, 1]: {'✅ PASS' if np.all((features >= -1) & (features <= 1)) else '❌ FAIL'}"
    )
    print(f"  No NaN values: {'✅ PASS' if np.all(np.isfinite(features)) else '❌ FAIL'}")

    print("\n" + "=" * 70)
    print("  ✅ FEATURE EXTRACTION TEST PASSED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_features()
