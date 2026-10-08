# Taller 1 — Kit de Extracción de Datos Financieros

> **Máster MIAX BME · Edición 15**  
> Bloque B1 · Taller 1: Arquitectura y extracción de datos financieros

## Descripción

Este taller presenta un toolkit Python limpio y extensible para descargar y estandarizar series temporales financieras desde **Yahoo Finance**. El foco está en la buena arquitectura de software: clases base abstractas, dataclasses y una separación clara de responsabilidades entre la ingesta de datos y el modelado.

## Estructura del repositorio

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

## Componentes principales

### `PriceSeries` — Modelo de datos

Un `dataclass` que representa una serie temporal estandarizada para un único activo:

| Campo | Tipo | Descripción |
|---|---|---|
| `ticker` | `str` | Símbolo del activo (en mayúsculas) |
| `asset_type` | `str` | `'equity'`, `'index'`, `'macro'`, etc. |
| `data` | `pd.DataFrame` | Indexado por fecha con columnas `close` y `returns` |
| `mean_return` | `float` | Retorno diario medio (calculado automáticamente) |
| `std_return` | `float` | Desviación típica del retorno diario (calculada automáticamente) |

### `BaseDataExtractor` — Interfaz abstracta

Define el contrato estándar de ingesta que toda fuente de datos debe implementar:

- `fetch_series(ticker, start, end) → PriceSeries`
- `fetch_batch(tickers, start, end) → List[PriceSeries]`

### `YahooFinanceExtractor` — Implementación concreta

Implementa `BaseDataExtractor` usando `yfinance`. Gestiona:

- Descarga de uno o varios tickers en una sola llamada a la API
- Normalización de columnas (minúsculas, índice plano)
- Cálculo de retornos diarios porcentuales (`close.pct_change()`)
- Manejo robusto de datos vacíos o ausentes

## Instalación

### 1. Crear y activar un entorno virtual

```bash
cd T1
python -m venv .venv
source .venv/bin/activate
```

### 2. Instalar el paquete

```bash
pip install -e src/
```

O instalar las dependencias directamente:

```bash
pip install -r requirements.txt
```

## Uso

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

## Dependencias

| Paquete | Versión mínima |
|---|---|
| `yfinance` | ≥ 0.2.36 |
| `pandas` | ≥ 2.0.0 |
| `numpy` | ≥ 1.24.0 |
| `matplotlib` | ≥ 3.7.0 |

## Documentación

Las guías del taller están disponibles en [`doc/`](doc/):

- **Parte 1** — Configuración de Git y SSH (`guia_taller_parte1_git_ssh.pdf`)
- **Parte 2** — Arquitectura y extracción de datos (`guia_taller_parte2.pdf`)
- **Diapositivas** — `Taller_B1_T1.pdf`

