from typing import Literal

from pydantic import BaseModel, Field, field_validator


class StrategySettings(BaseModel):
    """Parameters specific to the ADX/RSI strategy"""
    adx_threshold: int = Field(25, ge=10, le=50, description="Minimum trend strength")
    rsi_upper: int = Field(70, ge=50, le=90, description="Overbought threshold")
    rsi_lower: int = Field(30, ge=10, le=50, description="Oversold threshold")

class RiskSettings(BaseModel):
    """Risk Management Limits"""
    max_risk_per_trade: float = Field(0.01, ge=0.001, le=0.05, description="1% standard risk")
    max_daily_loss_usd: float = Field(500.0, gt=0, description="Hard stop for daily loss")
    max_lot_size: float = Field(1.0, gt=0, le=10.0, description="Safety ceiling for lot size")

class BotConfig(BaseModel):
        # Trading and backtest parameters (added for compatibility)
        initial_capital: float = Field(100000, description="Initial capital for paper trading/backtest")
        trade_quantity: int = Field(10, description="Default trade quantity")
        tp_percent: float = Field(2.0, description="Take profit percent for backtest")
        sl_percent: float = Field(1.0, description="Stop loss percent for backtest")
    """Master Configuration with Security Locks"""
    # Security: Lock bot to specific account ID to prevent trading on wrong account
    authorized_account_id: int = Field(..., description="MT5 Login ID Security Lock")

    symbol: str = Field("XAUUSD", pattern=r"^[A-Z]{6}$")
    timeframe: str = "M1"
    mode: Literal["paper", "live"] = "paper"

    strategy: StrategySettings = StrategySettings()
    risk: RiskSettings = RiskSettings()

    @field_validator("symbol")
    @classmethod
    def validate_gold_symbol(cls, v):
        if v not in ["XAUUSD", "GOLD", "GC=F"]:
             raise ValueError(f"Symbol {v} is not a valid Gold ticker.")
        return v

# --- USAGE EXAMPLE ---
# from config_schema import BotConfig
# try:
#     config = BotConfig(authorized_account_id=12345678)
#     print("✅ Configuration Validated")
# except Exception as e:
#     print(f"❌ Config Error: {e}")
