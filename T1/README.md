# Taller 1 — Kit de Extracción de Datos Financieros / Financial Data Extraction Toolkit

> 🇪🇸 [Español](#español) · 🇬🇧 [English](#english)

---

## Español

> **Máster MIAX BME · Edición 15**  
> Bloque B1 · Taller 1: Arquitectura y extracción de datos financieros

### Descripción

Este taller presenta un toolkit Python limpio y extensible para descargar y estandarizar series temporales financieras desde **Yahoo Finance**. El foco está en la buena arquitectura de software: clases base abstractas, dataclasses y una separación clara de responsabilidades entre la ingesta de datos y el modelado.

### Estructura del repositorio

```
T1/
├── doc/                              # Guías y diapositivas del taller (PDF/HTML)
│   ├── Taller_B1_T1.pdf
│   ├── guia_taller_parte1_git_ssh.*  # Parte 1: Configuración Git & SSH
│   └── guia_taller_parte2.*          # Parte 2: Arquitectura y extracción
├── examples/
│   └── test_fetch.py                 # Ejemplos de uso (descarga individual y en batch)
├── src/
│   └── toolkit/
│       ├── data/
│       │   ├── base.py               # Interfaz abstracta del extractor
│       │   ├── yahoo.py              # Implementación con Yahoo Finance
│       │   └── __init__.py
│       └── models/
│           └── series.py             # Dataclass PriceSeries
├── pyproject.toml
├── requirements.txt
└── setup.py
```

### Componentes principales

#### `PriceSeries` — Modelo de datos

Un `dataclass` que representa una serie temporal estandarizada para un único activo:

| Campo | Tipo | Descripción |
|---|---|---|
| `ticker` | `str` | Símbolo del activo (en mayúsculas) |
| `asset_type` | `str` | `'equity'`, `'index'`, `'macro'`, etc. |
| `data` | `pd.DataFrame` | Indexado por fecha con columnas `close` y `returns` |
| `mean_return` | `float` | Retorno diario medio (calculado automáticamente) |
| `std_return` | `float` | Desviación típica del retorno diario (calculada automáticamente) |

#### `BaseDataExtractor` — Interfaz abstracta

Define el contrato estándar de ingesta que toda fuente de datos debe implementar:

- `fetch_series(ticker, start, end) → PriceSeries`
- `fetch_batch(tickers, start, end) → List[PriceSeries]`

#### `YahooFinanceExtractor` — Implementación concreta

Implementa `BaseDataExtractor` usando `yfinance`. Gestiona:

- Descarga de uno o varios tickers en una sola llamada a la API
- Normalización de columnas (minúsculas, índice plano)
- Cálculo de retornos diarios porcentuales (`close.pct_change()`)
- Manejo robusto de datos vacíos o ausentes

### Instalación

#### 1. Crear y activar un entorno virtual

```bash
cd T1
python -m venv .venv
source .venv/bin/activate
```

#### 2. Instalar el paquete

```bash
pip install -e src/
```

O instalar las dependencias directamente:

```bash
pip install -r requirements.txt
```

### Uso

```python
from toolkit.data import YahooFinanceExtractor

extractor = YahooFinanceExtractor()

# Descarga de un único activo
apple = extractor.fetch_series(ticker="AAPL", start="2025-01-01", end="2026-01-01")
print(f"{apple.ticker} | Retorno medio: {apple.mean_return:.5f} | Desv. típica: {apple.std_return:.5f}")

# Descarga en batch de acciones e índices
portfolio = extractor.fetch_batch(
    tickers=["MSFT", "SAN.MC", "^IBEX"],
    start="2025-01-01",
    end="2026-01-01"
)
for s in portfolio:
    print(f"{s.ticker} — {len(s.data)} sesiones")
```

Consulta [`examples/test_fetch.py`](examples/test_fetch.py) para un script ejecutable completo.

### Dependencias

| Paquete | Versión mínima |
|---|---|
| `yfinance` | ≥ 0.2.36 |
| `pandas` | ≥ 2.0.0 |
| `numpy` | ≥ 1.24.0 |
| `matplotlib` | ≥ 3.7.0 |

### Documentación

Las guías del taller están disponibles en [`doc/`](doc/):

- **Parte 1** — Configuración de Git y SSH (`guia_taller_parte1_git_ssh.pdf`)
- **Parte 2** — Arquitectura y extracción de datos (`guia_taller_parte2.pdf`)
- **Diapositivas** — `Taller_B1_T1.pdf`

---

## English

> **Master MIAX BME · Edition 15**  
> Block B1 · Workshop 1: Architecture and financial data extraction

### Overview

This workshop introduces a clean, extensible Python toolkit for fetching and standardizing financial time-series data from **Yahoo Finance**. The focus is on good software architecture: abstract base classes, dataclasses, and a clear separation of concerns between data ingestion and data modeling.

### Repository Structure

```
T1/
├── doc/                              # Workshop guides & slides (PDF/HTML)
│   ├── Taller_B1_T1.pdf
│   ├── guia_taller_parte1_git_ssh.*  # Part 1: Git & SSH setup
│   └── guia_taller_parte2.*          # Part 2: Architecture & extraction
├── examples/
│   └── test_fetch.py                 # Usage examples (single & batch fetch)
├── src/
│   └── toolkit/
│       ├── data/
│       │   ├── base.py               # Abstract extractor interface
│       │   ├── yahoo.py              # Yahoo Finance implementation
│       │   └── __init__.py
│       └── models/
│           └── series.py             # PriceSeries dataclass
├── pyproject.toml
├── requirements.txt
└── setup.py
```

### Key Components

#### `PriceSeries` — Data Model

A `dataclass` that represents a standardized time series for a single asset:

| Field | Type | Description |
|---|---|---|
| `ticker` | `str` | Asset ticker symbol (uppercased) |
| `asset_type` | `str` | `'equity'`, `'index'`, `'macro'`, etc. |
| `data` | `pd.DataFrame` | DateTime-indexed with `close` and `returns` columns |
| `mean_return` | `float` | Auto-computed daily mean return |
| `std_return` | `float` | Auto-computed daily return standard deviation |

#### `BaseDataExtractor` — Abstract Interface

Defines the standardized ingestion contract that all data sources must implement:

- `fetch_series(ticker, start, end) → PriceSeries`
- `fetch_batch(tickers, start, end) → List[PriceSeries]`

#### `YahooFinanceExtractor` — Concrete Implementation

Implements `BaseDataExtractor` using `yfinance`. Handles:

- Single-ticker and multi-ticker batch downloads in a single API call
- Column normalization (lowercase, flat index)
- Daily percentage return calculation (`close.pct_change()`)
- Graceful handling of missing or empty data

### Installation

#### 1. Create and activate a virtual environment

```bash
cd T1
python -m venv .venv
source .venv/bin/activate
```

#### 2. Install the package

```bash
pip install -e src/
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

### Usage

```python
from toolkit.data import YahooFinanceExtractor

extractor = YahooFinanceExtractor()

# Fetch a single equity
apple = extractor.fetch_series(ticker="AAPL", start="2025-01-01", end="2026-01-01")
print(f"{apple.ticker} | Mean Return: {apple.mean_return:.5f} | Std: {apple.std_return:.5f}")

# Fetch a batch of equities and indices
portfolio = extractor.fetch_batch(
    tickers=["MSFT", "SAN.MC", "^IBEX"],
    start="2025-01-01",
    end="2026-01-01"
)
for s in portfolio:
    print(f"{s.ticker} — {len(s.data)} trading days")
```

See [`examples/test_fetch.py`](examples/test_fetch.py) for a runnable version.

### Dependencies

| Package | Min. Version |
|---|---|
| `yfinance` | ≥ 0.2.36 |
| `pandas` | ≥ 2.0.0 |
| `numpy` | ≥ 1.24.0 |
| `matplotlib` | ≥ 3.7.0 |

### Documentation

Workshop guides are available in [`doc/`](doc/):

- **Part 1** — Git & SSH setup (`guia_taller_parte1_git_ssh.pdf`)
- **Part 2** — Architecture & data extraction (`guia_taller_parte2.pdf`)
- **Slides** — `Taller_B1_T1.pdf`
