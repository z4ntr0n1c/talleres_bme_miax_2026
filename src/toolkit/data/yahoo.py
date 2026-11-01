"""Yahoo Finance data extractor via ``yfinance``."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import date

import pandas as pd
import yfinance as yf

from ..models.series import PriceSeries
from .base import BaseDataExtractor

logger = logging.getLogger(__name__)


class YahooFinanceExtractor(BaseDataExtractor):
    """Data extractor implementation using Yahoo Finance (``yfinance``)."""

    def fetch_series(
        self,
        ticker: str,
        start: date | str,
        end: date | str | None = None,
        asset_type: str = "equity",
    ) -> PriceSeries:
        """Fetch and standardize historical price data for a single ticker.

        Args:
            ticker: Yahoo Finance symbol (e.g. ``"AAPL"``, ``"SAN.MC"``, ``"^IBEX"``).
            start: Start date (``YYYY-MM-DD`` or ``date``).
            end: End date (exclusive; ``None`` defaults to today).
            asset_type: Semantic label for the asset (default: ``"equity"``).

        Returns:
            A standardized :class:`PriceSeries`.

        Raises:
            ValueError: If Yahoo Finance returns no data for the ticker.
        """
        raw_df = yf.download(
            tickers=ticker,
            start=str(start),
            end=str(end) if end is not None else None,
            progress=False,
            auto_adjust=True,
        )

        if raw_df is None or raw_df.empty:
            raise ValueError(f"No price data found for ticker '{ticker}'.")

        standardized_df = self._standardize_dataframe(raw_df)
        logger.info("Yahoo %s: %d observations", ticker.upper(), len(standardized_df))
        return PriceSeries(
            ticker=ticker.upper(),
            asset_type=asset_type,
            data=standardized_df,
        )

    def fetch_batch(
        self,
        tickers: Sequence[str],
        start: date | str,
        end: date | str | None = None,
        asset_type: str = "equity",
    ) -> list[PriceSeries]:
        """Fetch multiple tickers simultaneously and standardize each into a :class:`PriceSeries`.

        Args:
            tickers: Sequence of Yahoo Finance symbols.
            start: Start date (``YYYY-MM-DD`` or ``date``).
            end: End date (exclusive; ``None`` defaults to today).
            asset_type: Semantic label applied to all tickers (default: ``"equity"``).

        Returns:
            List of :class:`PriceSeries` for all successfully downloaded tickers.
        """
        ticker_list = list(tickers)
        if not ticker_list:
            return []

        if len(ticker_list) == 1:
            return [self.fetch_series(ticker_list[0], start=start, end=end, asset_type=asset_type)]

        batch_df = yf.download(
            tickers=ticker_list,
            start=str(start),
            end=str(end) if end is not None else None,
            group_by="ticker",
            progress=False,
            auto_adjust=True,
        )

        if batch_df is None or batch_df.empty:
            return []

        results: list[PriceSeries] = []
        for ticker in ticker_list:
            try:
                ticker_df = batch_df[ticker].dropna(how="all")
            except KeyError:
                logger.warning("Yahoo Finance: ticker '%s' not found in batch response.", ticker)
                continue

            if ticker_df.empty:
                logger.warning("Yahoo Finance: no price rows returned for '%s'.", ticker)
                continue

            std_df = self._standardize_dataframe(ticker_df)
            results.append(
                PriceSeries(
                    ticker=ticker.upper(),
                    asset_type=asset_type,
                    data=std_df,
                )
            )

        logger.info("Yahoo batch: %d/%d tickers loaded", len(results), len(ticker_list))
        return results

    @staticmethod
    def _standardize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to lowercase and calculate daily returns."""
        out = df.copy()
        if isinstance(out.columns, pd.MultiIndex):
            out.columns = [str(col[0]).lower() for col in out.columns]
        else:
            out.columns = [str(col).lower() for col in out.columns]

        return BaseDataExtractor._normalize_close_dataframe(out, close_col="close")
