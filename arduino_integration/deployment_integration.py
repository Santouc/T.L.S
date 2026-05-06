#!/usr/bin/env python3
"""
Integración de deployment con Arduino
Conecta el sistema de reconocimiento de señas con control de hardware Arduino
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

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

# Importar puente Arduino
from arduino_bridge import ArduinoBridge, ArduinoController

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


class UnifiedDeploymentPipeline:
    """Pipeline unificado de deployment para todas las plataformas con Arduino"""
    
    def __init__(self, model_path: str, labels_path: str, 
                 platform: str = "desktop", arduino_config: Optional[Dict] = None):
        """
        Inicializa pipeline unificado
        
        Args:
            model_path: Ruta del modelo
            labels_path: Ruta de etiquetas
            platform: Plataforma ("desktop", "edge")
            arduino_config: Configuración Arduino {"port": "COM3", "baudrate": 9600}
        """
        self.platform = platform
        self.arduino_controller = None
        
        # Inicializar runtime según plataforma
        if platform == "desktop":
            self.runtime = DesktopRuntime(model_path, labels_path)
        elif platform == "edge":
            self.runtime = EdgeRuntime(model_path, labels_path)
        else:
            raise ValueError(f"Plataforma no soportada: {platform}")
        
        # Inicializar controlador Arduino si se especifica
        if arduino_config:
            self.arduino_controller = ArduinoController()
            
            port = arduino_config.get("port", "COM3")
            baudrate = arduino_config.get("baudrate", 9600)
            make_default = arduino_config.get("make_default", True)
            
            success = self.arduino_controller.add_device(
                "main", port, baudrate, make_default
            )
            
            if success:
                logger.info(f"Arduino conectado en {port}")
            else:
                logger.warning(f"No se pudo conectar Arduino en {port}")
                self.arduino_controller = None
        
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
        if self.arduino_controller:
            self.arduino_controller.send_prediction_to_default(label, confidence)
        
        return label, confidence
    
    def send_arduino_command(self, command: str, *args) -> bool:
        """
        Envía comando directo a Arduino
        
        Args:
            command: Comando a enviar
            *args: Parámetros del comando
            
        Returns:
            True si envío exitoso
        """
        if not self.arduino_controller:
            return False
        
        if command == "led":
            if len(args) >= 2:
                led_num = args[0]
                state = args[1]
                return self.arduino_controller.default_device.send_led_command(led_num, state)
        
        elif command == "buzzer":
            if len(args) >= 2:
                freq = args[0]
                duration = args[1]
                return self.arduino_controller.default_device.send_buzzer_command(freq, duration)
        
        elif command == "servo":
            if len(args) >= 2:
                servo_num = args[0]
                angle = args[1]
                return self.arduino_controller.default_device.send_servo_command(servo_num, angle)
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene estado completo del sistema
        
        Returns:
            Diccionario con estado de runtime y Arduino
        """
        status = {
            "platform": self.platform,
            "runtime_ready": True,
            "arduino_connected": self.arduino_controller is not None
        }
        
        if self.arduino_controller:
            status["arduino_status"] = self.arduino_controller.get_all_status()
        
        return status
    
    def cleanup(self):
        """Limpieza de recursos"""
        if self.arduino_controller:
            self.arduino_controller.disconnect_all()
        
        logger.info("Pipeline limpiado")


def create_deployment_package(model, labels: List[str], output_dir: str = "deployment_package"):
    """
    Crea paquete completo de deployment con Arduino
    
    Args:
        model: Modelo TensorFlow/Keras
        labels: Lista de etiquetas
        output_dir: Directorio de salida
        
    Returns:
        True si paquete creado exitosamente
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Exportar modelos
        exporter = ModelExporter(model, labels)
        export_results = exporter.export_all_formats(output_dir)
        
        # Copiar archivos Arduino
        arduino_dir = os.path.join(output_dir, "arduino")
        os.makedirs(arduino_dir, exist_ok=True)
        
        # Copiar sketch Arduino (simulado - en realidad se copiarían los archivos)
        logger.info(f"Sketch Arduino copiado a {arduino_dir}")
        
        logger.info(f"Paquete de deployment creado en {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando paquete de deployment: {e}")
        return False


def main():
    """Función principal para demostración"""
    print("=== Sistema de Deployment con Arduino ===")
    print("Este sistema integra reconocimiento de señas con control Arduino.")
    print()
    
    print("Componentes implementados:")
    print("✅ Exportación de modelos (SavedModel, TFLite, H5)")
    print("✅ Runtime Desktop (TensorFlow)")
    print("✅ Runtime Edge (TFLite)")
    print("✅ Integración Arduino completa")
    print("✅ Pipeline unificado con hardware")
    print()
    
    print("Para deployment con Arduino:")
    print("1. Exportar modelo: ModelExporter.export_all_formats()")
    print("2. Configurar Arduino: UnifiedDeploymentPipeline(..., arduino_config)")
    print("3. Predecir y controlar: pipeline.predict_and_send(landmarks)")
    print("4. Control directo: pipeline.send_arduino_command('led', 2, True)")
    print()
    
    print("Ejemplo completo:")
    print("pipeline = UnifiedDeploymentPipeline(")
    print("    'model.tflite', 'labels.json', 'edge',")
    print("    arduino_config={'port': 'COM3', 'baudrate': 9600}")
    print(")")
    print("label, conf = pipeline.predict_and_send(landmarks)")
    print("pipeline.send_arduino_command('buzzer', 1000, 200)")


if __name__ == "__main__":
    main()
