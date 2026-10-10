from dataclasses import dataclass, field
from typing import Optional, Any
import pandas as pd
import numpy as np

@dataclass
class PriceSeries:
    ticker: str
    asset_type: str  # e.g., 'equity', 'index', 'macro'
    data: pd.DataFrame  # Standardized columns: Date index, 'close', 'returns'
    mean_return: float = field(init=False)
    std_return: float = field(init=False)

    def __post_init__(self):
        """Auto-computes required basic statistical metrics upon instantiation."""
        if "close" not in self.data.columns:
            raise ValueError("Input data must contain a 'close' column.")

        # Ensure returns are calculated
        if "returns" not in self.data.columns:
            self.data["returns"] = self.data["close"].pct_change().dropna()

        clean_returns = self.data["returns"].dropna()
        self.mean_return = float(clean_returns.mean()) if not clean_returns.empty else 0.0
        self.std_return = float(clean_returns.std()) if not clean_returns.empty else 0.0

    def __len__(self) -> int:
        """Returns the number of observations in the price series."""
        return len(self.returns)

    def __str__(self) -> str:
        return (
            f"PriceSeries({self.ticker}, type='{self.asset_type}', "
            f"obs={len(self)}, mean={self.mean_return:+.4f}, std={self.std_return:.4f})"
        )

    @property
    def returns(self) -> pd.Series:
        """Returns the clean daily returns series."""
        return self.data["returns"].dropna()

    @property
    def close(self) -> pd.Series:
        """Returns the close price series."""
        return self.data["close"].dropna()

    def annualized_return(self, trading_days: int = 252) -> float:
        """Computes the annualized return assuming geometric compounding."""
        if self.returns.empty:
            return 0.0
        return float(((1.0 + self.mean_return) ** trading_days) - 1.0)

    def annualized_volatility(self, trading_days: int = 252) -> float:
        """Computes the annualized volatility (standard deviation)."""
        return float(self.std_return * np.sqrt(trading_days))

    def sharpe_ratio(self, risk_free_rate: float = 0.0, trading_days: int = 252) -> float:
        """Computes the annualized Sharpe ratio."""
        ann_vol = self.annualized_volatility(trading_days)
        if ann_vol == 0.0:
            return 0.0
        return float((self.annualized_return(trading_days) - risk_free_rate) / ann_vol)

    def cumulative_returns(self) -> pd.Series:
        """Computes the cumulative return series starting from 0."""
        return (1.0 + self.returns).cumprod() - 1.0

    def drawdown_series(self) -> pd.Series:
        """Computes underwater drawdown series relative to running maximum."""
        wealth = (1.0 + self.returns).cumprod()
        running_max = wealth.cummax()
        return (wealth - running_max) / running_max

    def max_drawdown(self) -> float:
        """Computes maximum historical peak-to-trough decline (negative value)."""
        dd = self.drawdown_series()
        return float(dd.min()) if not dd.empty else 0.0

    def value_at_risk(self, confidence_level: float = 0.95) -> float:
        """Computes historical daily Value at Risk (VaR) at given confidence level."""
        if self.returns.empty:
            return 0.0
        return float(np.percentile(self.returns, (1.0 - confidence_level) * 100.0))

    def simulate_montecarlo(
        self,
        n_simulations: int = 1000,
        horizon: int = 252,
        mu: Optional[float] = None,
        sigma: Optional[float] = None,
        initial_value: Optional[float] = None,
        seed: Optional[int] = None,
    ):
        """Simulates stochastic price trajectories using Geometric Brownian Motion (GBM).

        Args:
            n_simulations: Number of paths (default: 1000).
            horizon: Number of trading days ahead (default: 252).
            mu: Daily drift (defaults to empirical mean_return).
            sigma: Daily volatility (defaults to empirical std_return).
            initial_value: Starting price (defaults to most recent close price).
            seed: Seed for random number generator.

        Returns:
            MonteCarloResult instance.
        """
        from .monte_carlo import MonteCarloEngine

        init_val = initial_value if initial_value is not None else float(self.close.iloc[-1])
        drift = mu if mu is not None else self.mean_return
        vol = sigma if sigma is not None else self.std_return

        return MonteCarloEngine.simulate_gbm(
            initial_value=init_val,
            mu=drift,
            sigma=vol,
            horizon=horizon,
            n_simulations=n_simulations,
            seed=seed,
            name=self.ticker,
        )

    def plot_montecarlo(
        self,
        n_simulations: int = 1000,
        horizon: int = 252,
        save_path: Optional[str] = None,
        show: bool = True,
        **kwargs,
    ):
        """Executes Monte Carlo simulation and renders trajectory and distribution plots."""
        sim = self.simulate_montecarlo(n_simulations=n_simulations, horizon=horizon, **kwargs)
        return sim.plot(save_path=save_path, show=show)