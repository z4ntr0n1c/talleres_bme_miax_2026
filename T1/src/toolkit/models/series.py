from dataclasses import dataclass, field
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