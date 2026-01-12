class PivotLevelCalculator:
    """Calculate classic and Fibonacci pivot levels for MCX Gold."""
    @staticmethod
    def calculate_pivot_levels(high, low, close):
        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        range_hl = high - low
        r_fib = close + 0.382 * range_hl
        s_fib = close - 0.382 * range_hl
        return {
            'pivot': pivot,
            'r1': r1,
            'r2': r2,
            's1': s1,
            's2': s2,
            'r_fib': r_fib,
            's_fib': s_fib
        }

if __name__ == "__main__":
    prev_high, prev_low, prev_close = 69000, 68500, 68800
    levels = PivotLevelCalculator.calculate_pivot_levels(prev_high, prev_low, prev_close)
    print(f"Pivot Levels: {levels}")
