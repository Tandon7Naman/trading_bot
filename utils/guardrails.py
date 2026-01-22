class PerformanceGuardrail:
    """Protocol 8.1: Real-time Strategy Switching"""

    def __init__(self, drawdown_limit=0.02):  # 2% Max Drawdown per session
        self.drawdown_limit = drawdown_limit
        self.initial_equity = 500000.0
        self.current_strategy = "RL_AUTONOMOUS"

    def check_and_switch(self, current_equity):
        drawdown = (self.initial_equity - current_equity) / self.initial_equity
        if drawdown >= self.drawdown_limit and self.current_strategy == "RL_AUTONOMOUS":
            print(f"⚠️ GUARDRAIL TRIGGERED: Drawdown {drawdown:.2%}. Switching to WYCKOFF_LEGACY.")
            self.current_strategy = "WYCKOFF_LEGACY"
            return "WYCKOFF_LEGACY"
        return self.current_strategy
