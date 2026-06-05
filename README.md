# Motor RPG 3D / Dreamcast Toolkit

Editor y runtime experimental para crear mapas RPG 3D con Python, Tkinter, PyOpenGL y assets exportables a Dreamcast.

## Estado del repositorio

Este proyecto contiene prototipos funcionales, recursos gráficos, escenas JSON, exportaciones Dreamcast y versiones heredadas. La auditoría técnica principal está documentada en [`docs/AUDIT.md`](docs/AUDIT.md).

## Punto de entrada local

```bash
python "editor de mapas v12.py"
```

> Requiere entorno gráfico con Tkinter/OpenGL y dependencias Python como `pyopengltk`, `PyOpenGL` y `Pillow`.

## Estructura actual de alto nivel

- `Toolkit.py`: editor principal Tkinter y orquestación de estado.
- `OpglManager.py`: viewport OpenGL, renderizado y lógica visual.
- `RuntimeCombat.py`, `RuntimeSkill.py`, `RuntimeActor.py`, `RuntimeSystem.py`: subsistemas de runtime/juego.
- `TextureManager.py`, `SpriteManager.py`, `FontRenderer.py`: gestión de assets visuales.
- `Actor*`, `Item*`, `Skill*`, `Tile.py`: modelos y ventanas de edición.
- `textures/`, `sprites/`, `fonts/`, `obj/`, `scenes/`: recursos del proyecto.
- `legacy/` y `src - copia/`: código histórico que debería aislarse o retirarse del paquete activo.


## Paquetes Python explícitos

El código nuevo debe vivir bajo `motor_rpg/` con límites claros:

- `motor_rpg.domain`: configuración tipada, serialización de escenas y reglas puras de combate.
- `motor_rpg.runtime`: servicios de ejecución, carga de assets y validación de manifiestos.
- `motor_rpg.rendering`: renderizado/OpenGL y adaptadores visuales.
- `motor_rpg.editor`: herramientas Tkinter y flujos de autoría.

Los módulos históricos en la raíz permanecen como puntos de entrada de compatibilidad,
pero deben delegar gradualmente en estos paquetes. La configuración global se expone
desde `config.py` como wrapper compatible sobre `motor_rpg.domain.config.GameConfig`.

## Calidad, tests y assets

```bash
python -m compileall -q motor_rpg tests
pytest
ruff check motor_rpg tests
mypy
python tools/validate_assets.py
```

La política de assets está documentada en [`docs/ASSETS.md`](docs/ASSETS.md).

## Verificación básica

```bash
python -m compileall -q .
```

El repositorio incluye `pyproject.toml`, CI, linting con Ruff, tipado incremental con mypy y pruebas de dominio/runtime.
