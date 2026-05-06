#!/usr/bin/env python3
"""
Sistema de deployment para múltiples plataformas
Desktop, Edge (Raspberry Pi/Jetson), Mobile (Android), Arduino integration
"""

import os
import json
import time
import serial
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import logging

# Importaciones de TensorFlow
try:
    import tensorflow as tf
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    logging.warning("TensorFlow no disponible")

# Importaciones de TFLite Runtime
try:
    import tflite_runtime.interpreter as tflite
    HAS_TFLITE_RUNTIME = True
except ImportError:
    HAS_TFLITE_RUNTIME = False
    logging.warning("TFLite Runtime no disponible")

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelExporter:
    """Sistema de exportación de modelos para diferentes plataformas"""
    
    def __init__(self, model, labels: List[str]):
        """
        Inicializa exportador de modelos
        
        Args:
            model: Modelo TensorFlow/Keras entrenado
            labels: Lista de nombres de clases
        """
        self.model = model
        self.labels = labels
        
        if not HAS_TENSORFLOW:
            raise ImportError("TensorFlow es requerido para exportación")
        
        logger.info(f"ModelExporter inicializado con {len(labels)} clases")
    
    def export_savedmodel(self, output_dir: str) -> bool:
        """
        Exporta modelo a formato SavedModel
        
        Args:
            output_dir: Directorio de salida
            
        Returns:
            True si exportación exitosa
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Guardar como SavedModel
            self.model.save(output_dir)
            
            # Guardar etiquetas
            labels_path = os.path.join(output_dir, "labels.json")
            with open(labels_path, 'w') as f:
                json.dump(self.labels, f, indent=2)
            
            logger.info(f"Modelo exportado como SavedModel en {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando SavedModel: {e}")
            return False
    
    def export_tflite(self, output_path: str, quantize: bool = True) -> bool:
        """
        Exporta modelo a formato TensorFlow Lite
        
        Args:
            output_path: Ruta del archivo .tflite
            quantize: Si aplicar cuantización
            
        Returns:
            True si exportación exitosa
        """
        try:
            # Crear conversor
            converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
            
            # Optimizaciones
            if quantize:
                converter.optimizations = [tf.lite.Optimize.DEFAULT]
                # Para cuantización int8 necesitas dataset representativo
                # converter.representative_dataset = self.representative_dataset
            
            # Convertir modelo
            tflite_model = converter.convert()
            
            # Guardar modelo
            with open(output_path, 'wb') as f:
                f.write(tflite_model)
            
            # Guardar etiquetas
            labels_path = output_path.replace('.tflite', '_labels.json')
            with open(labels_path, 'w') as f:
                json.dump(self.labels, f, indent=2)
            
            size_mb = len(tflite_model) / (1024 * 1024)
            logger.info(f"Modelo TFLite guardado en {output_path} ({size_mb:.2f} MB)")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando TFLite: {e}")
            return False
    
    def export_h5(self, output_path: str) -> bool:
        """
        Exporta modelo a formato H5
        
        Args:
            output_path: Ruta del archivo .h5
            
        Returns:
            True si exportación exitosa
        """
        try:
            self.model.save(output_path)
            
            # Guardar etiquetas
            labels_path = output_path.replace('.h5', '_labels.json')
            with open(labels_path, 'w') as f:
                json.dump(self.labels, f, indent=2)
            
            logger.info(f"Modelo H5 guardado en {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando H5: {e}")
            return False
    
    def export_all_formats(self, base_dir: str = "deployment") -> Dict[str, bool]:
        """
        Exporta modelo en todos los formatos soportados
        
        Args:
            base_dir: Directorio base para exportación
            
        Returns:
            Diccionario con éxito de cada formato
        """
        os.makedirs(base_dir, exist_ok=True)
        
        results = {}
        
        # H5
        h5_path = os.path.join(base_dir, "model.h5")
        results['h5'] = self.export_h5(h5_path)
        
        # SavedModel
        savedmodel_dir = os.path.join(base_dir, "saved_model")
        results['savedmodel'] = self.export_savedmodel(savedmodel_dir)
        
        # TFLite
        tflite_path = os.path.join(base_dir, "model.tflite")
        results['tflite'] = self.export_tflite(tflite_path, quantize=True)
        
        logger.info(f"Exportación completada: {results}")
        return results


class DesktopRuntime:
    """Runtime de deployment para Desktop (Python)"""
    
    def __init__(self, model_path: str, labels_path: str):
        """
        Inicializa runtime desktop
        
        Args:
            model_path: Ruta del modelo (.h5 o SavedModel)
            labels_path: Ruta de etiquetas JSON
        """
        if not HAS_TENSORFLOW:
            raise ImportError("TensorFlow es requerido para Desktop Runtime")
        
        # Cargar modelo
        if model_path.endswith('.h5'):
            self.model = tf.keras.models.load_model(model_path)
        else:
            self.model = tf.saved_model.load(model_path)
        
        # Cargar etiquetas
        with open(labels_path, 'r') as f:
            self.labels = json.load(f)
        
        logger.info(f"DesktopRuntime inicializado con {len(self.labels)} clases")
    
    def preprocess(self, landmarks: np.ndarray) -> np.ndarray:
        """
        Preprocesamiento consistente con entrenamiento
        
        Args:
            landmarks: Array (21, 3) de landmarks
            
        Returns:
            Array (1, 21, 3) preprocesado
        """
        # Normalización de traducción
        centered = landmarks - landmarks[0]
        
        # Normalización de escala
        scale = np.linalg.norm(centered[9])
        if scale < 1e-6:
            scale = 1.0
        normalized = centered / scale
        
        return normalized.reshape(1, 21, 3).astype(np.float32)
    
    def predict(self, landmarks: np.ndarray) -> Tuple[str, float]:
        """
        Predicción minimal y rápida
        
        Args:
            landmarks: Array (21, 3) de landmarks
            
        Returns:
            Tuple (label, confidence)
        """
        x = self.preprocess(landmarks)
        probs = self.model(x, training=False).numpy()[0]
        
        idx = np.argmax(probs)
        confidence = probs[idx]
        
        if confidence < 0.6:
            return "unknown", confidence
        else:
            return self.labels[idx], confidence


class EdgeRuntime:
    """Runtime de deployment para Edge devices (TFLite)"""
    
    def __init__(self, model_path: str, labels_path: str):
        """
        Inicializa runtime edge
        
        Args:
            model_path: Ruta del modelo TFLite
            labels_path: Ruta de etiquetas JSON
        """
        if not HAS_TFLITE_RUNTIME:
            raise ImportError("TFLite Runtime es requerido para Edge Runtime")
        
        # Cargar intérprete TFLite
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        
        # Obtener detalles de entrada/salida
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        # Cargar etiquetas
        with open(labels_path, 'r') as f:
            self.labels = json.load(f)
        
        logger.info(f"EdgeRuntime inicializado con {len(self.labels)} clases")
        logger.info(f"Input shape: {self.input_details[0]['shape']}")
    
    def preprocess(self, landmarks: np.ndarray) -> np.ndarray:
        """
        Preprocesamiento para TFLite
        
        Args:
            landmarks: Array (21, 3) de landmarks
            
        Returns:
            Array preprocesado con shape correcto
        """
        # Normalización idéntica a Desktop
        centered = landmarks - landmarks[0]
        scale = np.linalg.norm(centered[9])
        if scale < 1e-6:
            scale = 1.0
        normalized = centered / scale
        
        # Ajustar shape según input del modelo
        input_shape = self.input_details[0]['shape']
        if len(input_shape) == 3:
            return normalized.reshape(1, 21, 3).astype(np.float32)
        else:
            return normalized.flatten().astype(np.float32)
    
    def predict(self, landmarks: np.ndarray) -> Tuple[str, float]:
        """
        Predicción con TFLite
        
        Args:
            landmarks: Array (21, 3) de landmarks
            
        Returns:
            Tuple (label, confidence)
        """
        x = self.preprocess(landmarks)
        
        # Setear tensor de entrada
        self.interpreter.set_tensor(self.input_details[0]['index'], x)
        
        # Invocar inferencia
        self.interpreter.invoke()
        
        # Obtener salida
        probs = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        
        idx = np.argmax(probs)
        confidence = probs[idx]
        
        if confidence < 0.6:
            return "unknown", confidence
        else:
            return self.labels[idx], confidence


class ArduinoBridge:
    """Puente de comunicación con Arduino"""
    
    def __init__(self, port: str = "COM3", baudrate: int = 9600):
        """
        Inicializa puente Arduino
        
        Args:
            port: Puerto serial
            baudrate: Velocidad de comunicación
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.connected = False
        
        # Mapeo de acciones para señas
        self.action_mapping = {
            "A": "gesture_A",
            "B": "gesture_B", 
            "C": "gesture_C",
            "D": "gesture_D",
            "E": "gesture_E",
            "F": "gesture_F",
            "G": "gesture_G",
            "H": "gesture_H",
            "I": "gesture_I",
            "unknown": "no_gesture"
        }
    
    def connect(self) -> bool:
        """
        Conecta al Arduino
        
        Returns:
            True si conexión exitosa
        """
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Esperar a que Arduino esté listo
            self.connected = True
            logger.info(f"Conectado a Arduino en {self.port}")
            return True
        except Exception as e:
            logger.error(f"Error conectando a Arduino: {e}")
            return False
    
    def disconnect(self):
        """Desconecta del Arduino"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.connected = False
            logger.info("Desconectado de Arduino")
    
    def send_prediction(self, label: str, confidence: float) -> bool:
        """
        Envía predicción al Arduino
        
        Args:
            label: Etiqueta predicha
            confidence: Confianza de la predicción
            
        Returns:
            True si envío exitoso
        """
        if not self.connected or not self.serial_conn:
            return False
        
        try:
            # Formato: "label:confidence\n"
            action = self.action_mapping.get(label, "no_gesture")
            message = f"{action}:{confidence:.2f}\n"
            
            self.serial_conn.write(message.encode())
            self.serial_conn.flush()
            
            logger.debug(f"Enviado a Arduino: {message.strip()}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando a Arduino: {e}")
            return False
    
    def send_command(self, command: str) -> bool:
        """
        Envía comando directo al Arduino
        
        Args:
            command: Comando a enviar
            
        Returns:
            True si envío exitoso
        """
        if not self.connected or not self.serial_conn:
            return False
        
        try:
            message = f"{command}\n"
            self.serial_conn.write(message.encode())
            self.serial_conn.flush()
            
            logger.debug(f"Comando enviado: {command}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando comando: {e}")
            return False


class UnifiedDeploymentPipeline:
    """Pipeline unificado de deployment para todas las plataformas"""
    
    def __init__(self, model_path: str, labels_path: str, 
                 platform: str = "desktop", arduino_port: Optional[str] = None):
        """
        Inicializa pipeline unificado
        
        Args:
            model_path: Ruta del modelo
            labels_path: Ruta de etiquetas
            platform: Plataforma ("desktop", "edge")
            arduino_port: Puerto Arduino (opcional)
        """
        self.platform = platform
        self.arduino_bridge = None
        
        # Inicializar runtime según plataforma
        if platform == "desktop":
            self.runtime = DesktopRuntime(model_path, labels_path)
        elif platform == "edge":
            self.runtime = EdgeRuntime(model_path, labels_path)
        else:
            raise ValueError(f"Plataforma no soportada: {platform}")
        
        # Inicializar puente Arduino si se especifica
        if arduino_port:
            self.arduino_bridge = ArduinoBridge(arduino_port)
            self.arduino_bridge.connect()
        
        logger.info(f"UnifiedDeploymentPipeline inicializado para {platform}")
    
    def predict_and_send(self, landmarks: np.ndarray) -> Tuple[str, float]:
        """
        Predice y envía a Arduino si está configurado
        
        Args:
            landmarks: Array (21, 3) de landmarks
            
        Returns:
            Tuple (label, confidence)
        """
        # Predicción
        label, confidence = self.runtime.predict(landmarks)
        
        # Enviar a Arduino si está conectado
        if self.arduino_bridge and self.arduino_bridge.connected:
            self.arduino_bridge.send_prediction(label, confidence)
        
        return label, confidence
    
    def cleanup(self):
        """Limpieza de recursos"""
        if self.arduino_bridge:
            self.arduino_bridge.disconnect()
        
        logger.info("Pipeline limpiado")


def create_arduino_sketch(output_path: str = "arduino_sign_recognition.ino"):
    """
    Crea sketch de Arduino para recibir predicciones
    
    Args:
        output_path: Ruta del archivo .ino
    """
    sketch_content = '''
/*
  Arduino Sign Language Recognition Receiver
  Recibe predicciones vía serial y ejecuta acciones
*/

// Pines para diferentes salidas
const int LED_A = 2;
const int LED_B = 3;
const int LED_C = 4;
const int LED_D = 5;
const int LED_E = 6;
const int LED_F = 7;
const int LED_G = 8;
const int LED_H = 9;
const int LED_I = 10;
const int LED_UNKNOWN = 11;

const int BUZZER = 12;

void setup() {
  Serial.begin(9600);
  
  // Configurar pines LED como salida
  for (int i = LED_A; i <= LED_UNKNOWN; i++) {
    pinMode(i, OUTPUT);
    digitalWrite(i, LOW);
  }
  
  pinMode(BUZZER, OUTPUT);
  digitalWrite(BUZZER, LOW);
  
  Serial.println("Arduino Sign Recognition Ready");
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\\n');
    input.trim();
    
    // Formato esperado: "gesture:confidence"
    int colonIndex = input.indexOf(':');
    if (colonIndex > 0) {
      String gesture = input.substring(0, colonIndex);
      float confidence = input.substring(colonIndex + 1).toFloat();
      
      // Ejecutar acción basada en gesto
      executeGesture(gesture, confidence);
    }
  }
}

void executeGesture(String gesture, float confidence) {
  // Apagar todos los LEDs primero
  for (int i = LED_A; i <= LED_UNKNOWN; i++) {
    digitalWrite(i, LOW);
  }
  
  // Mapear gestos a LEDs
  int ledPin = LED_UNKNOWN; // Default
  
  if (gesture == "gesture_A") ledPin = LED_A;
  else if (gesture == "gesture_B") ledPin = LED_B;
  else if (gesture == "gesture_C") ledPin = LED_C;
  else if (gesture == "gesture_D") ledPin = LED_D;
  else if (gesture == "gesture_E") ledPin = LED_E;
  else if (gesture == "gesture_F") ledPin = LED_F;
  else if (gesture == "gesture_G") ledPin = LED_G;
  else if (gesture == "gesture_H") ledPin = LED_H;
  else if (gesture == "gesture_I") ledPin = LED_I;
  else if (gesture == "no_gesture") ledPin = LED_UNKNOWN;
  
  // Activar LED correspondiente
  digitalWrite(ledPin, HIGH);
  
  // Sonido de confirmación si confianza alta
  if (confidence > 0.8) {
    tone(BUZZER, 1000, 100);  // 1kHz por 100ms
  }
  
  // Debug output
  Serial.print("Gesto: ");
  Serial.print(gesture);
  Serial.print(" (");
  Serial.print(confidence, 2);
  Serial.println(")");
}
'''
    
    with open(output_path, 'w') as f:
        f.write(sketch_content)
    
    logger.info(f"Sketch de Arduino guardado en {output_path}")


def main():
    """Función principal para demostración"""
    print("=== Sistema de Deployment Multiplataforma ===")
    print("Este sistema permite deployment en Desktop, Edge, Mobile y Arduino.")
    print()
    
    print("Componentes implementados:")
    print("✅ Exportación de modelos (SavedModel, TFLite, H5)")
    print("✅ Runtime Desktop (TensorFlow)")
    print("✅ Runtime Edge (TFLite)")
    print("✅ Puente Arduino (Serial)")
    print("✅ Pipeline unificado")
    print()
    
    print("Para deployment:")
    print("1. Exportar modelo: ModelExporter.export_all_formats()")
    print("2. Elegir runtime: DesktopRuntime() o EdgeRuntime()")
    print("3. O usar pipeline unificado: UnifiedDeploymentPipeline()")
    print("4. Para Arduino: ArduinoBridge + create_arduino_sketch()")
    print()
    
    print("Ejemplo Desktop:")
    print("runtime = DesktopRuntime('model.h5', 'labels.json')")
    print("label, conf = runtime.predict(landmarks)")
    print()
    
    print("Ejemplo Edge:")
    print("runtime = EdgeRuntime('model.tflite', 'labels.json')")
    print("label, conf = runtime.predict(landmarks)")
    print()
    
    print("Ejemplo con Arduino:")
    print("pipeline = UnifiedDeploymentPipeline('model.tflite', 'labels.json', 'edge', 'COM3')")
    print("label, conf = pipeline.predict_and_send(landmarks)")
    
    # Crear sketch de Arduino
    create_arduino_sketch()


if __name__ == "__main__":
    main()
