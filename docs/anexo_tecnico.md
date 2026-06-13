# Anexo técnico del sistema de captura y reconocimiento

Este documento consolida la información técnica relevante del sistema (captura `teaching.py`, entrenamiento `ml/train.py` y `ml/train_dynamic.py`, e inferencia `main.py`). Está pensado para mantenimiento y revisión técnica, sin depender del código fuente.

## 1) Arquitectura general
- Cámara (video) → Detección de mano → Extracción de 21 landmarks (x,y,z) → Preprocesamiento/estabilización →
  - Clasificador estático (por cuadro)
  - Clasificador dinámico (por secuencia de cuadros)
- Entradas/salidas clave:
  - Entrada de modelos: landmarks normalizados (estático: `(21,3)`, dinámico: `(T,21,3)`).
  - Salida: distribución de probabilidad sobre clases (`labels`).

### 1.1 Módulos principales
- `core/hand_detector.py`: Detección de mano y landmarks (MediaPipe Hands). Modo de ejecución optimizado (VIDEO) y control de FPS.
- `core/image_processor.py`: Redimensionado, recortes y utilidades de imagen.
- `core/preprocessing.py`: `normalize_landmarks()` para normalizar traslación/escala sobre `(21,3)`.
- `ml/clasificador.py`: Carga y predicción del modelo estático (`model.h5` + `labels.json`).
- `ml/dynamic_classifier.py`: Carga y predicción del modelo dinámico (`model_dynamic.h5` + `labels_dynamic.json`).
- `ml/train.py`: Entrenamiento estático desde `dataset_static.json` (o `dataset_final.json` si no existe el primero).
- `ml/train_dynamic.py`: Entrenamiento dinámico desde `dataset_dynamic.json`.
- `utils/logger.py`: `get_logger()` para logs consistentes.
- `main.py`: Loop principal de inferencia (muestra resultado Estático y, si existe, Dinámico).
- `teaching.py`: Sistema de captura interactiva (estático y dinámico) con FSM.

## 2) Máquina de Estados (FSM) en teaching.py
Estados:
- `STATE_CAMERA = 0`  → Inactivo/preview con inferencia en vivo y overlay.
- `STATE_MENU = 1`    → Menú para seleccionar etiqueta.
- `STATE_CAPTURE = 2` → Captura estática (muestras por cuadro).
- `STATE_RECORDING = 3` → Grabación de secuencias dinámicas.

Controles del teclado:
- `m`: Abrir/cerrar menú.
- `Flechas arriba/abajo`: Navegar menú.
- `Enter`: Confirmar selección.
- `s`: Cambiar modo (estático/dinámico).
- `t`: Capturar (estático) / Iniciar-Detener (dinámico).
- `q`: Salir y guardar datasets.

Indicadores típicos (overlay/logs):
- Estado del sistema (CÁMARA / MENÚ / CAPTURANDO / GRABANDO).
- Etiqueta actual y contadores de dataset.
- Mensajes de guardado: muestra estática/secuencia dinámica/datasets guardados.
- Tracking: OK / RECUPERANDO / PERDIDO.

## 3) Datos y formatos
### 3.1 Landmarks
- 21 puntos por mano, con coordenadas `(x,y,z)` normalizadas.
- Orden y significado anatómico (wrist, MCP/PIP/DIP/punta por dedo), ver detalle conceptual en `docs/conceptos.md`.

### 3.2 Datasets
Ubicación: `data/datasets/`

- `dataset_static.json` (estático):
```jsonc
{
  "X": [ [ [x,y,z], [x,y,z], ... 21 pts ] , ... N muestras ],
  "y": [ 0, 1, 0, ... ],           // índices de clase
  "labels": ["A", "B", "C", ...],
  "metadata": {
    "type": "static",
    "num_samples": N,
    "landmark_format": "mediapipe_21_3d",
    "coordinate_system": "normalized"
  }
}
```

- `dataset_dynamic.json` (dinámico):
```jsonc
{
  "X": [  // N secuencias
    [  // secuencia 1 (T frames)
      [ [x,y,z], ... 21 pts ],
      ... T frames
    ],
    ... N secuencias
  ],
  "y": [ 0, 1, ... ],
  "labels": ["A", "B", ...],
  "metadata": {
    "type": "dynamic",
    "num_samples": N,
    "sequence_length": T,
    "landmark_format": "mediapipe_21_3d",
    "coordinate_system": "normalized"
  }
}
```
Notas:
- En entrenamiento dinámico se compactan clases usadas si el dataset no contiene todas las clases declaradas.
- Las muestras deben tener exactamente 21 puntos por frame.

## 4) Preprocesamiento y robustez
- `normalize_landmarks()`: normaliza traslación/escala por muestra (y por frame en el caso dinámico mediante aplanado-temporal y reshaping).
- Suavizado (smoothing) de landmarks en vivo para reducir jitter.
- Tolerancia a frames perdidos: se reutiliza el último válido por unos cuadros antes de declarar “PERDIDO”.

## 5) Modelos y entrenamiento
### 5.1 Modelo estático (`ml/train.py`)
- Entrada: `(21, 3)`
- Arquitectura:
  - Dense(64, relu) → Flatten → Dense(128, relu) → Dense(num_classes, softmax)
- Compilación: `optimizer='adam'`, `loss='sparse_categorical_crossentropy'`, `metrics=['accuracy']`
- Entrenamiento: `epochs=50`, `batch_size=min(8, len(X))`, `validation_split=0.2`
- Preprocesamiento previo: `normalize_landmarks(X)`
- Salidas guardadas: `data/models/model.h5`, `data/models/labels.json`
- Fallback de dataset: usa `data/datasets/dataset_static.json` o `data/datasets/dataset_final.json` si el primero no existe.

### 5.2 Modelo dinámico (`ml/train_dynamic.py`)
- Entrada: `(T, 21, 3)`
- Arquitectura:
  - TimeDistributed(Dense(64, relu)) → TimeDistributed(Flatten) →
  - BiLSTM(64, return_sequences=True) → Dropout(0.3) → BiLSTM(32) →
  - Dense(64, relu) → Dropout(0.3) → Dense(num_classes, softmax)
- Compilación: Adam(lr=0.001), `loss='sparse_categorical_crossentropy'`, `metrics=['accuracy']`
- Entrenamiento: `epochs=80`, `batch_size=min(8, len(X))`, `validation_split=0.2` (si hay ≥10 secuencias)
- Preprocesamiento previo: normalización por frame vía `normalize_dynamic_sequences()`
- Salidas guardadas: `data/models/model_dynamic.h5`, `data/models/labels_dynamic.json`

## 6) Inferencia en vivo (`main.py`)
- Carga modelos disponibles (estático obligatorio, dinámico si existe).
- Mantiene buffer temporal para el dinámico (p. ej., 20 frames) y estabiliza predicciones.
- Muestra en overlay: predicción Estático, predicción Dinámico (si procede) y estado de tracking.

## 7) Rutas y archivos relevantes
- Datasets: `data/datasets/dataset_static.json`, `data/datasets/dataset_dynamic.json`, `data/datasets/dataset_final.json` (fallback estático).
- Modelos: `data/models/model.h5`, `data/models/labels.json`, `data/models/model_dynamic.h5`, `data/models/labels_dynamic.json`.
- Detector de mano: `data/models/hand_landmarker.task`.

## 8) Logging y mensajes
- Uso de `utils.logger.get_logger()` para mensajes estructurados (info/warning/error).
- Mensajes típicos en consola/overlay:
  - Inicio del sistema de captura.
  - Controles disponibles.
  - Guardado de capturas/seq. y datasets (con conteos).
  - Advertencias: “Landmarks incompletos: X/21”, errores de cámara.

## 9) Rendimiento y consideraciones
- Resolución de cámara ajustada (ej. 320×240) para mejorar FPS en vivo.
- Consumo típico (orientativo): inferencia ~700–1,200 MB RAM; entrenamiento puede requerir varios GB.
- Evitar que otras apps usen la cámara; añadir selector de dispositivo si se dispone de varias cámaras.

## 10) Personalización y mantenimiento
- Etiquetas: cambiar nombres en `labels.json` afecta solo la visualización; agregar/eliminar clases requiere reentrenar.
- Textos de overlay/console: ubicados en funciones de UI y en llamadas a logger dentro de `teaching.py` y `main.py`.
- Cambios en FPS, smoothing o tolerancia de tracking: parámetros en `main.py`/`teaching.py` y módulos `core/*`.

---
Última actualización automática de especificaciones de entrenamiento tomada de los scripts actuales (`ml/train.py`, `ml/train_dynamic.py`).
