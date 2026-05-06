# Traductor de Lenguaje de Señas Chileno para Arduino UNO Q

Sistema embebido con **MediaPipe Hands** para traducción precisa del alfabeto manual del lenguaje de señas chileno a voz en tiempo real.

## Características Principales

- **MediaPipe Hands**: Detección robusta con 21 landmarks precisos
- **Cálculo 3D**: Ángulos articulares exactos usando coordenadas (x,y,z)
- **Optimizado para Arduino UNO Q**: 9-15 FPS en hardware ARM64
- **Clasificación híbrida**: Reglas lógicas + ML escalable
- **Voz natural**: espeak-ng con soporte para español

## Requisitos de Hardware

- Arduino UNO Q (2-4GB RAM, Debian Linux ARM64)
- Cámara USB compatible con Linux (preferiblemente 720p)
- Altavoces o auriculares

## Instalación Rápida

### Script Automático (Recomendado)

```bash
# Hacer ejecutable el script
chmod +x install_mediapipe_arm64.sh

# Ejecutar instalación
./install_mediapipe_arm64.sh
```

### Instalación Manual

#### 1. Instalar dependencias del sistema

```bash
sudo apt update
sudo apt install python3-pip espeak-ng espeak-ng-espanol libttspico-utils python3-dev cmake build-essential
```

#### 2. Instalar MediaPipe para ARM64

**Método A: Wheels precompilados**
```bash
cd /tmp
git clone https://github.com/PINTO0309/mediapipe-bin.git
cd mediapipe-bin
chmod +x ./v0.8.4/download.sh && ./v0.8.4/download.sh
pip3 install mediapipe-*.whl
```

**Método B: Compilación desde fuente** (2-3 horas)
```bash
# Seguir guía en: https://github.com/jiuqiant/mediapipe_python_aarch64
```

#### 3. Instalar dependencias Python

```bash
pip3 install -r requirements.txt
```

### 3. Configurar cámara

Asegúrate que la cámara sea reconocida:

```bash
ls /dev/video*
# Debería mostrar /dev/video0 o similar
```

## Uso

### Ejecutar el traductor

```bash
python3 traductor_senas.py
```

### Controles

- **q**: Salir del programa
- **c**: Limpiar texto acumulado
- **s**: Hablar texto acumulado manualmente

### Letras soportadas (Fase 1)

- **A**: Puño cerrado [0,0,0,0,0]
- **B**: Mano abierta [1,1,1,1,1]
- **C**: Media curva [0,1,1,1,1]
- **D**: Solo índice extendido [1,1,0,0,0]
- **E**: Índice y pulgar [0,1,0,0,0]
- **F**: Todos menos meñique [1,1,1,1,0]
- **G**: Índice apuntando [1,1,0,0,0]
- **H**: Índice y medio [1,1,1,0,0]

## Arquitectura del Sistema

### Flujo de Datos Optimizado

```
Cámara USB --> MediaPipe Hands --> 21 Landmarks 3D --> Cálculo Ángulos Precisos --> Vector 5D --> Clasificación --> Texto --> Voz
```

### Componentes Principales

1. **HandDetector**: MediaPipe Hands para 21 landmarks precisos
2. **FingerAngleCalculator**: Cálculo 3D de ángulos articulares
3. **SignClassifier**: Clasificación híbrida (reglas + ML)
4. **TTSManager**: Conversión texto a voz con espeak-ng

### Rendimiento Esperado en Arduino UNO Q

| Configuración | FPS | Uso CPU | Uso RAM |
|---------------|-----|---------|---------|
| 640x480, 15 FPS | 9-12 | 60-70% | 800MB |
| 480x360, 15 FPS | 12-15 | 45-55% | 650MB |
| 320x240, 15 FPS | 15-20 | 30-40% | 500MB |

## Configuración

### Ajustar parámetros de detección

En `HandDetector.__init__()` puedes modificar:

```python
# Resolución de captura
self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Rango de detección de piel (HSV)
self.lower_skin = np.array([0, 20, 70], dtype=np.uint8)
self.upper_skin = np.array([20, 255, 255], dtype=np.uint8)
```

### Agregar nuevas letras

En `SignClassifier.__init__()`:

```python
self.rules['N'] = [1, 0, 0, 0, 1]  # Pulgar y meñique extendidos
```

## Optimización para Arduino UNO Q

- Resolución reducida a 640x480
- FPS limitado a 15 para reducir carga
- Procesamiento asíncrono de TTS
- Buffer de detección para estabilidad

## Próximos Pasos

1. **Fase 2**: Agregar más letras al sistema de reglas
2. **Fase 3**: Colectar datos y entrenar modelo ML
3. **Fase 4**: Implementar reconocimiento de palabras completas
4. **Fase 5**: Optimización para mejor rendimiento

## Troubleshooting

### Problemas comunes

- **Cámara no detectada**: Verificar permisos y conexión USB
- **Baja detección**: Ajustar rangos de HSV o iluminación
- **Audio no funciona**: Instalar drivers de audio o probar con altavoces externos

### Logs de depuración

El sistema muestra información en consola:
- Letras detectadas
- Texto acumulado
- FPS del sistema

## Licencia

Proyecto educativo para desarrollo de sistemas embebidos.
