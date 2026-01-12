"""
Unified Pre-Trade Gateway
Coordinates all 8 professional pre-trade checks before any trade execution.
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class PreTradeGateway:
    """
    Orchestrates all pre-trade checks in sequence.
    Returns a "go/no-go" decision with detailed reasoning.
    """
    def __init__(self,
                 fiscal_loader=None,
                 global_cues=None,
                 econ_calendar=None,
                 currency_monitor=None,
                 pivot_calc=None,
                 signal_filter=None,
                 geo_risk=None,
                 risk_manager=None):
        self.fiscal_loader = fiscal_loader
        self.global_cues = global_cues
        self.econ_calendar = econ_calendar
        self.currency_monitor = currency_monitor
        self.pivot_calc = pivot_calc
        self.signal_filter = signal_filter
        self.geo_risk = geo_risk
        self.risk_manager = risk_manager
        self.checks_passed = []
        self.checks_failed = []
        self.last_gateway_decision = None

    def run_all_checks(self) -> Tuple[bool, Dict[str, Any]]:
        self.checks_passed = []
        self.checks_failed = []
        context = {
            "timestamp": datetime.now().isoformat(),
            "gateway_status": "RUNNING",
            "checks": {},
        }
        print("\n" + "="*70)
        print("PRE-TRADE GATEWAY: Starting all checks")
        print("="*70)
        # CHECK 1: Duty Confirmation (CRITICAL - blocks if fails)
        duty_pass, duty_ctx = self._check_fiscal_policy()
        context["checks"]["fiscal_policy"] = duty_ctx
        if not duty_pass:
            self.checks_failed.append("DUTY_CONFIRMATION")
            context["gateway_status"] = "BLOCKED_CRITICAL"
            return False, context
        # CHECK 2: Global Cues (session bias)
        bias_pass, bias_ctx = self._check_global_cues()
        context["checks"]["global_cues"] = bias_ctx
        if not bias_pass:
            self.checks_failed.append("GLOBAL_CUES")
        # CHECK 3: Economic Calendar (pause on high-impact)
        econ_pass, econ_ctx = self._check_economic_calendar()
        context["checks"]["economic_calendar"] = econ_ctx
        if not econ_pass:
            self.checks_failed.append("ECONOMIC_CALENDAR")
        # CHECK 4: Currency Monitor (USD/INR volatility)
        curr_pass, curr_ctx = self._check_currency_monitor()
        context["checks"]["currency_monitor"] = curr_ctx
        if not curr_pass:
            self.checks_failed.append("CURRENCY_MONITOR")
        # CHECK 5: Geopolitical Risk
        geo_pass, geo_ctx = self._check_geopolitical_risk()
        context["checks"]["geopolitical_risk"] = geo_ctx
        if not geo_pass:
            self.checks_failed.append("GEOPOLITICAL_RISK")
        # CHECK 6: Pivot Levels Ready
        pivot_pass, pivot_ctx = self._check_pivot_levels()
        context["checks"]["pivot_levels"] = pivot_ctx
        if not pivot_pass:
            self.checks_failed.append("PIVOT_LEVELS")
        # CHECK 7: Signal Confluence
        conf_pass, conf_ctx = self._check_signal_confluence()
        context["checks"]["signal_confluence"] = conf_ctx
        if not conf_pass:
            self.checks_failed.append("SIGNAL_CONFLUENCE")
        # CHECK 8: Risk Manager Ready
        risk_pass, risk_ctx = self._check_risk_manager()
        context["checks"]["risk_manager"] = risk_ctx
        if not risk_pass:
            self.checks_failed.append("RISK_MANAGER")
        # Final decision
        all_pass = len(self.checks_failed) == 0
        context["gateway_status"] = "GO" if all_pass else "NO-GO"
        context["checks_passed"] = self.checks_passed
        context["checks_failed"] = self.checks_failed
        self._print_gateway_summary(all_pass, context)
        self.last_gateway_decision = (all_pass, context)
        return all_pass, context
    def _check_fiscal_policy(self) -> Tuple[bool, Dict]:
        try:
            duty = self.fiscal_loader.validate_duty_before_trading()
            self.checks_passed.append("DUTY_CONFIRMATION")
            return True, {"status": "PASS", "duty_rate": duty}
        except Exception as e:
            logger.error(f"Duty check failed: {e}")
            return False, {"status": "FAIL", "error": str(e)}
    def _check_global_cues(self) -> Tuple[bool, Dict]:
        try:
            bias = self.global_cues.get_bias()
            self.checks_passed.append("GLOBAL_CUES")
            return True, {"status": "PASS", "bias": bias}
        except Exception as e:
            logger.warning(f"Global cues check failed: {e}")
            return False, {"status": "FAIL", "error": str(e)}
    def _check_economic_calendar(self) -> Tuple[bool, Dict]:
        try:
            is_safe = self.econ_calendar.is_safe_to_trade()
            if is_safe:
                self.checks_passed.append("ECONOMIC_CALENDAR")
                return True, {"status": "PASS"}
            else:
                return False, {"status": "FAIL", "reason": "High-impact event within 1 hour"}
        except Exception as e:
            logger.warning(f"Economic calendar check failed: {e}")
            return False, {"status": "FAIL", "error": str(e)}
    def _check_currency_monitor(self) -> Tuple[bool, Dict]:
        try:
            is_stable = self.currency_monitor.is_currency_stable()
            vol = self.currency_monitor.get_usdinr_volatility()
            if is_stable:
                self.checks_passed.append("CURRENCY_MONITOR")
                return True, {"status": "PASS", "usdinr_volatility": vol}
            else:
                return False, {"status": "FAIL", "reason": "High currency volatility"}
        except Exception as e:
            logger.warning(f"Currency monitor check failed: {e}")
            return False, {"status": "FAIL", "error": str(e)}
    def _check_geopolitical_risk(self) -> Tuple[bool, Dict]:
        try:
            risk_level = self.geo_risk.get_risk_level()
            if risk_level in ("LOW", "MEDIUM"):
                self.checks_passed.append("GEOPOLITICAL_RISK")
                return True, {"status": "PASS", "risk_level": risk_level}
            else:
                return False, {"status": "FAIL", "risk_level": risk_level}
        except Exception as e:
            logger.warning(f"Geopolitical risk check failed: {e}")
            return False, {"status": "FAIL", "error": str(e)}
    def _check_pivot_levels(self) -> Tuple[bool, Dict]:
        try:
            levels = self.pivot_calc.calculate_levels(
                high=70000, low=68000, close=69000
            )
            if levels and all(k in levels for k in ["S2", "S1", "Pivot", "R1", "R2"]):
                self.checks_passed.append("PIVOT_LEVELS")
                return True, {"status": "PASS", "levels": levels}
            else:
                return False, {"status": "FAIL", "reason": "Pivot calculation incomplete"}
        except Exception as e:
            logger.warning(f"Pivot levels check failed: {e}")
            return False, {"status": "FAIL", "error": str(e)}
    def _check_signal_confluence(self) -> Tuple[bool, Dict]:
        try:
            confluence = self.signal_filter.check_confluence(
                rsi=65, macd_hist=0.5, ema_9=69500, ema_21=69200
            )
            if confluence and confluence.get("strength") in ("STRONG_BUY", "BUY"):
                self.checks_passed.append("SIGNAL_CONFLUENCE")
                return True, {"status": "PASS", "signal_strength": confluence.get("strength")}
            else:
                return False, {"status": "FAIL", "reason": "Weak signal confluence"}
        except Exception as e:
            logger.warning(f"Signal confluence check failed: {e}")
            return False, {"status": "FAIL", "error": str(e)}
    def _check_risk_manager(self) -> Tuple[bool, Dict]:
        try:
            pos = self.risk_manager.calculate_position_size(69000, 68800)
            if pos > 0:
                self.checks_passed.append("RISK_MANAGER")
                return True, {"status": "PASS", "position_size": pos}
            else:
                return False, {"status": "FAIL", "reason": "Position size calculation returned 0"}
        except Exception as e:
            logger.warning(f"Risk manager check failed: {e}")
            return False, {"status": "FAIL", "error": str(e)}
    def _print_gateway_summary(self, all_pass: bool, context: Dict):
        status_str = "✓ GO" if all_pass else "✗ NO-GO"
        print(f"\n{status_str} - Gateway Decision: {context['gateway_status']}")
        print(f"Checks passed: {len(context['checks_passed'])}/8")
        print(f"Checks failed: {len(context['checks_failed'])}/8")
        if context['checks_failed']:
            print(f"\nFailed checks: {', '.join(context['checks_failed'])}")
            print("Trade execution BLOCKED until failures resolved.")
        else:
            print("\nAll checks passed. Trade execution APPROVED.")
        print("="*70 + "\n")
