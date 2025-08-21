# Tidal Top7

Una herramienta de Python que crea automáticamente playlists en TIDAL con el Top 7 de canciones de una lista de artistas definidos.

## 🎵 Descripción

Este proyecto demuestra cómo usar Python y la biblioteca `tidalapi` para crear playlists personalizadas en TIDAL. La herramienta toma una lista de artistas (desde un archivo de texto o línea de comandos) y crea una playlist con las 7 canciones más populares de cada artista.

## ✨ Características

- 🔍 Búsqueda robusta de artistas con múltiples variantes de nombres
- 🎯 Obtiene automáticamente las 7 canciones más populares de cada artista
- 📝 Crea playlists con nombre y descripción personalizados
- 🔄 Manejo de errores y compatibilidad con diferentes versiones de tidalapi
- 🚀 Interfaz de línea de comandos simple y fácil de usar

## 📋 Requisitos

- Python 3.10 o superior
- Cuenta de TIDAL Premium
- Poetry (para gestión de dependencias)

## 🚀 Instalación

1. **Clona el repositorio:**

   ```bash
   git clone <url-del-repositorio>
   cd tidal-top7
   ```

2. **Instala las dependencias:**
   ```bash
   poetry install
   ```

## 🔧 Configuración

Antes de usar la herramienta, necesitas configurar la autenticación de TIDAL:

1. **Configura las credenciales de TIDAL:**
   La herramienta usa autenticación OAuth simple. En la primera ejecución, se abrirá un navegador para autenticarte con tu cuenta de TIDAL.

## 📖 Uso

### Comando Básico

```bash
poetry run tidal-top7 --artists-file artists.txt --playlist-name "Alt 90s Top7"
```

### Opciones Disponibles

- `--artists-file`: Archivo de texto con un artista por línea
- `--artists`: Lista de artistas separados por comas
- `--playlist-name`: Nombre de la playlist (requerido)
- `--playlist-desc`: Descripción de la playlist (opcional)
- `--debug`: Muestra logs de depuración

### Ejemplos de Uso

**Usando un archivo de artistas:**

```bash
poetry run tidal-top7 --artists-file artists.txt --playlist-name "Alt 90s Top7"
```

**Usando lista directa de artistas:**

```bash
poetry run tidal-top7 --artists "Third Eye Blind, Matchbox 20, Fuel" --playlist-name "90s Rock Hits"
```

**Con descripción personalizada:**

```bash
poetry run tidal-top7 --artists-file artists.txt --playlist-name "Alt 90s Top7" --playlist-desc "Las mejores canciones de los 90s alternativos"
```

## 📁 Estructura del Proyecto

```
tidal-top7/
├── src/
│   └── tidal_top7/
│       ├── __init__.py
│       └── main.py          # Lógica principal de la aplicación
├── tests/                   # Tests unitarios
├── artists.txt             # Lista de artistas de ejemplo
├── pyproject.toml          # Configuración de Poetry
├── poetry.lock            # Dependencias bloqueadas
└── README.md              # Este archivo
```

## 🎯 Archivo artists.txt

El archivo `artists.txt` contiene una lista de artistas, uno por línea. Ejemplo:

```
Third Eye Blind
Matchbox 20
Better than ezra
Vertical Horizon
VAST
splender
Dishwalla
Pilot Speed
Pilate
Black Lab
Civil Twilight
Neverending White Lights
The Watchmen
The Verve Pipe
Moses Mayfield
Green or Blue
Harvard of the South
Emerson Hart
Thornley
Gin Blossoms
Tonic
Our Lady Peace
Toad The Wet Sprocket
Matthew Good
Matthew Good Band
Fuel
Collective Soul
```

## 🔧 Desarrollo

### Instalación para desarrollo

```bash
poetry install
```

### Ejecutar tests

```bash
poetry run pytest
```

### Ejecutar con modo debug

```bash
poetry run tidal-top7 --artists-file artists.txt --playlist-name "Test Playlist" --debug
```

## 📦 Dependencias

- `tidalapi`: Cliente de Python para la API de TIDAL
- `python-dotenv`: Manejo de variables de entorno
- `argparse`: Parsing de argumentos de línea de comandos

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## ⚠️ Notas Importantes

- Necesitas una cuenta de TIDAL Premium para usar esta herramienta
- La herramienta respeta los límites de rate de la API de TIDAL
- Algunos artistas pueden no estar disponibles en TIDAL o tener nombres diferentes
- Las playlists se crean como públicas por defecto

## 🐛 Solución de Problemas

### Error de autenticación

Si tienes problemas con la autenticación, asegúrate de tener una cuenta de TIDAL Premium válida.

### Artista no encontrado

La herramienta intenta múltiples variantes de nombres, pero algunos artistas pueden no estar disponibles en TIDAL. Revisa los logs de debug para más información.

### Problemas de red

Asegúrate de tener una conexión a internet estable para acceder a la API de TIDAL.

---

¡Disfruta creando tus playlists personalizadas en TIDAL! 🎵
