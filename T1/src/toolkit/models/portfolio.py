"""
Portfolio — DataClass representing an investment portfolio composed of multiple PriceSeries.

Manages asset aggregation, calendar alignment, weight assignment, and auto-computed
statistical and risk metrics upon instantiation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
import numpy as np
import pandas as pd

from .series import PriceSeries


@dataclass
class Portfolio:
    """DataClass representing an investment portfolio composed of multiple PriceSeries assets.

    Attributes:
        assets: List of PriceSeries instances constituting the portfolio.
        weights: Optional asset allocation weights. Supported formats:
                 - None: automatically assigns equal weights (1 / N).
                 - Dict[str, float]: mapping of ticker symbol -> weight.
                 - List[float] or np.ndarray: weight sequence ordered corresponding to assets.
                 Weights will be verified and normalized to sum to 1.0.
        name: Human-readable name or identifier for the portfolio.
        initial_capital: Nominal baseline capital allocated to the portfolio (default: 10,000.0).

    Auto-computed attributes (initialized in __post_init__):
        weights_dict: Normalized dictionary mapping ticker to assigned allocation weight.
        weights_vector: 1D NumPy array of normalized weights aligned with `assets`.
        returns_df: Date-indexed DataFrame of aligned individual asset returns.
        prices_df: Date-indexed DataFrame of aligned individual asset close prices.
        portfolio_returns: Date-indexed Series of daily aggregated portfolio returns.
        mean_return: Arithmetic mean of daily portfolio returns.
        std_return: Sample standard deviation (volatility) of daily portfolio returns.
        covariance_matrix: Covariance matrix of daily asset returns.
        correlation_matrix: Correlation matrix of daily asset returns.
    """

    assets: List[PriceSeries]
    weights: Optional[Union[Dict[str, float], List[float], np.ndarray]] = None
    name: str = "Portfolio"
    initial_capital: float = 10000.0

    # Auto-computed fields
    weights_dict: Dict[str, float] = field(init=False)
    weights_vector: np.ndarray = field(init=False)
    returns_df: pd.DataFrame = field(init=False)
    prices_df: pd.DataFrame = field(init=False)
    portfolio_returns: pd.Series = field(init=False)
    mean_return: float = field(init=False)
    std_return: float = field(init=False)
    covariance_matrix: pd.DataFrame = field(init=False)
    correlation_matrix: pd.DataFrame = field(init=False)

    def __post_init__(self):
        """Validates inputs, aligns asset time series, normalizes weights,

        and computes fundamental portfolio metrics.
        """
        if not self.assets:
            raise ValueError("Portfolio must contain at least one PriceSeries asset.")

        for asset in self.assets:
            if not isinstance(asset, PriceSeries):
                raise TypeError(
                    f"All items in 'assets' must be instances of PriceSeries, got {type(asset)}."
                )

        # Ensure unique tickers
        tickers = [asset.ticker for asset in self.assets]
        if len(tickers) != len(set(tickers)):
            raise ValueError(f"Duplicate tickers detected in portfolio assets: {tickers}")

        # 1. Align time series across all assets by Date index
        self._align_data()

        # 2. Process and normalize allocation weights
        self._process_weights()

        # 3. Compute portfolio daily returns and statistical metrics
        self._compute_metrics()

    def _align_data(self):
        """Aligns asset returns and close prices across calendars using inner join."""
        returns_dict = {asset.ticker: asset.data["returns"] for asset in self.assets}
        prices_dict = {asset.ticker: asset.data["close"] for asset in self.assets}

        # Combine into DataFrame and drop dates where any asset lacks data
        self.returns_df = pd.DataFrame(returns_dict).dropna()
        if self.returns_df.empty:
            raise ValueError(
                "Unable to align asset returns: No overlapping trading dates found across assets."
            )

        self.prices_df = pd.DataFrame(prices_dict).reindex(self.returns_df.index)

    def _process_weights(self):
        """Validates and normalizes weights to sum to 1.0."""
        n_assets = len(self.assets)
        tickers = [asset.ticker for asset in self.assets]

        if self.weights is None:
            # Default to equal weighting (1/N)
            equal_w = 1.0 / n_assets
            self.weights_dict = {ticker: equal_w for ticker in tickers}
        elif isinstance(self.weights, dict):
            # Dict mapping ticker -> weight
            missing = set(tickers) - set(self.weights.keys())
            if missing:
                raise ValueError(
                    f"Weights dictionary is missing allocations for tickers: {missing}"
                )
            raw_weights = [float(self.weights[t]) for t in tickers]
            total_w = sum(raw_weights)
            if total_w == 0:
                raise ValueError("Sum of allocation weights cannot be zero.")
            normalized = [w / total_w for w in raw_weights]
            self.weights_dict = {t: w for t, w in zip(tickers, normalized)}
        elif isinstance(self.weights, (list, tuple, np.ndarray)):
            if len(self.weights) != n_assets:
                raise ValueError(
                    f"Length of weights ({len(self.weights)}) does not match "
                    f"number of assets ({n_assets})."
                )
            raw_weights = [float(w) for w in self.weights]
            total_w = sum(raw_weights)
            if total_w == 0:
                raise ValueError("Sum of allocation weights cannot be zero.")
            normalized = [w / total_w for w in raw_weights]
            self.weights_dict = {t: w for t, w in zip(tickers, normalized)}
        else:
            raise TypeError(
                f"Unsupported weights type '{type(self.weights)}'. "
                "Expected None, dict, list, or numpy array."
            )

        self.weights_vector = np.array([self.weights_dict[t] for t in tickers], dtype=float)

    def _compute_metrics(self):
        """Computes daily weighted returns, covariance, correlation, and basic stats."""
        # Weighted daily portfolio return: R_p = sum(w_i * R_i)
        self.portfolio_returns = (self.returns_df * self.weights_vector).sum(axis=1)
        self.portfolio_returns.name = "portfolio_returns"

        self.mean_return = (
            float(self.portfolio_returns.mean()) if not self.portfolio_returns.empty else 0.0
        )
        self.std_return = (
            float(self.portfolio_returns.std()) if not self.portfolio_returns.empty else 0.0
        )

        self.covariance_matrix = self.returns_df.cov()
        self.correlation_matrix = self.returns_df.corr()

    # -------------------------------------------------------------------------
    # Analytical & Risk Methods
    # -------------------------------------------------------------------------

    @property
    def tickers(self) -> List[str]:
        """List of asset tickers in the portfolio."""
        return [asset.ticker for asset in self.assets]

    @property
    def start_date(self) -> str:
        """First overlapping trading date in portfolio."""
        return str(self.returns_df.index[0].date()) if not self.returns_df.empty else ""

    @property
    def end_date(self) -> str:
        """Last overlapping trading date in portfolio."""
        return str(self.returns_df.index[-1].date()) if not self.returns_df.empty else ""

    def annualized_return(self, trading_days: int = 252) -> float:
        """Computes annualized geometric return of the portfolio."""
        if self.portfolio_returns.empty:
            return 0.0
        return float(((1.0 + self.mean_return) ** trading_days) - 1.0)

    def annualized_volatility(self, trading_days: int = 252) -> float:
        """Computes annualized portfolio volatility based on daily std."""
        return float(self.std_return * np.sqrt(trading_days))

    def sharpe_ratio(self, risk_free_rate: float = 0.0, trading_days: int = 252) -> float:
        """Computes the annualized Sharpe ratio."""
        ann_vol = self.annualized_volatility(trading_days)
        if ann_vol == 0.0:
            return 0.0
        return float((self.annualized_return(trading_days) - risk_free_rate) / ann_vol)

    def cumulative_returns(self) -> pd.Series:
        """Computes cumulative return series starting from 0.0."""
        return (1.0 + self.portfolio_returns).cumprod() - 1.0

    def cumulative_wealth(self, capital: Optional[float] = None) -> pd.Series:
        """Computes the monetary value trajectory of the portfolio over time."""
        base_capital = self.initial_capital if capital is None else capital
        return base_capital * (1.0 + self.portfolio_returns).cumprod()

    def drawdown_series(self) -> pd.Series:
        """Computes portfolio underwater drawdown series relative to running high."""
        wealth = (1.0 + self.portfolio_returns).cumprod()
        running_max = wealth.cummax()
        return (wealth - running_max) / running_max

    def max_drawdown(self) -> float:
        """Computes maximum historical peak-to-trough decline (negative float)."""
        dd = self.drawdown_series()
        return float(dd.min()) if not dd.empty else 0.0

    def value_at_risk(
        self, confidence_level: float = 0.95, method: str = "historical"
    ) -> float:
        """Computes daily Value at Risk (VaR) at the specified confidence level.

        Args:
            confidence_level: Probability threshold (e.g., 0.95 for 95% VaR).
            method: 'historical' (empirical quantile) or 'parametric' (Gaussian assumption).

        Returns:
            Daily VaR expressed as a decimal return (typically negative).
        """
        if self.portfolio_returns.empty:
            return 0.0

        if method == "historical":
            return float(np.percentile(self.portfolio_returns, (1.0 - confidence_level) * 100.0))
        elif method == "parametric":
            try:
                from scipy.stats import norm
                z = float(norm.ppf(1.0 - confidence_level))
            except ImportError:
                # Standalone standard normal inverse CDF approximation (Beasley-Springer-Moro / Acklam)
                p = 1.0 - confidence_level
                # Common financial quantiles fallback or rational approximation
                common_z = {0.05: -1.6448536269514722, 0.01: -2.3263478740408408, 0.10: -1.2815515655446004}
                if round(p, 4) in common_z:
                    z = common_z[round(p, 4)]
                else:
                    # Rational approximation for normal quantiles
                    t = np.sqrt(-2.0 * np.log(p))
                    c0, c1, c2 = 2.515517, 0.802853, 0.010328
                    d1, d2, d3 = 1.432788, 0.189269, 0.001308
                    z = -(t - ((c2 * t + c1) * t + c0) / (((d3 * t + d2) * t + d1) * t + 1.0))
            return float(self.mean_return + z * self.std_return)
        else:
            raise ValueError(f"Unknown VaR method '{method}'. Use 'historical' or 'parametric'.")

    def conditional_value_at_risk(self, confidence_level: float = 0.95) -> float:
        """Computes daily Conditional Value at Risk (CVaR / Expected Shortfall)."""
        var = self.value_at_risk(confidence_level=confidence_level, method="historical")
        tail = self.portfolio_returns[self.portfolio_returns <= var]
        return float(tail.mean()) if not tail.empty else var

    def summary(self, risk_free_rate: float = 0.0) -> Dict[str, Any]:
        """Returns a comprehensive summary dictionary of portfolio characteristics."""
        return {
            "name": self.name,
            "assets": self.tickers,
            "weights": self.weights_dict,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "observations": len(self.portfolio_returns),
            "daily_mean_return": self.mean_return,
            "daily_std_return": self.std_return,
            "annualized_return": self.annualized_return(),
            "annualized_volatility": self.annualized_volatility(),
            "sharpe_ratio": self.sharpe_ratio(risk_free_rate=risk_free_rate),
            "max_drawdown": self.max_drawdown(),
            "historical_var_95": self.value_at_risk(0.95),
            "cvar_95": self.conditional_value_at_risk(0.95),
        }

    def __repr__(self) -> str:
        weights_str = ", ".join(f"{t}: {w:.1%}" for t, w in self.weights_dict.items())
        return (
            f"Portfolio(name='{self.name}', assets={len(self.assets)}, "
            f"weights={{{weights_str}}}, mean={self.mean_return:.5f}, "
            f"std={self.std_return:.5f}, sharpe={self.sharpe_ratio():.2f})"
        )
