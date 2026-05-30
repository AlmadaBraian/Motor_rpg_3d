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

## Verificación básica

```bash
python -m compileall -q .
```

Actualmente no existe configuración formal de tests, linting, tipado ni CI/CD. Ver la hoja de ruta propuesta en la auditoría.
