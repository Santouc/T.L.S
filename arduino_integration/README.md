# Arduino Integration for Sign Language Recognition

Esta carpeta contiene el sistema de integración con Arduino para control de hardware basado en el reconocimiento de señas.

## Componentes

### 1. `arduino_bridge.py`
Puente de comunicación Python-Arduino con características avanzadas:
- Comunicación serial robusta
- Envío asíncrono de comandos
- Control de LEDs, buzzers, servos
- Manejo de múltiples dispositivos
- Reconexión automática

### 2. `arduino_sign_recognition.ino`
Sketch de Arduino para recibir y procesar comandos:
- Control de 10 LEDs (A-I + unknown)
- Buzzer tonal para confirmación
- 2 servos para acciones mecánicas
- Sistema de comandos flexible
- Timeout de inactividad

## Conexiones Hardware

### LEDs (Señas A-I + Unknown)
```
LED_A  -> Pin 2
LED_B  -> Pin 3
LED_C  -> Pin 4
LED_D  -> Pin 5
LED_E  -> Pin 6
LED_F  -> Pin 7
LED_G  -> Pin 8
LED_H  -> Pin 9
LED_I  -> Pin 10
LED_UNKNOWN -> Pin 11
```

### Actuadores
```
Buzzer -> Pin 12
Servo 1 -> Pin 9 (compartido con LED_H)
Servo 2 -> Pin 10 (compartido con LED_I)
```

### Opcional
```
Potenciómetro -> Pin A0 (para ajustes manuales)
```

## Uso Básico

### Python
```python
from arduino_integration.arduino_bridge import ArduinoBridge

# Conectar
bridge = ArduinoBridge('COM3')  # o '/dev/ttyUSB0' en Linux
if bridge.connect():
    # Enviar predicción
    bridge.send_prediction('A', 0.85)
    
    # Control directo
    bridge.send_led_command(2, True)  # Encender LED A
    bridge.send_buzzer_command(1000, 200)  # 1kHz por 200ms
    
    bridge.disconnect()
```

### Múltiples Dispositivos
```python
from arduino_integration.arduino_bridge import ArduinoController

controller = ArduinoController()
controller.add_device('principal', 'COM3', make_default=True)
controller.add_device('secundario', 'COM4')

controller.send_prediction_to_all('B', 0.9)
```

## Comandos Soportados

### Formato General
```
comando:parametro1:parametro2
```

### Comandos Disponibles
- `gesture_X:conf` - Muestra gesto X con confianza conf
- `led_on:X` - Enciende LED X
- `led_off:X` - Apaga LED X
- `buzzer:freq:ms` - Tono freq Hz por ms milisegundos
- `servo:X:angle` - Mueve servo X a angle grados
- `test` - Ejecuta secuencia de prueba
- `status` - Reporta estado actual
- `disconnect` - Limpia y desconecta

## Características Avanzadas

### Envío Asíncrono
```python
bridge.start_async_sender()  # Inicia thread de envío
bridge.send_prediction('C', 0.8, async_send=True)  # No bloqueante
```

### Manejo de Errores
- Reconexión automática
- Timeout de comunicación
- Buffer de comandos con cola
- Logging detallado

### Mapeo de Acciones
Cada seña puede mapear a múltiples acciones:
- LED visual
- Tono de confirmación (confianza > 0.8)
- Movimiento de servo
- Combinaciones personalizadas

## Instalación

### Python
```bash
pip install pyserial
```

### Arduino
1. Abrir `arduino_sign_recognition.ino` en Arduino IDE
2. Seleccionar placa (Arduino Uno, Nano, etc.)
3. Cargar sketch
4. Verificar conexión serial en Monitor Serie

## Troubleshooting

### Problemas Comunes
1. **Puerto no encontrado**: Verificar nombre de puerto (COM3, /dev/ttyUSB0)
2. **Comunicación fallida**: Revisar baudrate (9600 por defecto)
3. **Sin respuesta**: Resetear Arduino, verificar conexiones

### Debug
```python
# Ver estado detallado
status = bridge.get_status()
print(status)

# Ver respuesta de Arduino
response = bridge.read_response(timeout=2.0)
print(response)
```

## Integración con Sistema Principal

El puente Arduino está diseñado para integrarse fácilmente con el sistema de reconocimiento:

```python
# En el pipeline principal
from arduino_integration.arduino_bridge import ArduinoBridge

# Inicializar
arduino_bridge = ArduinoBridge('COM3')
arduino_bridge.connect()
arduino_bridge.start_async_sender()

# En el loop de predicción
def on_prediction(label, confidence):
    arduino_bridge.send_prediction(label, confidence)
```

## Extensiones Posibles

- Control de más actuadores (motores, relés)
- Comunicación inalámbrica (Bluetooth, WiFi)
- Interfaz web para control remoto
- Sistema de logging de acciones
- Modos de operación diferentes
