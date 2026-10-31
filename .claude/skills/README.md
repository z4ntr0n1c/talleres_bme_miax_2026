# Skills de arquitectura — Talleres Máster MIAX BME

Skills para Claude Code que fijan las bases de arquitectura de software comunes a todos los talleres (`T1`, `T1_1`, `T2`, …). Son un punto de partida pequeño y se irán ampliando.

| Skill | Cuándo se usa |
|---|---|
| [`arquitectura-taller`](arquitectura-taller/SKILL.md) | Diseñar o revisar el código de un taller: capas, estructura de paquete, convenciones |
| [`nuevo-taller`](nuevo-taller/SKILL.md) | Crear el esqueleto de un taller nuevo (`TN/`) a partir de la plantilla |
| [`entorno-python`](entorno-python/SKILL.md) | Elegir intérprete, instalar dependencias y ejecutar scripts/notebooks |
| [`ejercicio-notebook`](ejercicio-notebook/SKILL.md) | Talleres basados en notebooks (versión alumno vs. resuelta, exportación) |

## Compartir y contribuir

- Esta carpeta **se versiona en git** (el `.gitignore` raíz ignora `.claude/*` salvo `!.claude/skills/`). Cualquier configuración personal (`.claude/settings.local.json`, etc.) queda fuera.
- Para añadir una skill: crea `.claude/skills/<nombre>/SKILL.md`, añádela a la tabla de arriba y a la del `README.md` raíz, y súbela en una PR.
- Mantén las skills cortas y concretas; enlaza a `T1/` como implementación de referencia en vez de duplicar código.

## Formato

Cada skill vive en `.claude/skills/<nombre>/SKILL.md` con frontmatter YAML:

```yaml
---
name: <nombre-en-kebab-case>
description: <qué hace y cuándo debe activarse>
---
```

Los recursos de apoyo (plantillas, ejemplos) van en subcarpetas de la propia skill (p. ej. `nuevo-taller/templates/`).

## Próximas ampliaciones (ideas)

- `testing-taller`: convención `pytest` + datos sintéticos offline.
- `reportes`: estándar de informes Markdown/PDF y dashboards.
- `adr`: registro de decisiones de arquitectura (`doc/adr/NNNN-*.md`).
- `revision-pr`: checklist de revisión antes de fusionar.

