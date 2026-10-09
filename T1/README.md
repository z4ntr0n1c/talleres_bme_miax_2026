# Taller 1 — Kit de Extracción de Datos Financieros / Financial Data Extraction Toolkit

> 🇪🇸 [Español](#español) · 🇬🇧 [English](#english)

---

## Español

> **Máster MIAX BME · Edición 15**  
> Bloque B1 · Taller 1: Arquitectura, extracción de datos, modelado de carteras, simulación estocástica y reportes cuantitativos

### Descripción

Este proyecto implementa una toolbox profesional en Python para la ingesta, estandarización y análisis de información bursátil y macroeconómica, así como la gestión de carteras de inversión, simulación estocástica de **Monte Carlo** y generación de reportes cuantitativos y visuales.

El diseño sigue una arquitectura modular y desacoplada mediante patrones de diseño orientados a objetos y **DataClasses**, separando estrictamente la capa de extracción de la capa de análisis, modelos, preprocesado y motores de diagnóstico.

### Estructura del repositorio

```
T1/
├── doc/                              # Guías y diapositivas del taller (PDF/HTML)
│   ├── Taller_B1_T1.pdf
│   ├── guia_taller_parte1_git_ssh.*  # Parte 1: Configuración Git & SSH
│   └── guia_taller_parte2.*          # Parte 2: Arquitectura y extracción
├── examples/
│   ├── test_fetch.py                 # Extracción individual y batch (Yahoo)
│   ├── test_fetch_fred.py            # Extracción macroeconómica (FRED)
│   ├── test_portfolio.py             # Creación y métricas de Cartera (Portfolio)
│   ├── test_monte_carlo.py           # Motor Monte Carlo y gráficos estocásticos
│   ├── test_reports_and_cleaning.py  # Limpieza, validación, reporte Markdown y dashboard
│   ├── plots/                        # Gráficos generados (conos MC y dashboard analítico)
│   └── reports/                      # Informes cuantitativos generados en Markdown
├── src/
│   └── toolkit/
│       ├── __init__.py               # Exportaciones de primer nivel
│       ├── data/                     # Capa de ingesta y conectores de mercado
│       │   ├── base.py               # Interfaz abstracta (BaseDataExtractor)
│       │   ├── yahoo.py              # Extractor Yahoo Finance (acciones/índices)
│       │   ├── fred.py               # Extractor FRED (datos macroeconómicos)
│       │   └── __init__.py
│       ├── models/                   # Capa de modelado cuantitativo
│       │   ├── series.py             # DataClass PriceSeries (series individuales)
│       │   ├── portfolio.py          # DataClass Portfolio (agregación, riesgos, reportes)
│       │   ├── monte_carlo.py        # Motor Monte Carlo y DataClass MonteCarloResult
│       │   └── __init__.py
│       └── utils/                    # Capa de limpieza, alineación y validación
│           ├── cleaning.py           # Gestión de NaNs, forward-fill y alineación multicalendario
│           ├── validation.py         # Validación estructural estricta de invariantes
│           └── __init__.py
├── pyproject.toml
├── requirements.txt
└── setup.py
```

### Componentes principales

#### 1. `PriceSeries` — Modelo de series temporales (`models/series.py`)

Un `dataclass` interoperable que estandariza las series de cualquier fuente de datos:

| Atributo / Método | Tipo | Descripción |
|---|---|---|
| `ticker` | `str` | Símbolo o identificador del activo (en mayúsculas) |
| `asset_type` | `str` | Clasificación semántica (`'equity'`, `'index'`, `'macro'`, etc.) |
| `data` | `pd.DataFrame` | Datos indexados por fecha con columnas `'close'` y `'returns'` |
| `mean_return` | `float` | Retorno diario medio (auto-calculado en `__post_init__`) |
| `std_return` | `float` | Desviación típica diaria (auto-calculada en `__post_init__`) |
| `annualized_return()` | `float` | Retorno anualizado compuesto geométrico |
| `annualized_volatility()` | `float` | Volatilidad anualizada ($\sigma \times \sqrt{252}$) |
| `sharpe_ratio()` | `float` | Ratio de Sharpe anualizado |
| `max_drawdown()` | `float` | Caída máxima histórica (*Peak-to-Trough*) |
| `value_at_risk(0.95)` | `float` | VaR histórico diario al 95% de confianza |
| `simulate_montecarlo()` | `MonteCarloResult` | Simulación estocástica de trayectorias (GBM) |
| `plot_montecarlo()` | `Figure` | Genera y muestra visualmente las trayectorias y distribución |

#### 2. `Portfolio` — Modelo de Cartera de Inversión (`models/portfolio.py`)

Un `dataclass` que agrega múltiples activos `PriceSeries`, gestiona sus ponderaciones, valida los datos y calcula métricas de riesgo y rendimiento de forma automática:

| Atributo / Método | Tipo | Descripción |
|---|---|---|
| `assets` | `List[PriceSeries]` | Lista de activos que componen la cartera |
| `weights` | `Dict / List / None` | Ponderaciones (si es `None`, asigna pesos equiponderados $1/N$) |
| `weights_dict` | `Dict[str, float]` | Diccionario normalizado que suma 1.0 (auto-calculado) |
| `returns_df` | `pd.DataFrame` | Matriz alineada por fecha de retornos individuales (auto-calculado) |
| `portfolio_returns` | `pd.Series` | Serie temporal de retornos diarios de la cartera $R_p = \sum w_i R_i$ |
| `mean_return` / `std_return` | `float` | Media y volatilidad diaria de la cartera (auto-calculadas) |
| `covariance_matrix` | `pd.DataFrame` | Matriz de covarianza diaria entre activos |
| `correlation_matrix` | `pd.DataFrame` | Matriz de correlación diaria entre activos |
| `annualized_return()` | `float` | Rentabilidad anualizada de la cartera |
| `annualized_volatility()` | `float` | Volatilidad anualizada de la cartera |
| `sharpe_ratio()` | `float` | Ratio de Sharpe de la cartera |
| `drawdown_series()` | `pd.Series` | Serie histórica de *drawdown* relativo al máximo acumulado |
| `max_drawdown()` | `float` | Caída máxima acumulada |
| `value_at_risk(0.95)` | `float` | Valor en Riesgo (VaR) diario al 95% (métodos `'historical'` y `'parametric'`) |
| `conditional_value_at_risk()` | `float` | CVaR / Expected Shortfall diario al 95% |
| `summary()` | `Dict[str, Any]` | Resumen exhaustivo de métricas y diagnóstico de la cartera |
| `simulate_montecarlo()` | `MonteCarloResult` | Simulación estocástica (multivariante correlada o agregada) |
| `plot_montecarlo()` | `Figure` | Visualización en pantalla de trayectorias y distribución terminal |
| `report()` | `str` (Markdown) | Genera informe formal estructurado en Markdown con diagnósticos y alertas de riesgo |
| `plots_report()` | `Figure` (Dashboard) | Genera panel gráfico 2x2: rendimiento comparado, drawdown, correlación y distribución VaR |

#### 3. Motor de Simulación Monte Carlo (`models/monte_carlo.py`)

- **`MonteCarloEngine`**: Motor estocástico con dos modelos de difusión:
  1. *Movimiento Browniano Geométrico (GBM)* univariante para activos individuales o cartera global agregada.
  2. *GBM Multivariante Correlado* para carteras mediante descomposición de Cholesky ($\boldsymbol{\Sigma} = \boldsymbol{L}\boldsymbol{L}^T$) sobre la matriz empírica de covarianzas.
- **`MonteCarloResult`**: Objeto con trayectorias ($S_t$), percentiles temporales ($5\%$, $50\%$, $95\%$), capital esperado, probabilidad de pérdida, VaR terminal y CVaR terminal monetarios.
- **Visualización integrada**: Gráficos duales con cono de trayectorias y distribución terminal con cortes de VaR.

#### 4. Preprocesado, Limpieza y Validación de Inputs (`utils/`)

- **`utils/cleaning.py`**:
  - `clean_missing_values(df, method='ffill')`: Tratamiento robusto de NaNs (forward-fill con límite de huecos para festivos bursátiles, backward-fill para el arranque o eliminación).
  - `align_calendar_series(series_map, join_method='inner')`: Sincronización temporal entre calendarios de diferentes bolsas (NYSE vs. BME).
  - `filter_anomalous_returns(series)`: Detección y filtrado de anomalías o splits no ajustados.
- **`utils/validation.py` (Política de Validación Estricta)**:
  - *Justificación*: En finanzas cuantitativas, la admisión de inputs arbitrarios corrompe las matrices de covarianza, genera división por cero en precios no positivos y distorsiona el Sharpe ratio. Por ello se aplica una política de **fallo temprano (*fail-fast*)**.
  - `validate_price_dataframe(df)`: Exige `DatetimeIndex`, orden monotónico estricto, sin duplicados temporales, presencia de columna `'close'` numérica y **precios estrictamente positivos (> 0)**.
  - `validate_portfolio_weights(weights, tickers)`: Valida dimensiones, ausencia de NaNs/infinitos, restricciones de cortos y normalización exacta a 1.0.

### Instalación

#### 1. Crear y activar el entorno virtual

```bash
cd T1
python -m venv .venv
source .venv/bin/activate
```

#### 2. Instalar el paquete en modo editable

```bash
pip install -e src/
```

O instalar las dependencias directamente:

```bash
pip install -r requirements.txt
```

### Ejemplos de uso

#### Ingesta, Cartera, Reporte Markdown y Dashboard Visual

```python
from toolkit.data import YahooFinanceExtractor
from toolkit.models import Portfolio

# 1. Ingesta de datos de mercado
yahoo = YahooFinanceExtractor()
assets = yahoo.fetch_batch(
    tickers=["AAPL", "MSFT", "SAN.MC", "^IBEX"],
    start="2024-01-01",
    end="2025-01-01"
)

# 2. Creación y validación de la Cartera
weights = {"AAPL": 0.40, "MSFT": 0.30, "SAN.MC": 0.15, "^IBEX": 0.15}
portfolio = Portfolio(assets=assets, weights=weights, initial_capital=100000.0)

# 3. Generación de informe cuantitativo en Markdown (.report())
md_report = portfolio.report(
    risk_free_rate=0.03,
    output_path="examples/reports/portfolio_report.md"
)
print("Informe Markdown generado con éxito.")

# 4. Generación de Dashboard visual 2x2 (.plots_report())
portfolio.plots_report(
    save_path="examples/plots/portfolio_dashboard.png",
    show=False
)
print("Dashboard gráfico de 4 paneles guardado.")

# 5. Simulación de Monte Carlo
mc = portfolio.simulate_montecarlo(n_simulations=2000, horizon=252)
mc.plot(save_path="examples/plots/mc_portfolio.png", show=False)
```

Ejecuta los scripts de prueba completos:
- `python examples/test_fetch.py`
- `python examples/test_fetch_fred.py`
- `python examples/test_portfolio.py`
- `python examples/test_monte_carlo.py`
- `python examples/test_reports_and_cleaning.py`

### Dependencias

| Paquete | Versión mínima | Propósito |
|---|---|---|
| `yfinance` | ≥ 0.2.36 | Descarga de acciones e índices bursátiles |
| `pandas` | ≥ 2.0.0 | Manipulación, limpieza y alineación de series temporales |
| `numpy` | ≥ 1.24.0 | Operaciones algebraicas, Cholesky y simulación vectorizada |
| `matplotlib` | ≥ 3.7.0 | Visualizaciones gráficas, dashboards analíticos y conos MC |
| `pandas-datareader` | ≥ 0.10.0 | Conexión con la API de FRED (datos macroeconómicos) |

### Documentación

Las guías del taller se encuentran en [`doc/`](doc/):
- **Parte 1** — Configuración de Git y SSH (`guia_taller_parte1_git_ssh.pdf`)
- **Parte 2** — Arquitectura y extracción de datos (`guia_taller_parte2.pdf`)
- **Diapositivas** — `Taller_B1_T1.pdf`

---

## English

> **Master MIAX BME · Edition 15**  
> Block B1 · Workshop 1: Architecture, data extraction, portfolio modeling, Monte Carlo simulation and reporting

### Overview

This project implements a professional Python toolbox for fetching, standardizing, and analyzing financial and macroeconomic data, as well as quantitative investment portfolio modeling, **Monte Carlo** stochastic simulation, automated Markdown reporting, and visual diagnostics dashboards.

The architecture emphasizes clean object-oriented design and **DataClasses**, cleanly decoupling the data ingestion layer from analytical models, data pre-processing, validation, and stochastic diffusion engines.

### Repository Structure

```
T1/
├── doc/                              # Workshop guides & slides (PDF/HTML)
│   ├── Taller_B1_T1.pdf
│   ├── guia_taller_parte1_git_ssh.*  # Part 1: Git & SSH setup
│   └── guia_taller_parte2.*          # Part 2: Architecture & extraction
├── examples/
│   ├── test_fetch.py                 # Single & batch fetch (Yahoo)
│   ├── test_fetch_fred.py            # Macro data extraction (FRED)
│   ├── test_portfolio.py             # Portfolio creation & risk metrics
│   ├── test_monte_carlo.py           # Monte Carlo engine & stochastic charts
│   ├── test_reports_and_cleaning.py  # Cleaning, validation, Markdown report & dashboard
│   ├── plots/                        # Exported simulation & dashboard figures
│   └── reports/                      # Exported Markdown quantitative reports
├── src/
│   └── toolkit/
│       ├── __init__.py               # Top-level exports
│       ├── data/                     # Ingestion layer & market connectors
│       │   ├── base.py               # Abstract interface (BaseDataExtractor)
│       │   ├── yahoo.py              # Yahoo Finance extractor (equities/indices)
│       │   ├── fred.py               # FRED extractor (macroeconomic series)
│       │   └── __init__.py
│       ├── models/                   # Quantitative modeling layer
│       │   ├── series.py             # PriceSeries DataClass (single series)
│       │   ├── portfolio.py          # Portfolio DataClass (aggregation, risk, reports)
│       │   ├── monte_carlo.py        # Monte Carlo engine & MonteCarloResult DataClass
│       │   └── __init__.py
│       └── utils/                    # Data cleaning, calendar alignment & validation
│           ├── cleaning.py           # Missing value imputation & multi-exchange alignment
│           ├── validation.py         # Strict structural invariant enforcement
│           └── __init__.py
├── pyproject.toml
├── requirements.txt
└── setup.py
```

### Key Components

#### 1. `PriceSeries` — Single Asset Data Model (`models/series.py`)

A standardized `dataclass` modeling price series from any source:

| Attribute / Method | Type | Description |
|---|---|---|
| `ticker` | `str` | Asset symbol (uppercased) |
| `asset_type` | `str` | Semantic type (`'equity'`, `'index'`, `'macro'`, etc.) |
| `data` | `pd.DataFrame` | Date-indexed DataFrame with `'close'` and `'returns'` |
| `mean_return` | `float` | Daily mean return (auto-computed in `__post_init__`) |
| `std_return` | `float` | Daily return standard deviation (auto-computed in `__post_init__`) |
| `annualized_return()` | `float` | Compound annualized return |
| `annualized_volatility()` | `float` | Annualized volatility ($\sigma \times \sqrt{252}$) |
| `sharpe_ratio()` | `float` | Annualized Sharpe ratio |
| `max_drawdown()` | `float` | Maximum peak-to-trough drawdown |
| `value_at_risk(0.95)` | `float` | Daily historical 95% Value at Risk |
| `simulate_montecarlo()` | `MonteCarloResult` | Stochastic trajectory simulation (GBM) |
| `plot_montecarlo()` | `Figure` | Trajectory and terminal distribution visualization |

#### 2. `Portfolio` — Investment Portfolio Model (`models/portfolio.py`)

A `dataclass` aggregating multiple `PriceSeries` assets, managing weights, validating inputs, and automatically computing statistical and risk metrics:

| Attribute / Method | Type | Description |
|---|---|---|
| `assets` | `List[PriceSeries]` | List of asset series in the portfolio |
| `weights` | `Dict / List / None` | Allocations (defaults to equal weighting $1/N$ if `None`) |
| `weights_dict` | `Dict[str, float]` | Normalized weight dictionary summing to 1.0 |
| `returns_df` | `pd.DataFrame` | Aligned daily return matrix across all assets |
| `portfolio_returns` | `pd.Series` | Daily portfolio return series $R_p = \sum w_i R_i$ |
| `mean_return` / `std_return` | `float` | Daily mean and volatility of portfolio returns |
| `covariance_matrix` | `pd.DataFrame` | Daily return covariance matrix |
| `correlation_matrix` | `pd.DataFrame` | Daily return correlation matrix |
| `annualized_return()` | `float` | Annualized portfolio return |
| `annualized_volatility()` | `float` | Annualized portfolio volatility |
| `sharpe_ratio()` | `float` | Annualized Sharpe ratio |
| `drawdown_series()` | `pd.Series` | Underwater drawdown series relative to cumulative peak |
| `max_drawdown()` | `float` | Maximum portfolio drawdown |
| `value_at_risk(0.95)` | `float` | Daily 95% Value at Risk (`'historical'` and `'parametric'`) |
| `conditional_value_at_risk()` | `float` | Daily 95% CVaR / Expected Shortfall |
| `summary()` | `Dict[str, Any]` | Comprehensive portfolio metric summary |
| `simulate_montecarlo()` | `MonteCarloResult` | Stochastic simulation (multivariate correlated or aggregate) |
| `plot_montecarlo()` | `Figure` | Screen rendering of trajectories and terminal distribution |
| `report()` | `str` (Markdown) | Generates structured Markdown report with executive summary & risk flags |
| `plots_report()` | `Figure` (Dashboard) | Generates 2x2 visual dashboard: relative growth, drawdown, correlation & return distribution |

#### 3. Monte Carlo Simulation Engine (`models/monte_carlo.py`)

- **`MonteCarloEngine`**: Stochastic simulation engine featuring:
  1. *Geometric Brownian Motion (GBM)* for single assets or aggregate portfolio drift/volatility.
  2. *Correlated Multivariate GBM* utilizing Cholesky decomposition of the empirical asset covariance matrix ($\boldsymbol{\Sigma} = \boldsymbol{L}\boldsymbol{L}^T$).
- **`MonteCarloResult`**: Container class storing full path trajectories ($S_t$), percentiles ($5\%$, $50\%$, $95\%$), expected capital, probability of loss, monetary terminal VaR, and terminal CVaR.

#### 4. Preprocessing, Cleaning & Input Validation (`utils/`)

- **`utils/cleaning.py`**:
  - `clean_missing_values(df, method='ffill')`: Missing value imputation with forward-fill limits suited for market holidays.
  - `align_calendar_series(series_map, join_method='inner')`: Synchronizes differing trading calendars across exchanges.
- **`utils/validation.py` (Strict Input Policy)**:
  - *Justification*: Unconstrained inputs cause silent failures in quantitative finance (e.g., negative prices producing NaN returns, non-positive definite covariances). Strict validation enforces fail-fast integrity.
  - `validate_price_dataframe(df)`: Enforces `DatetimeIndex`, monotonic order, uniqueness, required numeric `'close'`, and strictly positive prices.
  - `validate_portfolio_weights(weights, tickers)`: Enforces dimension match, finite values, short constraints, and exact normalization.

### Installation

```bash
cd T1
python -m venv .venv
source .venv/bin/activate
pip install -e src/
```

### Usage

```python
from toolkit.data import YahooFinanceExtractor
from toolkit.models import Portfolio

yahoo = YahooFinanceExtractor()
assets = yahoo.fetch_batch(["AAPL", "MSFT", "SAN.MC"], start="2024-01-01", end="2025-01-01")

portfolio = Portfolio(assets=assets, weights={"AAPL": 0.5, "MSFT": 0.3, "SAN.MC": 0.2})

# 1. Generate Markdown Report
report_md = portfolio.report(risk_free_rate=0.03, output_path="examples/reports/portfolio_report.md")

# 2. Generate 4-panel visual dashboard
portfolio.plots_report(save_path="examples/plots/portfolio_dashboard.png", show=False)
```

Run test examples:
- `python examples/test_fetch.py`
- `python examples/test_fetch_fred.py`
- `python examples/test_portfolio.py`
- `python examples/test_monte_carlo.py`
- `python examples/test_reports_and_cleaning.py`

### Dependencies

| Package | Min. Version | Purpose |
|---|---|---|
| `yfinance` | ≥ 0.2.36 | Equity and index price data |
| `pandas` | ≥ 2.0.0 | Time series alignment and data manipulation |
| `numpy` | ≥ 1.24.0 | Vectorized algebra, Cholesky decomposition, and simulations |
| `matplotlib` | ≥ 3.7.0 | Plotting trajectories, distributions, and analytics dashboard |
| `pandas-datareader` | ≥ 0.10.0 | FRED macroeconomic API client |

### Documentation

Workshop guides available in [`doc/`](doc/):
- **Part 1** — Git & SSH setup (`guia_taller_parte1_git_ssh.pdf`)
- **Part 2** — Architecture & data extraction (`guia_taller_parte2.pdf`)
- **Slides** — `Taller_B1_T1.pdf`
