"""
Monte Carlo Simulation Engine for financial assets and investment portfolios.

Provides stochastic trajectory simulation based on Geometric Brownian Motion (GBM)
and multivariate correlated asset diffusion, with analytical summaries and visual reporting.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


@dataclass
class MonteCarloResult:
    """Encapsulates the output and diagnostics of a Monte Carlo simulation run.

    Attributes:
        name: Name of the asset or portfolio simulated.
        trajectories: 2D NumPy array of shape (horizon + 1, n_simulations)
                      containing the simulated value paths over time.
        horizon: Number of forward time steps (e.g. trading days).
        n_simulations: Total number of generated Monte Carlo trajectories.
        initial_value: Starting price or capital at t = 0.
        mu: Drift parameter (daily expected return) used in the simulation.
        sigma: Diffusion parameter (daily volatility) used in the simulation.
        method: Stochastic model employed ('gbm' or 'multivariate_gbm').
    """

    name: str
    trajectories: np.ndarray
    horizon: int
    n_simulations: int
    initial_value: float
    mu: float
    sigma: float
    method: str = "gbm"
    time_steps: np.ndarray = field(init=False)

    def __post_init__(self):
        self.time_steps = np.arange(self.horizon + 1)

    @property
    def terminal_values(self) -> np.ndarray:
        """Simulated asset or portfolio values at the final horizon step T."""
        return self.trajectories[-1, :]

    @property
    def terminal_returns(self) -> np.ndarray:
        """Percentage return from t=0 to t=T for each simulated path."""
        return (self.terminal_values - self.initial_value) / self.initial_value

    @property
    def terminal_mean(self) -> float:
        """Expected (mean) value at horizon T."""
        return float(np.mean(self.terminal_values))

    @property
    def terminal_median(self) -> float:
        """Median value at horizon T."""
        return float(np.median(self.terminal_values))

    @property
    def terminal_std(self) -> float:
        """Standard deviation of simulated terminal values."""
        return float(np.std(self.terminal_values))

    @property
    def terminal_min(self) -> float:
        """Minimum observed terminal value across simulations."""
        return float(np.min(self.terminal_values))

    @property
    def terminal_max(self) -> float:
        """Maximum observed terminal value across simulations."""
        return float(np.max(self.terminal_values))

    @property
    def probability_of_loss(self) -> float:
        """Estimated probability that terminal value is below the initial investment."""
        return float(np.mean(self.terminal_values < self.initial_value))

    def percentiles(self, q: Optional[List[float]] = None) -> Dict[float, float]:
        """Calculates specific percentiles of the terminal value distribution.

        Args:
            q: List of percentiles in [0, 1] range (default: [0.05, 0.25, 0.50, 0.75, 0.95]).
        """
        if q is None:
            q = [0.05, 0.25, 0.50, 0.75, 0.95]
        return {p: float(np.percentile(self.terminal_values, p * 100.0)) for p in q}

    def terminal_var(self, confidence_level: float = 0.95) -> float:
        """Computes Value at Risk (VaR) in monetary units at the terminal horizon.

        Expressed as the maximum expected monetary loss at the given confidence level.
        """
        cutoff = float(np.percentile(self.terminal_values, (1.0 - confidence_level) * 100.0))
        loss = self.initial_value - cutoff
        return float(max(0.0, loss))

    def terminal_cvar(self, confidence_level: float = 0.95) -> float:
        """Computes Conditional Value at Risk (CVaR / Expected Shortfall) in monetary units.

        Average monetary loss in the tail beyond the VaR threshold.
        """
        cutoff = float(np.percentile(self.terminal_values, (1.0 - confidence_level) * 100.0))
        tail = self.terminal_values[self.terminal_values <= cutoff]
        if len(tail) == 0:
            return self.terminal_var(confidence_level)
        expected_tail_val = float(np.mean(tail))
        loss = self.initial_value - expected_tail_val
        return float(max(0.0, loss))

    def summary(self, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Generates a comprehensive diagnostic summary of the Monte Carlo simulation."""
        pcts = self.percentiles([0.05, 0.25, 0.50, 0.75, 0.95])
        return {
            "name": self.name,
            "method": self.method,
            "n_simulations": self.n_simulations,
            "horizon_days": self.horizon,
            "initial_value": self.initial_value,
            "daily_mu": self.mu,
            "daily_sigma": self.sigma,
            "annualized_drift": self.mu * 252,
            "annualized_vol": self.sigma * np.sqrt(252),
            "terminal_mean": self.terminal_mean,
            "terminal_median": self.terminal_median,
            "terminal_std": self.terminal_std,
            "terminal_min": self.terminal_min,
            "terminal_max": self.terminal_max,
            "expected_return": (self.terminal_mean - self.initial_value) / self.initial_value,
            "probability_of_loss": self.probability_of_loss,
            f"terminal_var_{int(confidence_level*100)}": self.terminal_var(confidence_level),
            f"terminal_cvar_{int(confidence_level*100)}": self.terminal_cvar(confidence_level),
            "p05": pcts[0.05],
            "p25": pcts[0.25],
            "p50": pcts[0.50],
            "p75": pcts[0.75],
            "p95": pcts[0.95],
        }

    def plot(
        self,
        title: Optional[str] = None,
        max_paths_to_display: int = 150,
        confidence_level: float = 0.95,
        figsize: Tuple[int, int] = (14, 6),
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Any:
        """Visualizes simulation trajectories and terminal value distribution.

        Args:
            title: Custom super-title for the figure.
            max_paths_to_display: Number of sample trajectories to plot (to maintain rendering performance).
            confidence_level: Confidence level for VaR line and intervals.
            figsize: Figure dimensions in inches.
            save_path: Optional path to export the figure (PNG/PDF).
            show: Whether to invoke plt.show().

        Returns:
            Tuple of (matplotlib.figure.Figure, np.ndarray of Axes).
        """
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        plot_title = title or f"Monte Carlo Simulation: {self.name} ({self.n_simulations:,} paths, T={self.horizon}d)"
        fig.suptitle(plot_title, fontsize=14, fontweight="bold", y=0.98)

        # ---------------- Subplot 1: Trajectories ----------------
        display_n = min(self.n_simulations, max_paths_to_display)
        ax1.plot(
            self.time_steps,
            self.trajectories[:, :display_n],
            color="#2563eb",
            alpha=0.10,
            linewidth=0.8,
        )

        # Statistical envelopes across all paths
        median_path = np.median(self.trajectories, axis=1)
        p_lower = np.percentile(self.trajectories, (1.0 - confidence_level) * 100.0, axis=1)
        p_upper = np.percentile(self.trajectories, confidence_level * 100.0, axis=1)

        ax1.plot(self.time_steps, median_path, color="#ea580c", linewidth=2.2, label="Median Path")
        ax1.plot(
            self.time_steps,
            p_upper,
            color="#16a34a",
            linestyle="--",
            linewidth=1.8,
            label=f"{int(confidence_level*100)}th Percentile",
        )
        ax1.plot(
            self.time_steps,
            p_lower,
            color="#dc2626",
            linestyle="--",
            linewidth=1.8,
            label=f"{int((1.0-confidence_level)*100)}th Percentile",
        )
        ax1.axhline(
            self.initial_value,
            color="#475569",
            linestyle=":",
            linewidth=1.5,
            label=f"Initial ({self.initial_value:,.1f})",
        )
        ax1.fill_between(self.time_steps, p_lower, p_upper, color="#2563eb", alpha=0.08)

        ax1.set_title("Simulated Trajectories (Sample Paths & Envelopes)", fontsize=11, fontweight="semibold")
        ax1.set_xlabel("Time Horizon (Trading Days)", fontsize=10)
        ax1.set_ylabel("Value", fontsize=10)
        ax1.grid(True, linestyle=":", alpha=0.6)
        ax1.legend(loc="upper left", fontsize=9, framealpha=0.9)

        # ---------------- Subplot 2: Terminal Distribution ----------------
        n_bins = min(60, max(20, self.n_simulations // 40))
        counts, bins, _ = ax2.hist(
            self.terminal_values,
            bins=n_bins,
            density=True,
            color="#93c5fd",
            edgecolor="#1d4ed8",
            alpha=0.65,
            label="Terminal Distribution",
        )

        var_threshold = float(np.percentile(self.terminal_values, (1.0 - confidence_level) * 100.0))

        ax2.axvline(
            self.initial_value,
            color="#475569",
            linestyle=":",
            linewidth=1.5,
            label=f"Initial: {self.initial_value:,.1f}",
        )
        ax2.axvline(
            self.terminal_mean,
            color="#ea580c",
            linestyle="-",
            linewidth=2.0,
            label=f"Mean: {self.terminal_mean:,.1f}",
        )
        ax2.axvline(
            var_threshold,
            color="#dc2626",
            linestyle="--",
            linewidth=1.8,
            label=f"{int(confidence_level*100)}% VaR Cutoff: {var_threshold:,.1f}",
        )

        # Highlight tail loss region
        tail_bins = bins[bins <= var_threshold]
        if len(tail_bins) > 1:
            ax2.axvspan(bins[0], var_threshold, color="#ef4444", alpha=0.15, label=f"Tail Loss (P={1-confidence_level:.0%})")

        ax2.set_title(f"Terminal Value Distribution (at T={self.horizon})", fontsize=11, fontweight="semibold")
        ax2.set_xlabel("Terminal Value", fontsize=10)
        ax2.set_ylabel("Probability Density", fontsize=10)
        ax2.grid(True, linestyle=":", alpha=0.6)
        ax2.legend(loc="upper right", fontsize=9, framealpha=0.9)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        if show:
            plt.show()

        return fig, (ax1, ax2)


class MonteCarloEngine:
    """Stochastic engine executing Monte Carlo simulations for financial time series."""

    @staticmethod
    def simulate_gbm(
        initial_value: float,
        mu: float,
        sigma: float,
        horizon: int = 252,
        n_simulations: int = 1000,
        dt: float = 1.0,
        seed: Optional[int] = None,
        name: str = "Asset",
    ) -> MonteCarloResult:
        """Simulates single-asset or aggregate portfolio paths using Geometric Brownian Motion (GBM).

        S_{t+1} = S_t * exp((mu - 0.5 * sigma^2) * dt + sigma * sqrt(dt) * Z)

        Args:
            initial_value: Starting asset price or portfolio capital.
            mu: Expected return per time step (daily drift).
            sigma: Standard deviation of returns per time step (daily volatility).
            horizon: Number of forward projection steps (default: 252 days).
            n_simulations: Number of paths to simulate (default: 1,000).
            dt: Time increment per step (default: 1.0).
            seed: Optional random number generator seed for deterministic reproducibility.
            name: Label assigned to the simulation run.

        Returns:
            MonteCarloResult instance containing the simulated trajectories and stats.
        """
        if initial_value <= 0:
            raise ValueError(f"initial_value must be positive, got {initial_value}")
        if horizon <= 0:
            raise ValueError(f"horizon must be positive integer, got {horizon}")
        if n_simulations <= 0:
            raise ValueError(f"n_simulations must be positive integer, got {n_simulations}")
        if sigma < 0:
            raise ValueError(f"sigma must be non-negative, got {sigma}")

        rng = np.random.default_rng(seed)

        # Drift and diffusion components
        drift = (mu - 0.5 * (sigma**2)) * dt
        diffusion = sigma * np.sqrt(dt)

        # Generate Gaussian shocks: shape (horizon, n_simulations)
        shocks = rng.standard_normal(size=(horizon, n_simulations))
        daily_log_returns = drift + diffusion * shocks

        # Cumulative log returns
        cum_log_returns = np.vstack([
            np.zeros((1, n_simulations)),
            np.cumsum(daily_log_returns, axis=0),
        ])

        # Exponentiate to obtain price paths: S_t = S_0 * exp(sum(r))
        trajectories = initial_value * np.exp(cum_log_returns)

        return MonteCarloResult(
            name=name,
            trajectories=trajectories,
            horizon=horizon,
            n_simulations=n_simulations,
            initial_value=initial_value,
            mu=mu,
            sigma=sigma,
            method="gbm",
        )

    @staticmethod
    def simulate_multivariate_gbm(
        initial_capital: float,
        weights: np.ndarray,
        mu_vector: np.ndarray,
        cov_matrix: np.ndarray,
        horizon: int = 252,
        n_simulations: int = 1000,
        dt: float = 1.0,
        seed: Optional[int] = None,
        name: str = "Portfolio",
    ) -> MonteCarloResult:
        """Simulates portfolio paths using correlated multivariate Geometric Brownian Motion.

        Generates correlated Gaussian shocks using the Cholesky decomposition of the
        asset covariance matrix: Sigma = L * L^T.

        Args:
            initial_capital: Baseline portfolio capital.
            weights: 1D array of asset weights (normalized, sum=1.0).
            mu_vector: 1D array of daily expected returns for each asset.
            cov_matrix: 2D covariance matrix of daily asset returns.
            horizon: Number of trading steps to project.
            n_simulations: Number of Monte Carlo trajectories.
            dt: Time increment per step (default: 1.0).
            seed: Seed for random number generator.
            name: Descriptive label for the portfolio.

        Returns:
            MonteCarloResult instance representing the simulated portfolio wealth paths.
        """
        n_assets = len(weights)
        if cov_matrix.shape != (n_assets, n_assets):
            raise ValueError(
                f"Covariance matrix shape {cov_matrix.shape} does not match "
                f"number of assets ({n_assets})."
            )

        rng = np.random.default_rng(seed)

        # Cholesky factor L such that L @ L.T = cov_matrix
        try:
            L = np.linalg.cholesky(cov_matrix * dt)
        except np.linalg.LinAlgError:
            # Handle potential numerical non-positive-definiteness via eigenvalue clipping
            eigvals, eigvecs = np.linalg.eigh(cov_matrix * dt)
            eigvals = np.maximum(eigvals, 1e-8)
            clean_cov = eigvecs @ np.diag(eigvals) @ eigvecs.T
            L = np.linalg.cholesky(clean_cov)

        vol_vector = np.sqrt(np.diag(cov_matrix))
        drift_vector = (mu_vector - 0.5 * (vol_vector**2)) * dt

        # Trajectories array for total portfolio wealth
        portfolio_wealth = np.zeros((horizon + 1, n_simulations))
        portfolio_wealth[0, :] = initial_capital

        # Initial capital allocation per asset
        asset_wealth = np.zeros((n_assets, n_simulations))
        for i in range(n_assets):
            asset_wealth[i, :] = initial_capital * weights[i]

        for t in range(1, horizon + 1):
            # Uncorrelated shocks ~ N(0, 1): shape (n_assets, n_simulations)
            uncorrelated = rng.standard_normal(size=(n_assets, n_simulations))
            # Correlated shocks via Cholesky
            correlated_shocks = L @ uncorrelated

            # Asset log returns for step t
            step_log_ret = drift_vector[:, np.newaxis] + correlated_shocks
            asset_wealth = asset_wealth * np.exp(step_log_ret)

            # Portfolio total wealth is sum of asset wealth
            portfolio_wealth[t, :] = np.sum(asset_wealth, axis=0)

        # Implied portfolio parameters
        portfolio_mu = float(np.sum(weights * mu_vector))
        portfolio_sigma = float(np.sqrt(weights.T @ cov_matrix @ weights))

        return MonteCarloResult(
            name=name,
            trajectories=portfolio_wealth,
            horizon=horizon,
            n_simulations=n_simulations,
            initial_value=initial_capital,
            mu=portfolio_mu,
            sigma=portfolio_sigma,
            method="multivariate_gbm",
        )

