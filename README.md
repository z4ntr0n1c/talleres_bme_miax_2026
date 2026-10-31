# talleres_bme_miax_2026
Talleres del Master MIAX de BME - Edicion 15

## Estructura

| Carpeta | Contenido |
|---|---|
| [`T1/`](T1/) | Toolkit de datos financieros (ingesta, carteras, Monte Carlo, reportes) |
| [`T1_1/`](T1_1/) | Ejercicio guiado en notebook: *Hues and Cues* (percepción del color) |
| [`T2/`](T2/) | Taller 2 (en preparación) |
| [`.claude/skills/`](.claude/skills/) | Skills compartidas de arquitectura de software para asistentes de IA |

## Skills de arquitectura (`.claude/skills/`)

Las skills recogen las bases de arquitectura comunes a todos los talleres y las usa automáticamente **Claude Code** al trabajar en este repositorio. Se versionan en git para que todo el grupo trabaje con las mismas convenciones.

| Skill | Para qué sirve |
|---|---|
| [`arquitectura-taller`](.claude/skills/arquitectura-taller/SKILL.md) | Capas, estructura de paquete y convenciones de código |
| [`nuevo-taller`](.claude/skills/nuevo-taller/SKILL.md) | Crear el esqueleto de un taller nuevo |
| [`entorno-python`](.claude/skills/entorno-python/SKILL.md) | Intérpretes, dependencias y ejecución |
| [`ejercicio-notebook`](.claude/skills/ejercicio-notebook/SKILL.md) | Notebooks de ejercicio (alumno vs. resuelto) y exportación |

- Solo se comparte `.claude/skills/`; el resto de `.claude/` (p. ej. `settings.local.json`) sigue siendo local e ignorado por git.
- Para añadir o modificar una skill, consulta [`.claude/skills/README.md`](.claude/skills/README.md) y súbela en una PR como cualquier otro cambio.
