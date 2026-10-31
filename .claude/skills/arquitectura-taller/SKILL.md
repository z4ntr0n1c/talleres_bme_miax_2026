---
name: arquitectura-taller
description: Bases de arquitectura de software para los talleres del Máster MIAX BME (T1, T2, ...). Úsala al diseñar, ampliar o revisar el código Python de un taller: estructura de paquete src-layout, separación en capas data/utils/models/reports, contratos entre capas, convenciones de código y de datos.
---

# Arquitectura base de un taller

Referencia viva: `T1/` (toolkit financiero). Todo taller nuevo con código reutilizable sigue este patrón.

## 1. Principios

1. **Paquete instalable, no scripts sueltos**: la lógica vive en `src/<paquete>/`; `examples/` y notebooks solo *consumen* el paquete.
2. **Capas con dependencia en un solo sentido**:

   ```
   data  ──►  utils  ──►  models  ──►  reports
   (ingesta)  (limpieza/   (dominio,     (markdown,
              validación)  cálculo)      gráficos)
   ```

   Una capa nunca importa de una capa posterior. `models` no conoce a `data` (recibe objetos ya construidos).
3. **Contratos explícitos**: interfaces con `abc.ABC` para puntos de extensión (p. ej. `BaseDataExtractor`) y `@dataclass` para objetos de dominio.
4. **Fail-fast**: validar en las fronteras (entrada de datos, construcción de objetos) y lanzar una excepción propia (`ValidationError(ValueError)`).
5. **Reproducibilidad**: todo lo aleatorio acepta `seed`; nada depende de rutas absolutas.

## 2. Estructura de un taller

```
TN/
├── src/<paquete>/
│   ├── __init__.py        # API pública (__all__)
│   ├── data/              # base.py (ABC) + un módulo por fuente
│   ├── utils/             # cleaning.py, validation.py
│   ├── models/            # dataclasses de dominio
│   └── reports/           # (opcional) generación de informes/plots
├── examples/              # scripts ejecutables de demostración/validación
├── tests/                 # pytest, preferiblemente offline
├── doc/                   # architecture.md, guías, enunciado
├── pyproject.toml         # única fuente de metadatos y dependencias
├── requirements.txt       # espejo de dependencias de pyproject
├── README.md
└── CLAUDE.md              # guía local del taller para la IA
```

Para crearla automáticamente usa la skill `nuevo-taller`.

## 3. Convenciones

- **Código**: PEP 8, type hints en la API pública, docstrings en todo lo público, nombres de módulos en `snake_case`, clases en `PascalCase`.
- **Datos tabulares**: `pandas.DataFrame` con índice `DatetimeIndex` si es temporal y columnas en minúscula (`close`, `returns`, …). Documenta el esquema en el docstring del objeto que lo contiene.
- **API pública**: se exporta en el `__init__.py` del subpaquete y en el del paquete raíz. Cambiar una firma pública obliga a actualizar `README.md` y `doc/architecture.md`.
- **Configuración y secretos**: variables de entorno; nunca en el código ni en git.
- **Salidas generadas** (`*.png`, `reports/`, `data/`): fuera de git.

## 4. Checklist de revisión

- [ ] ¿Respeta el sentido de dependencias entre capas?
- [ ] ¿La nueva funcionalidad está en `src/` y no en un script/notebook?
- [ ] ¿Hay validación en la frontera y excepción propia?
- [ ] ¿Tipos, docstrings y exportación en `__all__`?
- [ ] ¿Se puede probar sin red (datos sintéticos)?
- [ ] ¿`README.md` / `doc/architecture.md` siguen siendo ciertos?

