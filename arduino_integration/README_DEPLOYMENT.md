# Deployment Integration with Arduino

Este archivo integra el sistema de deployment con el control de hardware Arduino, proporcionando un pipeline completo desde el reconocimiento de señas hasta la actuación física.

## Componentes de Integration

### 1. `deployment_integration.py`
Sistema unificado que conecta:
- **Model Runtime**: Desktop (TensorFlow) o Edge (TFLite)
- **Arduino Controller**: Comunicación y control de hardware
- **Unified Pipeline**: Interfaz única para predicción + control

### 2. `arduino_bridge.py`
Puente de comunicación Python-Arduino (ver README.md principal)

### 3. `arduino_sign_recognition.ino`
Sketch de Arduino para recibir comandos (ver README.md principal)

## Arquitectura de Deployment

```
[Camera] → [MediaPipe] → [Landmarks] → [Runtime Model]
    ↓
[Prediction] → [Arduino Controller] → [Hardware Actions]
```

## Uso del Sistema Integrado

### Configuración Básica
```python
from deployment_integration import UnifiedDeploymentPipeline

# Configuración con Arduino
arduino_config = {
    "port": "COM3",        # o "/dev/ttyUSB0" en Linux
    "baudrate": 9600,
    "make_default": True
}

# Pipeline unificado
pipeline = UnifiedDeploymentPipeline(
    model_path="model.tflite",
    labels_path="labels.json", 
    platform="edge",
    arduino_config=arduino_config
)
```

### Predicción y Control Automático
```python
# Predice y envía automáticamente a Arduino
label, confidence = pipeline.predict_and_send(landmarks)

# El sistema automáticamente:
# 1. Preprocesa landmarks
# 2. Ejecuta inferencia del modelo
# 3. Envía predicción a Arduino
# 4. Arduino ejecuta acciones (LEDs, buzzer, servos)
```

### Control Manual de Hardware
```python
# Control directo de actuadores
pipeline.send_arduino_command("led", 2, True)      # Encender LED A
pipeline.send_arduino_command("led", 2, False)     # Apagar LED A
pipeline.send_arduino_command("buzzer", 1000, 200) # 1kHz por 200ms
pipeline.send_arduino_command("servo", 1, 90)     # Servo 1 a 90°
```

## Plataformas Soportadas

### Desktop (TensorFlow)
```python
pipeline = UnifiedDeploymentPipeline(
    "model.h5", "labels.json", 
    platform="desktop",
    arduino_config=arduino_config
)
```

### Edge (TFLite)
```python
pipeline = UnifiedDeploymentPipeline(
    "model.tflite", "labels.json",
    platform="edge", 
    arduino_config=arduino_config
)
```

## Flujo Completo de Deployment

### 1. Exportación de Modelos
```python
from deployment_integration import ModelExporter

exporter = ModelExporter(trained_model, labels)
exporter.export_all_formats("deployment_package")
```

### 2. Configuración del Sistema
```python
# Cargar runtime y Arduino
pipeline = UnifiedDeploymentPipeline(
    "deployment_package/model.tflite",
    "deployment_package/model.tflite_labels.json",
    platform="edge",
    arduino_config={"port": "COM3", "baudrate": 9600}
)
```

### 3. Operación en Tiempo Real
```python
while True:
    landmarks = get_landmarks_from_mediapipe()
    
    if landmarks is not None:
        # Predicción + control automático
        label, conf = pipeline.predict_and_send(landmarks)
        
        # Mostrar resultado
        print(f"Seña: {label} (confianza: {conf:.2f})")
```

### 4. Limpieza
```python
pipeline.cleanup()  # Desconecta Arduino
```

## Características Avanzadas

### Estado del Sistema
```python
status = pipeline.get_status()
print(status)
# {
#     "platform": "edge",
#     "runtime_ready": True,
#     "arduino_connected": True,
#     "arduino_status": {
#         "main": {
#             "connected": True,
#             "port": "COM3",
#             "queue_size": 0
#         }
#     }
# }
```

### Múltiples Dispositivos Arduino
```python
# Configurar múltiples Arduinos
arduino_config = {
    "port": "COM3",
    "baudrate": 9600,
    "make_default": True
}

pipeline = UnifiedDeploymentPipeline("model.tflite", "labels.json", "edge", arduino_config)

# Agregar segundo dispositivo
pipeline.arduino_controller.add_device("secondary", "COM4")

# Enviar a todos
pipeline.arduino_controller.send_prediction_to_all("A", 0.9)
```

## Mapeo de Acciones

### Señas → Hardware
| Seña | LED | Buzzer | Servo | Frecuencia |
|------|-----|--------|-------|-----------|
| A | LED_A (Pin 2) | 440 Hz | Servo 1 → 0° | Nota A4 |
| B | LED_B (Pin 3) | 494 Hz | Servo 1 → 180° | Nota B4 |
| C | LED_C (Pin 4) | 523 Hz | Servo 2 → 0° | Nota C5 |
| D | LED_D (Pin 5) | 587 Hz | Servo 2 → 180° | Nota D5 |
| E | LED_E (Pin 6) | 659 Hz | - | Nota E5 |
| F | LED_F (Pin 7) | 698 Hz | - | Nota F5 |
| G | LED_G (Pin 8) | 784 Hz | - | Nota G5 |
| H | LED_H (Pin 9) | 880 Hz | - | Nota A5 |
| I | LED_I (Pin 10) | 988 Hz | - | Nota B5 |
| Unknown | LED_UNKNOWN (Pin 11) | - | - | - |

### Reglas de Activación
- **LED siempre**: Se enciende LED correspondiente
- **Buzzer**: Solo si confianza > 0.8
- **Servos**: Movimiento específico por seña
- **Timeout**: Apagado automático después de 5s

## Troubleshooting

### Problemas Comunes
1. **Arduino no responde**: Verificar puerto y baudrate
2. **Modelo no carga**: Revisar formato (.h5 vs .tflite)
3. **Predicciones incorrectas**: Verificar preprocesamiento consistente
4. **Hardware no funciona**: Revisar conexiones y alimentación

### Debug
```python
# Ver estado detallado
status = pipeline.get_status()
print(json.dumps(status, indent=2))

# Ver respuesta Arduino
if pipeline.arduino_controller:
    response = pipeline.arduino_controller.default_device.read_response()
    print(f"Arduino response: {response}")
```

## Performance

### Latencias Esperadas
- **Desktop**: < 20ms (TensorFlow)
- **Edge**: < 40ms (TFLite)
- **Arduino**: < 10ms (Serial)
- **Total**: < 50ms end-to-end

### Optimizaciones
- **Frame skipping**: Reducir cómputo si es necesario
- **Async Arduino**: Cola de comandos no bloqueante
- **Model cuantizado**: TFLite con optimizaciones

## Ejemplos de Aplicación

### 1. Sistema de Ayuda para Sordos
- Reconoce señas y muestra en pantalla
- Feedback táctil con vibración (servo)
- Confirmación audio con buzzer

### 2. Control Domótico por Señas
- A: Encender luces
- B: Apagar luces  
- C: Subir temperatura
- D: Bajar temperatura

### 3. Sistema Educativo
- Reconoce práctica de señas
- Feedback visual inmediato (LEDs)
- Puntuación basada en precisión

## Extensión del Sistema

### Agregar Nuevos Actuadores
```python
# En arduino_sign_recognition.ino
void executeGesture(String gesture, float confidence) {
    // Agregar nuevo mapeo aquí
    if (gesture == "custom_gesture") {
        // Nueva acción
    }
}
```

### Personalizar Mapeo
```python
# Modificar action_mapping en arduino_bridge.py
bridge.action_mapping["custom"] = "custom_action"
```

### Agregar Nuevos Comandos
```python
# Comandos personalizados
pipeline.send_arduino_command("custom", param1, param2)
```
