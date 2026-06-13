# Sistema de Reconocimiento de Señas - Guía Completa

Sistema completo de reconocimiento de lenguaje de señas con TensorFlow, MediaPipe y múltiples opciones de deployment.

## 📋 Índice

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso Rápido](#uso-rápido)
- [Entrenamiento](#entrenamiento)
- [Componentes](#componentes)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Arquitectura](#arquitectura)

## 🌟 Características

### Core Features
- **Reconocimiento en tiempo real** con MediaPipe Hands
- **Modelo TensorFlow** para clasificación de señas
- **Preprocesamiento optimizado** con normalización
- **Multiplataforma** Desktop, Edge, Mobile
- **API REST + WebSocket** para integración
- **Sistema de evaluación** completo con métricas

### Advanced Features
- **Data pipeline** completo: captura → procesamiento → entrenamiento
- **Real-time optimization** con smoothing temporal
- **Production API** con autenticación y monitoreo
- **Docker deployment** listo para producción

## 📦 Requisitos

### Software
- **Python 3.8+**
- **TensorFlow 2.13+**
- **OpenCV 4.5+**
- **MediaPipe**
- **FastAPI** (para API)

### Hardware
- **Cámara web** o cámara integrada
- **CPU** moderna (GPU opcional)
- **4GB+ RAM** recomendado

## 🔧 Instalación

### 1. Clonar el repositorio
```bash
git clone <repositorio>
cd mimo
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Verificar instalación
```bash
python --version  # Debe ser 3.8+
py --version      # Alternativa en Windows
```

## 🚀 Uso Rápido

### Ejecutar sistema principal
```bash
py main.py
```

**Controles:**
- **'q'**: Salir del programa
- **ESC**: Cerrar ventana

**Lo que verás:**
- Ventana con cámara en tiempo real
- Detección de manos con landmarks
- Predicción de señas en pantalla
- FPS y confianza de predicción

## 🎯 Entrenamiento

### Paso 1: Capturar Datos
```bash
py teaching.py
```

**Controles:**
- **'S'**: Guardar muestra actual
- **'N'**: Siguiente etiqueta
- **'ESC'**: Salir y guardar

**Meta:** 200-300 muestras por clase

### Paso 2: Procesar Dataset
```bash
py ml/data_processor.py
```

**Procesos:**
- Limpieza de datos inválidos
- Eliminación de duplicados
- Augmentación (ruido, rotación, escala)
- Balanceo de clases

### Paso 3: Entrenar Modelo
```bash
py ml/train.py
```

**Resultados:**
- `data/models/model.h5`
- `data/models/labels.json`
- Accuracy > 90% esperado

### Paso 4: Evaluar Modelo
```bash
py ml/model_evaluator.py
```

**Métricas:**
- Accuracy general
- Matriz de confusión
- Precision/Recall/F1
- Análisis de errores

### Paso 5: Probar Sistema
```bash
py main.py
```

## 📁 Componentes

### Core System
```
main.py                    # Sistema principal
teaching.py                # Captura interactiva de datos
core/                      # Detección, imagen y utilidades centrales
ml/                        # Clasificador, entrenamiento y evaluación
data/datasets/             # Datasets JSON
data/models/               # Modelo, labels y hand_landmarker.task
utils/                     # Configuración y logging
```

### Advanced Components
```
api/                      # API de producción
├── main.py              # FastAPI server
├── client_examples.py   # Clientes ejemplo
├── Dockerfile          # Containerización
└── docker-compose.yml  # Orquestación

```

## 🌐 Deployment

### API REST + WebSocket
```bash
cd api
py main.py
# Acceder a http://localhost:8000
```

**Endpoints:**
- `POST /predict` - Predicción individual
- `WebSocket /ws` - Streaming en tiempo real
- `GET /stats` - Estadísticas del sistema

### Docker Production
```bash
cd api
docker-compose up -d
```


### Edge Deployment (TFLite)
```python
from ml.deployment_manager import EdgeRuntime

runtime = EdgeRuntime("model.tflite", "labels.json")
result = runtime.predict(landmarks)
```

## 📊 Métricas y Monitoreo

### Performance Targets
- **Latency**: < 30ms (Desktop), < 40ms (Edge)
- **FPS**: 20+ (real-time)
- **Accuracy**: > 90% (con buen dataset)
- **Memory**: < 500MB (Desktop), < 100MB (TFLite)

### Monitoring
- **Request statistics** (API)
- **Model performance** (evaluator)
- **System health** (health checks)
- **Error tracking** (logging)

## 🔧 Configuración

### Model Parameters
```python
# En ml/train.py
model.fit(X, y, epochs=20, batch_size=32, validation_split=0.2)
```

### Confidence Threshold
```python
# En ml/clasificador.py
if confidence < 0.6:  # Ajustar según necesidad
    return "unknown", confidence
```

### Camera Settings
```python
# En main.py
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 15)
```

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. "No hay modelo disponible"
**Causa:** No existe `model.h5` o `labels.json`
**Solución:**
```bash
py ml/train.py
```

#### 2. Error de cámara
**Causa:** Cámara no encontrada o en uso
**Solución:**
```python
# Intentar diferentes índices
cap = cv2.VideoCapture(1)  # o 2, 3...
```

#### 3. Baja precisión
**Causa:** Dataset pequeño o de mala calidad
**Solución:**
- Capturar más datos (200+ muestras por clase)
- Mejorar iluminación y fondo
- Aumentar epochs de entrenamiento

#### 4. Alta latencia
**Causa:** Hardware limitado
**Solución:**
- Usar TFLite: `ml/deployment_manager.py`
- Reducir resolución de cámara
- Aumentar frame skipping

### Debug Mode
```python
# Habilitar logging detallado
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🏗️ Arquitectura

### Data Flow
```
Camera → MediaPipe → Landmarks → Preprocess → Model → Prediction → UI/API
```

### Model Architecture
```
Input (21, 3) → Dense(64) → Dense(128) → Dense(num_classes) → Softmax
```

### Processing Pipeline
```
Raw Data → Clean → Augment → Balance → Train → Evaluate → Deploy
```

## 📚 Referencias

### MediaPipe
- [MediaPipe Hands Documentation](https://google.github.io/mediapipe/solutions/hands.html)
- [Hand Landmarks Guide](https://google.github.io/mediapipe/solutions/hands.html#hand_landmarks)

### TensorFlow
- [Keras Sequential API](https://www.tensorflow.org/guide/keras/sequential_model)
- [Model Training Guide](https://www.tensorflow.org/guide/keras/training_and_evaluation)

### Computer Vision
- [OpenCV Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [Real-time Computer Vision](https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html)

## 🤝 Contribución

### Development Setup
```bash
# Clonar repositorio
git clone <repositorio>
cd mimo

# Instalar dependencias de desarrollo
pip install -r requirements.txt
pip install pytest black flake8

# Ejecutar tests
pytest tests/

# Formatear código
black .
```

### Pull Request Process
1. Fork del repositorio
2. Feature branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -am 'Agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Pull Request

## 📄 Licencia

MIT License - ver archivo LICENSE para detalles.

## 🆘 Soporte

### Issues y Bugs
- **GitHub Issues**: Reportar bugs y feature requests
- **Discussions**: Preguntas y discusiones técnicas
- **Documentation**: Mejoras a la documentación

### Contacto
- **Email**: [tu-email@ejemplo.com]
- **Twitter**: [@tu-twitter]
- **LinkedIn**: [tu-linkedin]

---

## 🎯 Quick Start Summary

```bash
# 1. Instalación
pip install -r requirements.txt

# 2. Entrenamiento (opcional - usa modelo demo por defecto)
py teaching.py            # Capturar datos
py ml/data_processor.py   # Procesar datos
py ml/train.py            # Entrenar modelo

# 3. Ejecutar sistema
py main.py

# 4. API (opcional)
cd api && py main.py
```

**¡Listo!** El sistema está operativo y reconociendo señas en tiempo real.
