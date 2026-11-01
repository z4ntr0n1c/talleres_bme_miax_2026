"""Offline unit test suite for ``toolkit`` (no network access required).

Compatible with both ``pytest`` and standard ``python -m unittest``.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

_SRC_DIR = str(Path(__file__).resolve().parents[1] / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from toolkit import (
    FREDExtractor,
    MonteCarloEngine,
    Portfolio,
    PriceSeries,
    ValidationError,
    YahooFinanceExtractor,
    align_calendar_series,
    clean_missing_values,
    filter_anomalous_returns,
    setup_logging,
    validate_portfolio_weights,
    validate_price_dataframe,
)

matplotlib.use("Agg")


def _make_synthetic_assets() -> list[PriceSeries]:
    """Build two deterministic synthetic PriceSeries without network calls."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    close_a = 100.0 * np.cumprod(1.0 + rng.normal(0.0008, 0.012, size=len(dates)))
    close_b = 50.0 * np.cumprod(1.0 + rng.normal(0.0005, 0.010, size=len(dates)))

    df_a = pd.DataFrame({"close": close_a}, index=dates)
    df_b = pd.DataFrame({"close": close_b}, index=dates)
    return [
        PriceSeries(ticker="aapl", asset_type="equity", data=df_a),
        PriceSeries(ticker="msft", asset_type="equity", data=df_b),
    ]


class TestToolkitOffline(unittest.TestCase):
    """Offline test suite for the T1 financial toolkit."""

    def test_setup_logging_is_idempotent(self) -> None:
        logger = setup_logging()
        setup_logging()
        self.assertEqual(len(logger.handlers), 1)

    def test_price_series_does_not_mutate_input_dataframe(self) -> None:
        dates = pd.date_range("2024-01-01", periods=10, freq="B")
        raw_df = pd.DataFrame({"close": np.linspace(100.0, 110.0, 10)}, index=dates)
        series = PriceSeries(ticker="aapl", asset_type="equity", data=raw_df)

        self.assertNotIn("returns", raw_df.columns)
        self.assertIn("returns", series.data.columns)
        self.assertEqual(series.ticker, "AAPL")
        self.assertEqual(len(series), 9)
        self.assertGreater(series.annualized_return(), 0.0)
        self.assertGreater(series.annualized_volatility(), 0.0)
        self.assertNotEqual(series.value_at_risk(0.95, method="parametric"), 0.0)
        self.assertLessEqual(series.conditional_value_at_risk(0.95), series.value_at_risk(0.95))

    def test_standardize_dataframes(self) -> None:
        dates = pd.date_range("2024-01-01", periods=6, freq="B")
        yahoo_raw = pd.DataFrame({"Close": [100, 101, 102, 103, 104, 105]}, index=dates)
        std_yahoo = YahooFinanceExtractor._standardize_dataframe(yahoo_raw)
        self.assertEqual(list(std_yahoo.columns), ["close", "returns"])
        self.assertEqual(std_yahoo.index.name, "date")

        fred_raw = pd.DataFrame({"DFF": [5.0, 5.1, 5.2, 5.1, 5.3, 5.4]}, index=dates)
        std_fred = FREDExtractor._standardize_dataframe(fred_raw, "DFF")
        self.assertEqual(list(std_fred.columns), ["close", "returns"])

    def test_validation_invariants(self) -> None:
        dates = pd.date_range("2024-01-01", periods=6, freq="B")
        valid_df = pd.DataFrame({"close": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]}, index=dates)
        self.assertTrue(validate_price_dataframe(valid_df))

        neg_df = valid_df.copy()
        neg_df.iloc[1, 0] = -1.0
        with self.assertRaises(ValidationError):
            validate_price_dataframe(neg_df)

        weights = validate_portfolio_weights([30, 70], ["AAPL", "MSFT"])
        self.assertEqual(weights, {"AAPL": 0.3, "MSFT": 0.7})

    def test_cleaning_and_alignment(self) -> None:
        dates = pd.date_range("2024-01-01", periods=4, freq="D")
        s1 = pd.Series([100.0, np.nan, 102.0, 103.0], index=dates)
        s2 = pd.Series([50.0, 51.0, np.nan, 53.0], index=dates)

        inner = align_calendar_series({"A": s1, "B": s2}, join_method="inner")
        self.assertEqual(len(inner), 2)

        outer = align_calendar_series({"A": s1, "B": s2}, join_method="outer_ffill")
        self.assertEqual(len(outer), 4)

        df_cleaned = clean_missing_values(pd.DataFrame({"close": s1}), method="ffill")
        self.assertFalse(df_cleaned["close"].isna().any())

        clean_ret, anomalies = filter_anomalous_returns(
            pd.Series([0.01, -0.02, 2.5]), max_abs_return=1.0
        )
        self.assertEqual(len(clean_ret), 2)
        self.assertEqual(len(anomalies), 1)

    def test_portfolio_metrics_and_reports(self) -> None:
        assets = _make_synthetic_assets()
        portfolio = Portfolio(
            assets=assets,
            weights={"AAPL": 0.6, "MSFT": 0.4},
            name="Synthetic Test Portfolio",
            initial_capital=10_000.0,
        )

        self.assertEqual(len(portfolio), 2)
        self.assertEqual(portfolio["aapl"].ticker, "AAPL")
        self.assertEqual(portfolio.weights_dict, {"AAPL": 0.6, "MSFT": 0.4})
        self.assertLess(portfolio.value_at_risk(0.95, method="parametric"), 0.0)
        self.assertLessEqual(
            portfolio.conditional_value_at_risk(0.95), portfolio.value_at_risk(0.95)
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            md_path = tmp_path / "reports" / "report.md"
            md_text = portfolio.report(risk_free_rate=0.02, output_path=md_path)
            self.assertTrue(md_path.is_file())
            self.assertIn("Synthetic Test Portfolio", md_text)

            plot_path = tmp_path / "plots" / "dashboard.png"
            portfolio.plots_report(save_path=plot_path, show=False)
            self.assertTrue(plot_path.is_file())

    def test_monte_carlo_reproducibility(self) -> None:
        assets = _make_synthetic_assets()
        portfolio = Portfolio(assets=assets, initial_capital=10_000.0)

        mc1 = portfolio.simulate_montecarlo(
            n_simulations=200, horizon=30, seed=123, multivariate=True
        )
        mc2 = portfolio.simulate_montecarlo(
            n_simulations=200, horizon=30, seed=123, multivariate=True
        )
        self.assertTrue(np.allclose(mc1.trajectories, mc2.trajectories))
        self.assertEqual(mc1.trajectories.shape, (31, 200))

        mc_agg = MonteCarloEngine.simulate_gbm(
            initial_value=100.0, mu=0.0005, sigma=0.01, horizon=20, n_simulations=100, seed=7
        )
        with tempfile.TemporaryDirectory() as tmp:
            mc_plot = Path(tmp) / "mc.png"
            mc_agg.plot(save_path=mc_plot, show=False)
            self.assertTrue(mc_plot.is_file())


if __name__ == "__main__":
    unittest.main()

