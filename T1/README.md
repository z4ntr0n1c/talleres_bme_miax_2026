# Taller 1 — Kit de Extracción de Datos Financieros / Financial Data Extraction Toolkit

> 🇪🇸 [Español](#español) · 🇬🇧 [English](#english)

---

## Español

> **Máster MIAX BME · Edición 15**  
> Bloque B1 · Taller 1: Arquitectura, extracción de datos y modelado de carteras

### Descripción

Este proyecto implementa una toolbox profesional en Python para la ingesta, estandarización y análisis de información bursátil y macroeconómica, así como la gestión y modelado cuantitativo de carteras de inversión.

El diseño sigue una arquitectura modular y desacoplada mediante patrones de diseño orientados a objetos y **DataClasses**, separando estrictamente la capa de extracción de la capa de análisis y modelos.

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
│   └── test_portfolio.py             # Creación y métricas de Cartera (Portfolio)
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
│       │   ├── portfolio.py          # DataClass Portfolio (agregación y riesgos)
│       │   └── __init__.py
│       └── utils/                    # Limpieza y utilidades auxiliares
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

#### 2. `Portfolio` — Modelo de Cartera de Inversión (`models/portfolio.py`)

Un `dataclass` que agrega múltiples activos `PriceSeries`, gestiona sus ponderaciones y calcula métricas de riesgo y rendimiento de forma automática:

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

#### 3. Extractores de datos (`data/`)

- **`BaseDataExtractor`** (`data/base.py`): Interfaz abstracta que exige la implementación de `fetch_series()` y `fetch_batch()`.
- **`YahooFinanceExtractor`** (`data/yahoo.py`): Conector a Yahoo Finance con soporte para descargas individuales o masivas en un solo request y normalización automática.
- **`FREDExtractor`** (`data/fred.py`): Conector al sistema FRED de la Reserva Federal (tipos de interés, VIX, petróleo, inflación) devolviendo objetos compatibles `PriceSeries`.

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

#### Ingesta de datos y creación de cartera equiponderada

```python
from toolkit.data import YahooFinanceExtractor, FREDExtractor
from toolkit.models import Portfolio

# 1. Descarga de acciones e índices
yahoo = YahooFinanceExtractor()
assets = yahoo.fetch_batch(
    tickers=["AAPL", "MSFT", "SAN.MC", "^IBEX"],
    start="2024-01-01",
    end="2025-01-01"
)

# 2. Creación de Cartera (pesos iguales por defecto: 1/N)
portfolio = Portfolio(assets=assets, name="Cartera Global")
print(portfolio)

# 3. Métricas automáticas
print(f"Retorno diario medio: {portfolio.mean_return:.5f}")
print(f"Volatilidad anualizada: {portfolio.annualized_volatility():.2%}")
print(f"Ratio de Sharpe: {portfolio.sharpe_ratio(risk_free_rate=0.03):.2f}")
print(f"Max Drawdown: {portfolio.max_drawdown():.2%}")
print(f"VaR (95%): {portfolio.value_at_risk(0.95):.2%}")
```

#### Cartera con ponderaciones personalizadas

```python
custom_weights = {"AAPL": 0.40, "MSFT": 0.30, "SAN.MC": 0.15, "^IBEX": 0.15}
portfolio = Portfolio(assets=assets, weights=custom_weights, name="Growth Portfolio")

# Matriz de correlación
print(portfolio.correlation_matrix.round(3))
```

Ejecuta los scripts de prueba completos:
- `python examples/test_fetch.py`
- `python examples/test_fetch_fred.py`
- `python examples/test_portfolio.py`

### Dependencias

| Paquete | Versión mínima | Propósito |
|---|---|---|
| `yfinance` | ≥ 0.2.36 | Descarga de acciones e índices bursátiles |
| `pandas` | ≥ 2.0.0 | Manipulación y alineación de series temporales |
| `numpy` | ≥ 1.24.0 | Operaciones algebraicas y estadísticas vectorizadas |
| `matplotlib` | ≥ 3.7.0 | Visualizaciones gráficas |
| `pandas-datareader` | ≥ 0.10.0 | Conexión con la API de FRED (datos macroeconómicos) |

### Documentación

Las guías del taller se encuentran en [`doc/`](doc/):
- **Parte 1** — Configuración de Git y SSH (`guia_taller_parte1_git_ssh.pdf`)
- **Parte 2** — Arquitectura y extracción de datos (`guia_taller_parte2.pdf`)
- **Diapositivas** — `Taller_B1_T1.pdf`

---

## English

> **Master MIAX BME · Edition 15**  
> Block B1 · Workshop 1: Architecture, data extraction and portfolio modeling

### Overview

This project implements a professional Python toolbox for fetching, standardizing, and analyzing financial and macroeconomic data, as well as quantitative investment portfolio modeling and management.

The architecture emphasizes clean object-oriented design and **DataClasses**, cleanly decoupling the data ingestion layer from analytical models.

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
│   └── test_portfolio.py             # Portfolio creation & risk metrics
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
│       │   ├── portfolio.py          # Portfolio DataClass (aggregation & risk)
│       │   └── __init__.py
│       └── utils/                    # Data cleaning & helpers
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

#### 2. `Portfolio` — Investment Portfolio Model (`models/portfolio.py`)

A `dataclass` aggregating multiple `PriceSeries` assets, managing weights, and automatically computing statistical and risk metrics:

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

#### 3. Data Extractors (`data/`)

- **`BaseDataExtractor`** (`data/base.py`): Abstract interface defining `fetch_series()` and `fetch_batch()`.
- **`YahooFinanceExtractor`** (`data/yahoo.py`): Fetches equities and indices in single or batch queries.
- **`FREDExtractor`** (`data/fred.py`): Fetches macroeconomic series from FRED (Fed Funds rate, VIX, Oil, etc.).

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

# Create Portfolio with custom weights
weights = {"AAPL": 0.50, "MSFT": 0.30, "SAN.MC": 0.20}
portfolio = Portfolio(assets=assets, weights=weights, name="Tech & Banking")

print(portfolio)
print(f"Sharpe Ratio: {portfolio.sharpe_ratio(risk_free_rate=0.03):.2f}")
print(f"Max Drawdown: {portfolio.max_drawdown():.2%}")
print(f"95% VaR: {portfolio.value_at_risk(0.95):.2%}")
```

Run test examples:
- `python examples/test_fetch.py`
- `python examples/test_fetch_fred.py`
- `python examples/test_portfolio.py`

### Dependencies

| Package | Min. Version | Purpose |
|---|---|---|
| `yfinance` | ≥ 0.2.36 | Equity and index price data |
| `pandas` | ≥ 2.0.0 | Time series alignment and data manipulation |
| `numpy` | ≥ 1.24.0 | Vectorized algebra and statistical computations |
| `matplotlib` | ≥ 3.7.0 | Plotting and reporting |
| `pandas-datareader` | ≥ 0.10.0 | FRED macroeconomic API client |

### Documentation

Workshop guides available in [`doc/`](doc/):
- **Part 1** — Git & SSH setup (`guia_taller_parte1_git_ssh.pdf`)
- **Part 2** — Architecture & data extraction (`guia_taller_parte2.pdf`)
- **Slides** — `Taller_B1_T1.pdf`
