---
name: entorno-python
description: Cómo elegir el intérprete Python, instalar dependencias y ejecutar scripts o notebooks en los talleres del Máster MIAX BME. Úsala antes de ejecutar código, instalar paquetes o cuando aparezcan errores de importación (ModuleNotFoundError, Pylance reportMissingImports).
---

# Entorno Python de los talleres

## Intérpretes disponibles

| Entorno | Ruta | Cuándo |
|---|---|---|
| venv por taller | `TN/.venv/bin/python` | Código del paquete del taller (preferido) |
| conda `MIAX15` | `~/anaconda3/envs/MIAX15/bin/python` | Intérprete por defecto del workspace (VS Code), notebooks, deep learning (torch, jax, tensorflow) |

Python objetivo: **3.11**.

## Reglas

1. Usa siempre la **ruta explícita** del intérprete en comandos no interactivos (`T1/.venv/bin/python script.py`), nunca `python` a secas.
2. **Nunca** instales en el Python del sistema ni en `base` de conda.
3. Instala el paquete del taller en **editable** desde la carpeta del taller: `pip install -e .`.
4. Si añades una dependencia: `pyproject.toml` **y** `requirements.txt` del taller.
5. Dependencias de un ejercicio concreto (p. ej. `seaborn` en T1_1) se documentan en su README, no en el paquete de otro taller.

## Ejecución sin pantalla

```python
import matplotlib
matplotlib.use("Agg")
```

Si `~/.config/matplotlib` no es escribible: `export MPLCONFIGDIR="$PWD/.mpl_cache"`.

## Diagnóstico rápido

```bash
TN/.venv/bin/python -c "import sys; print(sys.executable, sys.version)"
TN/.venv/bin/python -m pip list
```

- **Pylance no resuelve imports**: el intérprete seleccionado en VS Code no es el que tiene el paquete → *Python: Select Interpreter* o revisar `.vscode/settings.json` (`python.defaultInterpreterPath`, `python.analysis.extraPaths`).
- **`ModuleNotFoundError` del propio paquete**: falta `pip install -e .` en ese entorno.

