# CLAUDE.md — Taller 1 (T1): Toolkit de Datos Financieros · MIAX BME

Guía para asistentes de IA (Claude / agentes) que trabajen en este taller. Responde y documenta **en español** salvo que se pida lo contrario.

## Contexto

Taller 1 del Bloque B1 del Máster MIAX (Instituto BME). Paquete Python `t1-bme-miax-toolkit` (import: `toolkit`) para:

1. **Ingesta** de datos de mercado (Yahoo Finance) y macro (FRED).
2. **Modelado** de series de precios (`PriceSeries`) y carteras (`Portfolio`).
3. **Simulación Monte Carlo** GBM univariante y multivariante (Cholesky).
4. **Limpieza, validación** (fail-fast) y **reportes** (Markdown + dashboard 2×2).

Documentación de referencia: `README.md` (ES/EN), `doc/architecture.md` (UML y flujo de datos), guías `doc/guia_taller_parte{1..5}_*.pdf` y enunciado `doc/Taller_B1_T1.pdf`.

## Entorno Python

Hay dos entornos válidos; **no instales paquetes globalmente**.

| Entorno | Ruta del intérprete | Uso |
|---|---|---|
| venv local (preferido para T1) | `.venv/bin/python` (Python 3.11) | Toolkit, ejemplos, tests |
| conda `MIAX15` | `~/anaconda3/envs/MIAX15/bin/python` | Intérprete por defecto del workspace (VS Code), notebooks y deep learning |

```bash
source .venv/bin/activate            # o: conda activate MIAX15
pip install -e .                      # instala `toolkit` en modo editable (src-layout)
# alternativa sólo dependencias:
pip install -r requirements.txt
```

- Invoca siempre el intérprete explícito (`.venv/bin/python ...`) en comandos no interactivos.
- Dependencias núcleo (`pyproject.toml` / `requirements.txt`): `yfinance`, `pandas>=2`, `numpy`, `matplotlib`, `pandas-datareader`, `requests`. Si añades una dependencia, actualiza **ambos** ficheros.
- Matplotlib en modo headless: usa `matplotlib.use("Agg")` y, si `~/.config/matplotlib` no es escribible, exporta `MPLCONFIGDIR` a un directorio local.

## Estructura

```
Taller-T1-B1/
├── src/toolkit/
│   ├── __init__.py       # API pública y __version__
│   ├── logging_utils.py  # setup_logging() idempotente
│   ├── reports.py        # Capa de presentación: Markdown report + gráficos Matplotlib
│   ├── data/             # base.py (BaseDataExtractor, ABC) · yahoo.py · fred.py
│   ├── models/           # series.py (PriceSeries) · portfolio.py (Portfolio) · monte_carlo.py · metrics.py
│   └── utils/            # cleaning.py · validation.py (ValidationError)
├── tests/                # test_toolkit.py (suite unitaria offline sin red: unittest / pytest)
├── examples/             # test_*.py (scripts de validación con red) · plots/ · reports/
├── doc/                  # guías, arquitectura, enunciado
├── pyproject.toml · requirements.txt
```

API pública exportada en `src/toolkit/__init__.py`; si añades una clase/función pública, expórtala en el `__init__.py` del subpaquete **y** en el de nivel superior (`__all__`).

## Arquitectura y convenciones

- **Capas**: `data` → `utils` (limpieza/validación) → `models` → reportes. `models` no debe depender de `data`.
- **Extractores** heredan de `BaseDataExtractor` e implementan `fetch_series(ticker, start, end, ...)`, `fetch_batch(tickers, start, end, ...)` y `_standardize_dataframe(...)`. Devuelven siempre `PriceSeries`.
- **Formato estándar de datos**: `DataFrame` con índice `DatetimeIndex` y columnas en minúscula `close` (obligatoria) y `returns` (rentabilidades simples, `pct_change`).
- **Dataclasses** (`@dataclass`) con métricas calculadas en `__post_init__` (`field(init=False)`).
- **Anualización**: `trading_days=252` por defecto; `risk_free_rate` y `confidence_level` (0.95) como parámetros con valor por defecto.
- **Validación fail-fast**: lanza `ValidationError` (subclase de `ValueError`) ante datos o pesos inválidos (pesos deben sumar 1, sin NaN, etc.).
- Estilo: PEP 8, type hints en firmas públicas, docstrings en todas las funciones/clases públicas. Mantén comentarios y docstrings existentes.
- Monte Carlo: permite fijar semilla (`seed`) para reproducibilidad; usa `numpy` vectorizado, sin bucles por simulación.

## Ejecutar y probar

Suite de tests unitarios offline (`tests/test_toolkit.py`) y scripts de validación en `examples/` (estos últimos requieren **red** para Yahoo/FRED):

```bash
.venv/bin/python -m unittest discover -s tests -v        # Suite unitaria offline (sin red)
.venv/bin/python examples/test_fetch.py                  # Yahoo: serie individual y batch
.venv/bin/python examples/test_fetch_fred.py             # FRED: series macro
.venv/bin/python examples/test_portfolio.py              # Cartera, métricas, correlación/covarianza
.venv/bin/python examples/test_monte_carlo.py            # GBM univariante y multivariante
.venv/bin/python examples/test_reports_and_cleaning.py   # validación, reporte .md y dashboard 2x2
```

- Salidas: gráficos en `examples/plots/*.png`, informes en `examples/reports/*.md`.
- Comprobación rápida sin red: `.venv/bin/python -c "import toolkit; print(toolkit.__all__)"`.
- Para tests offline, construye `PriceSeries` con un `DataFrame` sintético (`close` generado con numpy) en lugar de descargar.

## Git y ficheros ignorados

- `.gitignore` excluye: `.venv/`, `__pycache__/`, `*.egg-info/`, `reports/`, `*.png`, `.vscode/` y `.claude/` **excepto** `.claude/skills/`, que se comparte.
- Las skills de arquitectura comunes están en `.claude/skills/`; consúltalas antes de diseñar código nuevo.
- Commits estilo convencional: `feat: ...`, `fix: ...`, `docs: ...`.
- No subas datos descargados, credenciales ni API keys (usa variables de entorno).

## Qué NO hacer

- No modificar `.venv/` a mano ni instalar en el Python del sistema.
- No cambiar los nombres de columnas estándar (`close`, `returns`) ni las firmas públicas sin actualizar `README.md` y `doc/architecture.md`.
- No reescribir los PDF/HTML de `doc/` salvo petición expresa.

