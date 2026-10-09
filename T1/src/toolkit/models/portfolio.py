"""
Portfolio — DataClass representing an investment portfolio composed of multiple PriceSeries.

Manages asset aggregation, calendar alignment, weight assignment, and auto-computed
statistical and risk metrics upon instantiation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any, Tuple
import numpy as np
import pandas as pd

from .series import PriceSeries
from ..utils.validation import validate_price_dataframe, validate_portfolio_weights, ValidationError
from ..utils.cleaning import align_calendar_series


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
            # Enforce structural time series invariants
            validate_price_dataframe(asset.data, required_columns=("close",))

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

        # Synchronize calendars using inner intersection
        self.returns_df = align_calendar_series(returns_dict, join_method="inner")
        if self.returns_df.empty:
            raise ValueError(
                "Unable to align asset returns: No overlapping trading dates found across assets."
            )

        self.prices_df = pd.DataFrame(prices_dict).reindex(self.returns_df.index)

    def _process_weights(self):
        """Validates and normalizes weights using policy validation utilities."""
        tickers = [asset.ticker for asset in self.assets]

        if self.weights is None:
            # Default to equal weighting (1/N)
            equal_w = 1.0 / len(self.assets)
            self.weights_dict = {ticker: equal_w for ticker in tickers}
        else:
            self.weights_dict = validate_portfolio_weights(self.weights, tickers)

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

    # -------------------------------------------------------------------------
    # Monte Carlo Stochastic Simulation (Requirement 4.4)
    # -------------------------------------------------------------------------

    def simulate_montecarlo(
        self,
        n_simulations: int = 1000,
        horizon: int = 252,
        mu: Optional[float] = None,
        sigma: Optional[float] = None,
        initial_capital: Optional[float] = None,
        seed: Optional[int] = None,
        multivariate: bool = True,
    ):
        """Simulates future portfolio trajectories using Monte Carlo stochastic diffusion.

        Supports two modeling approaches:
          1. Correlated multivariate Geometric Brownian Motion (multivariate=True, default):
             Takes individual asset drifts and the full empirical covariance matrix
             into account via Cholesky decomposition.
          2. Aggregate portfolio Geometric Brownian Motion (multivariate=False):
             Projects total capital using the portfolio's aggregate drift and volatility.

        Args:
            n_simulations: Total number of Monte Carlo paths to generate (default: 1,000).
            horizon: Forward projection horizon in trading days (default: 252 days = 1 year).
            mu: Expected daily drift parameter (overrides empirical mean if provided).
            sigma: Expected daily volatility parameter (overrides empirical std if provided).
            initial_capital: Starting capital (defaults to self.initial_capital).
            seed: Random seed for deterministic reproducibility.
            multivariate: Whether to perform correlated multivariate asset simulation.

        Returns:
            MonteCarloResult: Object encapsulating all paths, statistics, risk metrics, and plots.
        """
        from .monte_carlo import MonteCarloEngine

        cap = initial_capital if initial_capital is not None else self.initial_capital

        if multivariate and len(self.assets) > 1 and mu is None and sigma is None:
            mu_vec = np.array([asset.mean_return for asset in self.assets])
            cov_mat = self.covariance_matrix.values
            return MonteCarloEngine.simulate_multivariate_gbm(
                initial_capital=cap,
                weights=self.weights_vector,
                mu_vector=mu_vec,
                cov_matrix=cov_mat,
                horizon=horizon,
                n_simulations=n_simulations,
                seed=seed,
                name=self.name,
            )
        else:
            drift = mu if mu is not None else self.mean_return
            vol = sigma if sigma is not None else self.std_return
            return MonteCarloEngine.simulate_gbm(
                initial_value=cap,
                mu=drift,
                sigma=vol,
                horizon=horizon,
                n_simulations=n_simulations,
                seed=seed,
                name=self.name,
            )

    def plot_montecarlo(
        self,
        n_simulations: int = 1000,
        horizon: int = 252,
        save_path: Optional[str] = None,
        show: bool = True,
        **kwargs,
    ):
        """Executes Monte Carlo simulation and renders trajectory and distribution plots.

        Args:
            n_simulations: Number of paths (default: 1,000).
            horizon: Time horizon in trading days (default: 252).
            save_path: Optional file path to export image.
            show: Whether to display interactive plot window.
            **kwargs: Extra parameters forwarded to simulate_montecarlo.

        Returns:
            Tuple of (matplotlib.figure.Figure, np.ndarray of Axes).
        """
        sim = self.simulate_montecarlo(n_simulations=n_simulations, horizon=horizon, **kwargs)
        return sim.plot(
            title=f"Monte Carlo Simulation: {self.name} (Capital: {sim.initial_value:,.0f}€)",
            save_path=save_path,
            show=show,
        )

    # -------------------------------------------------------------------------
    # Analytical Reporting & Visualization Dashboard (Requirement 4.5)
    # -------------------------------------------------------------------------

    def report(
        self,
        risk_free_rate: float = 0.0,
        confidence_level: float = 0.95,
        output_path: Optional[str] = None,
    ) -> str:
        """Generates a structured, publication-ready analytical report in Markdown.

        Includes:
          - Portfolio Overview & Metadata
          - Asset Allocation Breakdown Table
          - Key Performance & Risk Diagnostics
          - Cross-Asset Correlation Matrix
          - Automated Risk Diagnostics & Warning Flags

        Args:
            risk_free_rate: Annualized risk-free benchmark rate (default: 0.0).
            confidence_level: Confidence level for VaR and CVaR (default: 0.95).
            output_path: Optional file path to export the Markdown document.

        Returns:
            Markdown string with formatted tables and risk warnings.
        """
        conf_pct = int(confidence_level * 100)
        cum_ret = float((1.0 + self.portfolio_returns).prod() - 1.0)
        ann_ret = self.annualized_return()
        ann_vol = self.annualized_volatility()
        sharpe = self.sharpe_ratio(risk_free_rate=risk_free_rate)
        max_dd = self.max_drawdown()
        hist_var = self.value_at_risk(confidence_level, method="historical")
        param_var = self.value_at_risk(confidence_level, method="parametric")
        cvar = self.conditional_value_at_risk(confidence_level)

        # Asset breakdown table
        asset_rows = []
        for asset in self.assets:
            w = self.weights_dict[asset.ticker]
            asset_rows.append(
                f"| `{asset.ticker}` | {asset.asset_type.capitalize()} | {w:.1%} | "
                f"{asset.mean_return:+.4f} | {asset.annualized_return():+.2%} | "
                f"{asset.annualized_volatility():.2%} | {asset.sharpe_ratio(risk_free_rate):.2f} | "
                f"{asset.max_drawdown():.2%} |"
            )
        asset_table = "\n".join(asset_rows)

        # Correlation table
        corr_df = self.correlation_matrix.round(3)
        corr_headers = "| | " + " | ".join(f"`{col}`" for col in corr_df.columns) + " |"
        corr_sep = "|---|" + "---|"*len(corr_df.columns)
        corr_rows = []
        for idx, row in corr_df.iterrows():
            row_str = f"| `{idx}` | " + " | ".join(f"{val:.3f}" for val in row) + " |"
            corr_rows.append(row_str)
        corr_table = "\n".join([corr_headers, corr_sep] + corr_rows)

        # Quantitative Diagnostics & Automated Risk Warnings
        warnings = []
        # 1. Concentration risk
        max_weight_ticker = max(self.weights_dict, key=self.weights_dict.get)
        max_w = self.weights_dict[max_weight_ticker]
        if max_w > 0.40:
            warnings.append(
                f"- ⚠️ **Concentration Risk Warning**: Asset `{max_weight_ticker}` represents {max_w:.1%} "
                "of the portfolio (exceeds conservative 40% diversification threshold)."
            )
        else:
            warnings.append("- ✅ **Concentration**: Well-balanced asset allocations (< 40% max per position).")

        # 2. Pairwise Correlation / Collinearity
        high_corrs = []
        tickers = self.tickers
        for i in range(len(tickers)):
            for j in range(i + 1, len(tickers)):
                r = self.correlation_matrix.iloc[i, j]
                if r > 0.75:
                    high_corrs.append(f"`{tickers[i]}` & `{tickers[j]}` (r = {r:.2f})")
        if high_corrs:
            warnings.append(
                f"- ⚠️ **Collinearity / Low Diversification Warning**: Strong positive correlation detected between: "
                + ", ".join(high_corrs) + ". This dampens portfolio diversification benefits."
            )
        else:
            warnings.append("- ✅ **Diversification**: No excessive collinearity detected between pairs (all pairwise r ≤ 0.75).")

        # 3. Tail Risk & Drawdown
        if max_dd < -0.20:
            warnings.append(
                f"- ⚠️ **Severe Drawdown Warning**: Historical maximum drawdown of {max_dd:.2%} "
                "exceeds the 20% moderate risk threshold."
            )
        else:
            warnings.append(f"- ✅ **Drawdown Profile**: Maximum historical peak-to-trough decline contained at {max_dd:.2%}.")

        if abs(hist_var) > 0.025:
            warnings.append(
                f"- ⚠️ **Tail Risk Alert**: Daily {conf_pct}% VaR is {hist_var:.2%}, indicating significant potential for intraday tail loss."
            )

        diagnostics_block = "\n".join(warnings)

        md_content = f"""# 📊 Portfolio Quantitative Analysis & Risk Report: {self.name}

> Generated on: **{self.end_date}** | MIAX-BME Quantitative Analytics Toolkit  
> Base Nominal Capital: **{self.initial_capital:,.2f}** | Observations: **{len(self.portfolio_returns)} trading days** ({self.start_date} to {self.end_date})

---

## 1. Executive Summary

| Metric | Portfolio Value | Description / Interpretation |
|---|---|---|
| **Cumulative Return** | **{cum_ret:+.2%}** | Total compound growth over the observation period |
| **Annualized Return** | **{ann_ret:+.2%}** | Geometric annualized expected compound rate |
| **Annualized Volatility** | **{ann_vol:.2%}** | Annualized standard deviation ($\\sigma \\times \\sqrt{{252}}$) |
| **Sharpe Ratio (Rf={risk_free_rate:.1%})** | **{sharpe:.2f}** | Excess return per unit of volatility |
| **Maximum Drawdown** | **{max_dd:.2%}** | Maximum peak-to-trough decline |
| **Historical Daily VaR ({conf_pct}%)** | **{hist_var:.2%}** | Maximum expected daily loss at {conf_pct}% confidence (Empirical) |
| **Parametric Daily VaR ({conf_pct}%)** | **{param_var:.2%}** | Daily {conf_pct}% Value at Risk under Gaussian assumption |
| **Daily CVaR / Expected Shortfall ({conf_pct}%)** | **{cvar:.2%}** | Average loss in the worst {100-conf_pct}% tail distribution |

---

## 2. Asset Allocation Breakdown

| Ticker | Type | Weight | Daily Mean | Ann. Return | Ann. Vol | Sharpe | Max DD |
|---|---|---|---|---|---|---|---|
{asset_table}

---

## 3. Cross-Asset Correlation Matrix

{corr_table}

---

## 4. Automated Risk Diagnostics & Warning Flags

{diagnostics_block}

---
*Report automatically generated via `Portfolio.report()` (Toolkit BME-MIAX).*
"""

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md_content)

        return md_content

    def plots_report(
        self,
        figsize: Tuple[int, int] = (16, 11),
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Any:
        """Generates an analytics visual dashboard with value-added reporting panels.

        Panels:
          1. [Top-Left] Comparative Cumulative Performance:
             Tracks normalized wealth paths (1.0 base) of the Portfolio vs each asset.
          2. [Top-Right] Portfolio Underwater Drawdown Evolution:
             Time series of peak-to-trough decline with Max Drawdown level highlighted.
          3. [Bottom-Left] Asset Correlation Matrix Heatmap:
             Annotated heatmap showing cross-asset linear dependency and diversification.
          4. [Bottom-Right] Portfolio Daily Return Distribution:
             Histogram with KDE curve, historical 95% VaR and CVaR cutoff lines.

        Args:
            figsize: Figure size in inches (default: 16x11).
            save_path: Optional file path to export the figure (PNG/PDF).
            show: Whether to invoke plt.show().

        Returns:
            Tuple of (matplotlib.figure.Figure, np.ndarray of Axes).
        """
        import matplotlib.pyplot as plt

        fig, axs = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle(
            f"Portfolio Quantitative Diagnostics & Visual Dashboard: {self.name}",
            fontsize=15,
            fontweight="bold",
            y=0.98,
        )

        ax_perf, ax_dd = axs[0, 0], axs[0, 1]
        ax_corr, ax_dist = axs[1, 0], axs[1, 1]

        # ---------------- Panel 1: Comparative Cumulative Performance ----------------
        dates = self.portfolio_returns.index

        # Portfolio wealth curve (base 1.0)
        port_cum = (1.0 + self.portfolio_returns).cumprod()
        ax_perf.plot(dates, port_cum, color="#1e40af", linewidth=2.5, label=f"Portfolio ({self.name})")

        # Constituent assets normalized wealth
        colors = ["#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"]
        for i, asset in enumerate(self.assets):
            asset_ret = self.returns_df[asset.ticker]
            asset_cum = (1.0 + asset_ret).cumprod()
            c = colors[i % len(colors)]
            ax_perf.plot(
                dates,
                asset_cum,
                color=c,
                linewidth=1.2,
                linestyle="--",
                alpha=0.8,
                label=f"{asset.ticker} ({self.weights_dict[asset.ticker]:.0%})",
            )

        ax_perf.axhline(1.0, color="#64748b", linestyle=":", linewidth=1.0)
        ax_perf.set_title("1. Comparative Cumulative Performance (Base 1.0)", fontsize=11, fontweight="semibold")
        ax_perf.set_ylabel("Normalized Growth", fontsize=10)
        ax_perf.grid(True, linestyle=":", alpha=0.5)
        ax_perf.legend(loc="upper left", fontsize=8.5, framealpha=0.9)

        # ---------------- Panel 2: Underwater Drawdown Evolution ----------------
        dd = self.drawdown_series()
        ax_dd.plot(dates, dd, color="#dc2626", linewidth=1.5, label="Drawdown")
        ax_dd.fill_between(dates, dd, 0, color="#ef4444", alpha=0.25)
        max_dd_val = float(dd.min())
        max_dd_date = dd.idxmin()
        ax_dd.axhline(max_dd_val, color="#7f1d1d", linestyle="--", linewidth=1.4, label=f"Max Drawdown: {max_dd_val:.2%}")
        ax_dd.scatter([max_dd_date], [max_dd_val], color="#7f1d1d", zorder=5, s=40)

        ax_dd.set_title("2. Historical Portfolio Underwater Drawdown", fontsize=11, fontweight="semibold")
        ax_dd.set_ylabel("Drawdown (%)", fontsize=10)
        ax_dd.grid(True, linestyle=":", alpha=0.5)
        ax_dd.legend(loc="lower left", fontsize=8.5, framealpha=0.9)

        # ---------------- Panel 3: Correlation Matrix Heatmap ----------------
        corr = self.correlation_matrix.values
        tickers = self.tickers
        im = ax_corr.imshow(corr, cmap="coolwarm", vmin=-1.0, vmax=1.0)
        plt.colorbar(im, ax=ax_corr, fraction=0.046, pad=0.04)

        ax_corr.set_xticks(range(len(tickers)))
        ax_corr.set_yticks(range(len(tickers)))
        ax_corr.set_xticklabels(tickers, rotation=45, ha="right", fontsize=9)
        ax_corr.set_yticklabels(tickers, fontsize=9)

        # Annotate text values in heatmap cells
        for i in range(len(tickers)):
            for j in range(len(tickers)):
                val = corr[i, j]
                color = "white" if abs(val) > 0.55 else "black"
                ax_corr.text(j, i, f"{val:.2f}", ha="center", va="center", color=color, fontsize=9, fontweight="bold")

        ax_corr.set_title("3. Asset Correlation Heatmap", fontsize=11, fontweight="semibold")

        # ---------------- Panel 4: Daily Return Distribution & Risk Cutoffs ----------------
        n_bins = min(50, max(20, len(self.portfolio_returns) // 8))
        counts, bins, _ = ax_dist.hist(
            self.portfolio_returns,
            bins=n_bins,
            density=True,
            color="#93c5fd",
            edgecolor="#2563eb",
            alpha=0.6,
            label="Daily Returns",
        )

        var_95 = self.value_at_risk(0.95, method="historical")
        cvar_95 = self.conditional_value_at_risk(0.95)
        mean_ret = self.mean_return

        ax_dist.axvline(mean_ret, color="#1e40af", linestyle="-", linewidth=1.8, label=f"Mean: {mean_ret:+.2%}")
        ax_dist.axvline(var_95, color="#f97316", linestyle="--", linewidth=1.8, label=f"95% VaR: {var_95:.2%}")
        ax_dist.axvline(cvar_95, color="#dc2626", linestyle="--", linewidth=1.8, label=f"95% CVaR: {cvar_95:.2%}")

        # Shade tail risk
        tail_bins = bins[bins <= var_95]
        if len(tail_bins) > 1:
            ax_dist.axvspan(bins[0], var_95, color="#ef4444", alpha=0.18, label="5% Tail Loss Zone")

        ax_dist.set_title("4. Daily Return Distribution & Tail Risk Cutoffs", fontsize=11, fontweight="semibold")
        ax_dist.set_xlabel("Daily Return", fontsize=10)
        ax_dist.set_ylabel("Probability Density", fontsize=10)
        ax_dist.grid(True, linestyle=":", alpha=0.5)
        ax_dist.legend(loc="upper right", fontsize=8.5, framealpha=0.9)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        if show:
            plt.show()

        return fig, axs


