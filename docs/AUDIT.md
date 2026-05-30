# Auditoría técnica del repositorio Motor RPG 3D

Fecha de auditoría: 2026-05-30.

## Resumen ejecutivo

El repositorio contiene un editor/runtime RPG 3D en Python con Tkinter y OpenGL, más recursos gráficos, escenas JSON, exportaciones Dreamcast y código legado. El prototipo compila, pero el riesgo principal es de mantenibilidad: módulos monolíticos, acoplamiento global, ausencia de tests automatizados, dependencias no declaradas y artefactos generados versionados.

### Prioridades recomendadas

1. Separar editor, runtime, renderizado y dominio en paquetes Python explícitos.
2. Extraer estado global y constantes duplicadas a configuración tipada.
3. Introducir pruebas de serialización/escenas, reglas de combate y carga de assets.
4. Añadir `pyproject.toml`, CI, linting, typing incremental y política de assets.
5. Limpiar artefactos generados (`__pycache__`, `.pyc`, respaldos `~`, zips temporales) del control de versiones.

## Alcance revisado

- Módulos Python principales en la raíz del repositorio.
- Recursos de juego y exportaciones (`textures/`, `sprites/`, `obj/`, `fonts/`, `scenes/`, `export_dc/`).
- Código legado (`legacy/`, `src - copia/`).
- Estado de documentación, tests, dependencias y CI/CD.

## Hallazgos por área

### 1. Calidad y mantenibilidad del código

**Hallazgos**

- Existen módulos demasiado grandes para una evolución segura: `Toolkit.py` supera las 5.400 líneas y concentra UI, estado de editor, lógica de selección, serialización y play mode; `RuntimeCombat.py` supera las 4.500 líneas y mezcla reglas de combate, cámara, turnos y efectos; `OpglManager.py` supera las 3.300 líneas y mezcla viewport, renderizado, entrada y utilidades.
- Hay imports wildcard y duplicados que dificultan rastrear dependencias y nombres disponibles. Por ejemplo, `Toolkit.py` importa `EventManager`, `OpglManager`, `SpriteManager` y `config` con `*`; `OpglManager.py` repite imports de Tk/OpenGL/PIL/math/os y también usa imports wildcard.
- Hay configuración duplicada en varios módulos (`GRID_W`, `GRID_H`, `CELL_PIXELS`, rutas de textura/exportación) en lugar de depender de un único módulo de settings.
- Se observan handlers amplios con `except:` silencioso al escanear texturas, lo que oculta errores de archivos corruptos o problemas de permisos.
- El tipado es prácticamente inexistente: los modelos son clases mutables con muchos atributos dinámicos, lo cual aumenta el riesgo de errores en serialización, combate y renderizado.
- Hay artefactos de build/cache versionados (`__pycache__`, `.pyc`, respaldos de imágenes `~`, `Thumbs.db`, zips) que hacen más ruidosos los diffs y complican revisiones.

**Recomendaciones**

- Crear paquetes `motor_rpg/editor`, `motor_rpg/runtime`, `motor_rpg/rendering`, `motor_rpg/assets`, `motor_rpg/domain` y mover el código gradualmente.
- Reemplazar imports wildcard por imports explícitos.
- Introducir `dataclasses` o `pydantic`/validadores ligeros para `ActorAsset`, `SkillAsset`, `ItemAsset`, `Tile`, instancias runtime y comandos de eventos.
- Sustituir `except:` por `except (OSError, ValueError, PIL.UnidentifiedImageError) as exc:` con logging estructurado.
- Añadir `.gitignore` y plan de limpieza con `git rm --cached` para artefactos ya versionados.

### 2. Arquitectura y diseño

**Hallazgos**

- La raíz mezcla código activo, escenas de prueba, recursos, exportaciones, herramientas, archivos heredados y copias. Esto impide distinguir API pública, prototipos y datos.
- `Toolkit` opera como objeto dios: construye estado global, maneja UI, runtime, combate, assets, cámara y persistencia.
- `EventManager.py` define funciones libres que reciben `self`; esto simula mixins sin contrato explícito y acopla eventos a atributos internos de `Toolkit`.
- `OpglManager.GLViewport` conoce detalles de combate, sprites, texturas, cámara, HUD, eventos y modelos, por lo que renderizado y lógica de juego no están aislados.
- No hay frontera clara entre editor y runtime: clases de edición cargan y modifican estructuras usadas directamente durante play mode.

**Recomendaciones**

- Definir una arquitectura hexagonal simple:
  - Dominio: entidades puras (`Actor`, `Tile`, `Skill`, `Scene`, `CombatState`).
  - Aplicación: casos de uso (`load_scene`, `save_scene`, `start_combat`, `resolve_turn`).
  - Infraestructura: Tkinter, OpenGL, filesystem, export Dreamcast.
  - Presentación: ventanas y viewport.
- Crear DTOs/formatos versionados para escenas JSON con migraciones (`schema_version`).
- Convertir `EventManager` en servicio/clase con dependencias explícitas o command registry (`action -> handler`).
- Introducir interfaces pequeñas: `TextureRepository`, `SceneRepository`, `Renderer`, `InputController`.

### 3. Rendimiento y optimización

**Hallazgos**

- El procesamiento de texturas transparentes recorre cada píxel y sus vecinos al cargar una textura. Es aceptable si se cachea una vez, pero puede congelar la UI con texturas grandes o muchas recargas.
- El escaneo de texturas abre y redimensiona todas las imágenes en la inicialización del gestor, lo que penaliza el arranque y mezcla thumbnails Tk con carga GL.
- Los módulos grandes sugieren loops de renderizado/combate difíciles de perfilar y optimizar por responsabilidades mezcladas.
- No hay estrategia documentada de liberación de texturas OpenGL (`glDeleteTextures`) ni control de ciclo de vida de recursos.

**Recomendaciones**

- Separar carga de thumbnails, carga GL y procesamiento offline de assets.
- Cachear metadatos de assets y usar lazy loading para miniaturas y texturas GL.
- Mover corrección de halos alfa a un preprocesador de assets o vectorizar con Pillow/Numpy si permanece en runtime.
- Añadir perfiles básicos (`cProfile`, contador de frame time, conteo de draw calls/texturas) en modo debug.
- Centralizar alta/baja de recursos OpenGL en un `ResourceManager` con liberación explícita.

### 4. Seguridad y robustez

**Hallazgos**

- La carga de JSON y assets no valida esquema, tamaños ni rutas esperadas antes de poblar el estado.
- La resolución de rutas permite nombres de textura absolutos si existen, lo cual puede ser útil en editor pero debe controlarse para proyectos compartidos.
- El uso de prints dificulta auditoría de errores y no permite niveles (`debug`, `warning`, `error`).
- Los artefactos binarios y cachés versionados pueden filtrar material temporal y aumentan el tamaño del repositorio.

**Recomendaciones**

- Validar JSON con schemas o validadores Python antes de mutar el estado.
- Normalizar rutas para que los proyectos solo referencien assets dentro de directorios permitidos, salvo modo desarrollador explícito.
- Migrar a `logging` con nombre de módulo y niveles.
- Añadir política de tamaños máximos para imágenes/modelos en carga interactiva.

### 5. Documentación

**Hallazgos**

- No existía README de entrada ni documentación de instalación antes de esta auditoría.
- No hay documentación de formatos JSON, arquitectura, comandos de eventos, flujo de exportación Dreamcast ni dependencias.
- Algunos comentarios explican intención local, pero no reemplazan documentación de módulos o contratos.

**Recomendaciones**

- Mantener `README.md` con instalación, ejecución, troubleshooting y dependencias.
- Crear `docs/architecture.md`, `docs/scene-format.md`, `docs/event-commands.md` y `docs/export-dreamcast.md`.
- Documentar invariantes clave: coordenadas de grid, orientación de cámara, unidades de altura, estados de combate y ciclo de vida de assets.

### 6. CI/CD, testing y gestión de dependencias

**Hallazgos**

- No hay `pyproject.toml`, `requirements.txt`, workflow de CI ni configuración de test runner.
- No se observan tests automatizados para serialización de escenas, carga de assets, comandos de eventos o reglas de combate.
- La presencia de dependencias GUI/OpenGL requiere separar tests headless de tests de integración visual.

**Recomendaciones**

- Añadir `pyproject.toml` con dependencias, `ruff`, `mypy` incremental y `pytest`.
- Crear CI mínima con jobs: `python -m compileall`, `ruff check`, `pytest`.
- Añadir tests headless iniciales:
  - serialización/deserialización de `Tile`, actores, sprites y escenas;
  - validación de comandos de eventos;
  - cálculo de turnos/daño/movimiento en combate;
  - resolución de rutas de assets sin crear contexto OpenGL.
- Separar pruebas de integración GUI/OpenGL detrás de marcador `pytest.mark.integration`.

## Hoja de ruta propuesta

### Fase 0: Higiene inmediata

- Añadir `.gitignore` y dejar de versionar caches/generados en próximos commits.
- Documentar dependencias y punto de entrada.
- Agregar `python -m compileall -q .` como check mínimo.

### Fase 1: Fundaciones de calidad

- Introducir `pyproject.toml`, `ruff`, `pytest` y CI.
- Crear paquete `motor_rpg` y mover módulos sin cambiar comportamiento.
- Eliminar imports wildcard empezando por `Toolkit.py`, `OpglManager.py` y `EventManager.py`.

### Fase 2: Separación arquitectónica

- Extraer modelos de dominio a dataclasses tipadas.
- Dividir `Toolkit.py` en controladores de UI, repositorios de assets, serialización y modo runtime.
- Dividir `RuntimeCombat.py` en estado, reglas, animaciones/cámara y presentación.
- Convertir eventos en command registry extensible y testeable.

### Fase 3: Rendimiento y robustez

- Implementar lazy loading y ResourceManager para OpenGL.
- Añadir validadores de escenas/assets y migraciones por versión.
- Añadir profiling de frame time/draw calls y pruebas de carga de assets grandes.

## Checks ejecutados durante la auditoría

- `python -m compileall -q .` terminó correctamente después de limpiar cachés generados localmente por la versión de Python del entorno.
- Se revisó la estructura con `find` y `rg --files` evitando recorridos recursivos pesados no filtrados.
- Se inspeccionaron manualmente módulos críticos: `Toolkit.py`, `OpglManager.py`, `RuntimeCombat.py`, `RuntimeSkill.py`, `TextureManager.py`, `EventManager.py` y `config.py`.
