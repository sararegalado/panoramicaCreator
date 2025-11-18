# 📸 Panorama Creator - Estructura Modular

Sistema de creación de panoramas con captura desde iPhone y procesamiento automático.

## 🏗️ Arquitectura

El proyecto está organizado en módulos independientes y reutilizables:

```
panoramicaCreator/
│
├── main.py                    # 🚀 Punto de entrada principal
├── GUI.py                     # 🖼️  Interfaz gráfica (usa los módulos)
│
├── camera_manager.py          # 📷 Gestión de cámaras
├── capture_controller.py      # 🎬 Control de captura de secuencias
├── image_processor.py         # 🔧 Procesamiento y creación de panoramas
├── panorama_stitcher.py       # 🔗 Motor de stitching (core)
├── crop_panorama.py           # ✂️  Script standalone para recorte
│
├── output/                    # 📁 Panoramas generados
└── input/                     # 📁 Imágenes de entrada (opcional)
```

## 📦 Módulos

### 🚀 `main.py` - Punto de Entrada
**Propósito:** Lanza la aplicación completa.

**Uso:**
```bash
python main.py
```

---

### 📷 `camera_manager.py` - Gestión de Cámaras
**Responsabilidades:**
- Detectar cámaras disponibles
- Conectar/desconectar cámaras
- Leer frames
- Encontrar iPhone automáticamente

**Ejemplo:**
```python
from camera_manager import CameraManager

cam = CameraManager()
cameras = cam.find_cameras()  # [0, 1]
cam.connect(1)  # Conectar a iPhone
ret, frame = cam.read_frame()
```

**Métodos principales:**
- `find_cameras()` - Busca todas las cámaras
- `connect(index)` - Conecta a una cámara
- `read_frame()` - Lee un frame
- `find_iphone()` - Detecta iPhone automáticamente
- `disconnect()` - Desconecta cámara

---

### 🎬 `capture_controller.py` - Control de Captura
**Responsabilidades:**
- Capturar secuencias de fotos
- Control de intervalos y progreso
- Cargar imágenes desde archivos

**Ejemplo:**
```python
from capture_controller import CaptureController

controller = CaptureController(camera_manager)
controller.start_sequence(
    n_photos=5, 
    interval=2.0,
    callback_done=lambda success, images: print(f"Capturadas: {len(images)}")
)
```

**Métodos principales:**
- `start_sequence(n_photos, interval, callback_done)` - Inicia captura
- `stop_sequence()` - Detiene captura
- `load_images_from_files(paths)` - Carga desde archivos
- `get_images()` - Obtiene imágenes capturadas

---

### 🔧 `image_processor.py` - Procesamiento de Imágenes
**Responsabilidades:**
- Aplanamiento fotométrico
- Creación de panoramas
- Guardar resultados

**Ejemplo:**
```python
from image_processor import ImageProcessor

processor = ImageProcessor(output_dir="output")
panorama = processor.create_panorama(
    images=captured_images,
    apply_flattening=True,
    crop_borders=True
)
processor.save_panorama(panorama, prefix="panorama")
```

**Métodos principales:**
- `apply_photometric_flattening(images)` - Normaliza iluminación
- `create_panorama(images, ...)` - Crea panorama
- `save_panorama(panorama, prefix)` - Guarda resultado

---

### 🔗 `panorama_stitcher.py` - Motor de Stitching
**Responsabilidades:**
- Algoritmo de stitching OpenCV
- Recorte agresivo de bordes
- Estadísticas y visualización

**Ejemplo:**
```python
from panorama_stitcher import PanoramaStitcher

stitcher = PanoramaStitcher()
stitcher.load_images()
stitcher.create_panorama()
stitcher.crop_black_borders()
stitcher.save_results()
```

---

### 🖼️ `GUI.py` - Interfaz Gráfica
**Responsabilidades:**
- Interfaz de usuario Tkinter
- Integración de todos los módulos
- Preview en tiempo real

**Uso:** Se lanza automáticamente desde `main.py`

---

### ✂️ `crop_panorama.py` - Script de Recorte
**Responsabilidades:**
- Recorte standalone de panoramas existentes

**Uso:**
```bash
# Recorte básico
python crop_panorama.py output/panorama.png

# Sobrescribir original
python crop_panorama.py output/panorama.png --replace

# Más agresivo
python crop_panorama.py output/panorama.png --threshold 40
```

---

## 🎯 Flujo de Trabajo

### Desde la GUI:
```
main.py → GUI.py → Integra todos los módulos
                    ↓
                    camera_manager (detectar cámara)
                    ↓
                    capture_controller (capturar fotos)
                    ↓
                    image_processor (crear panorama)
                    ↓
                    Resultado guardado ✅
```

### Programáticamente:
```python
from camera_manager import CameraManager
from capture_controller import CaptureController
from image_processor import ImageProcessor

# 1. Configurar cámara
cam = CameraManager()
cam.connect(cam.find_iphone())

# 2. Capturar secuencia
controller = CaptureController(cam)
controller.start_sequence(5, 2.0)

# 3. Crear panorama
processor = ImageProcessor()
panorama = processor.create_panorama(controller.get_images())
processor.save_panorama(panorama)
```

---

## 🚀 Ejecutar Aplicación

```bash
# Método principal (recomendado)
python main.py

# Alternativa (directo)
python GUI.py
```

---

## 🔧 Características de la Arquitectura

### ✅ Ventajas
- **Modular:** Cada componente tiene una responsabilidad clara
- **Reutilizable:** Los módulos pueden usarse independientemente
- **Testeable:** Fácil de probar cada componente por separado
- **Mantenible:** Código organizado y fácil de entender
- **Extensible:** Añadir funcionalidades sin afectar otros módulos

### 📝 Separación de Responsabilidades
- **camera_manager:** Solo maneja hardware (cámaras)
- **capture_controller:** Solo maneja secuencias de captura
- **image_processor:** Solo maneja procesamiento de imágenes
- **GUI:** Solo maneja interfaz de usuario
- **main:** Solo punto de entrada

---

## 📚 Documentación

Cada módulo incluye:
- Docstrings detallados
- Ejemplos de uso
- Parámetros explicados
- Valores de retorno claros

---

## 🎓 Universidad de Deusto - Visión por Computador 2025-2026

**Proyecto:** Creación Automática de Panoramas con iPhone
