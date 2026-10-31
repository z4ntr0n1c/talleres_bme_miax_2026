---
name: ejercicio-notebook
description: Convenciones para talleres basados en Jupyter notebooks (p. ej. T1_1 Hues and Cues) — separación entre versión alumno y versión resuelta, organización de datos, rutas, ejecución y exportación a HTML/PDF. Úsala al crear, resolver, revisar o exportar un notebook de ejercicio.
---

# Talleres basados en notebooks

## Estructura

```
TN_M/
├── Ejercicio_<Nombre>_Alumnos.ipynb            # plantilla con TODOs vacíos (NO contiene soluciones)
├── Ejercicio_<Nombre>_Alumnos_resuelto.ipynb   # solución completa con salidas
├── Instrucciones_<X>.pdf                       # enunciado
├── data/ (o ficheros de datos junto al notebook)
└── export/                                     # HTML/PDF generados (opcional)
```

## Reglas

1. **Nunca** escribir soluciones en el notebook `_Alumnos`. Las soluciones van solo en `_resuelto`. Antes de un commit, comprobar que no son idénticos:

   ```bash
   cmp Ejercicio_X_Alumnos.ipynb Ejercicio_X_Alumnos_resuelto.ipynb && echo "¡ATENCIÓN: idénticos!"
   ```

2. Respetar la estructura de celdas del enunciado: cada `# TODO N.M` se resuelve **en su celda**, sin reordenar ni borrar celdas markdown.
3. **Rutas relativas** con fallback (el notebook puede ejecutarse desde su carpeta o desde la raíz):

   ```python
   from pathlib import Path
   BASE = Path("TN_M") if Path("TN_M").exists() else Path(".")
   df = pd.read_csv(BASE / "datos.csv")
   ```

4. Las celdas deben ejecutarse **de arriba abajo** sin errores en un kernel limpio.
5. Lógica reutilizable (funciones de más de unas líneas) → candidata a moverse a un módulo `.py` o al paquete de un taller (ver `arquitectura-taller`).
6. Las respuestas de reflexión en markdown se redactan en español, con cifras obtenidas del propio notebook.

## Ejecución y exportación

- Verificar en kernel limpio con el intérprete del taller (ver `entorno-python`).
- Exportación HTML/PDF: el script de referencia es `T1_1/export_notebook_to_html_and_pdf.py` (ejecuta, embebe salidas y genera HTML; el PDF se obtiene con Chrome headless `--print-to-pdf`).
- Si `jupyter nbconvert` está disponible, es la alternativa estándar:

  ```bash
  jupyter nbconvert --to html --execute Ejercicio_X_Alumnos_resuelto.ipynb
  ```

