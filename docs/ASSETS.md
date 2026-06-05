# Política de assets

Esta política mantiene reproducible la carga de recursos del editor/runtime y evita
referencias accidentales fuera del proyecto.

## Raíces permitidas

Los assets versionados deben vivir en una de estas carpetas:

- `cd/`
- `export_dc/`
- `fonts/`
- `music/`
- `obj/`
- `png/`
- `scenes/`
- `sprites/`
- `textures/`

## Extensiones permitidas

La configuración tipada acepta únicamente: `.bmp`, `.c`, `.jpg`, `.jpeg`, `.json`, `.kra`, `.mp3`, `.mtl`, `.obj`,
`.otf`, `.png`, `.ttf`, `.txt` y `.wav`.

## Tamaño máximo

Cada archivo individual debe pesar menos de 25 MiB salvo aprobación explícita. Los
paquetes o zips históricos no deben usarse como entrada del runtime activo.

## Manifiestos

Los manifiestos JSON deben declarar una lista `assets` con rutas relativas al
manifiesto o al root usado por el cargador. Cada entrada puede ser una cadena o un
objeto con `path`/`file`/`src` y `kind`/`type`.

## Validación local

```bash
python tools/validate_assets.py
```
