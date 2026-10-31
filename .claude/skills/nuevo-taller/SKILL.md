---
name: nuevo-taller
description: Crea el esqueleto de un taller nuevo (T2, T3, ...) en la raíz del repositorio siguiendo la arquitectura base (src-layout, capas data/utils/models, examples, tests, doc). Úsala cuando el usuario pida empezar, inicializar o estructurar un taller.
---

# Crear un taller nuevo

## Entradas a pedir (si no se indican)

- **Carpeta** del taller: `T2`, `T3`, … (en la raíz del repo).
- **Nombre del paquete** Python (`snake_case`, p. ej. `toolkit_t2`).
- **Descripción** de una línea.
- **Tipo**: `paquete` (código reutilizable, estructura completa) o `notebook` (ejercicio guiado → ver skill `ejercicio-notebook`).

## Pasos (tipo `paquete`)

1. Comprobar que la carpeta no tiene ya código; si existe, **no sobrescribir** sin confirmación.
2. Crear la estructura:

   ```
   TN/
   ├── src/<paquete>/{__init__.py, data/__init__.py, utils/__init__.py, models/__init__.py}
   ├── examples/
   ├── tests/test_smoke.py
   ├── doc/architecture.md
   ├── pyproject.toml
   ├── requirements.txt
   ├── README.md
   └── .gitignore
   ```

3. Rellenar a partir de las plantillas de [`templates/`](templates/), sustituyendo `{{PAQUETE}}`, `{{TALLER}}` y `{{DESCRIPCION}}`:
   - `pyproject.toml.tmpl` → `pyproject.toml`
   - `README.md.tmpl` → `README.md`
   - `test_smoke.py.tmpl` → `tests/test_smoke.py`
4. Crear entorno e instalar en editable (ver skill `entorno-python`):

   ```bash
   cd TN && python -m venv .venv && .venv/bin/pip install -e . pytest
   .venv/bin/python -m pytest -q
   ```

5. Copiar el `.gitignore` de `T1/` como base.
6. Opcional: generar `TN/CLAUDE.md` tomando `T1/CLAUDE.md` como modelo.

## Criterio de terminado

- `pip install -e .` funciona y `python -c "import <paquete>"` no falla.
- `pytest` pasa el test de humo.
- `README.md` explica instalación y estructura.

