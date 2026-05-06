#!/usr/bin/env python3
"""
Traductor de Lenguaje de Señas Chileno
Archivo principal que orquesta el sistema completo
"""

import cv2
import numpy as np
import time
import threading
from collections import deque

# Importar módulos personalizados
from opencv import ImageProcessor
from hand_detection.landmarks import HandDetector
from utils.config import Config
from utils.logger import Logger

# Importar el clasificador híbrido real
from tf_classifier.clasificador import SignClassifier

class SignLanguageTranslator:
    """Clase principal que coordina todos los componentes del sistema"""
    
    def __init__(self):
        # Configuración inicial
        self.config = Config()
        self.logger = Logger()
        
        # Inicializar componentes
        self.hand_detector = HandDetector()
        self.image_processor = ImageProcessor()
        self.sign_classifier = SignClassifier(
            model_path="tf_classifier/model.h5",
            labels_path="tf_classifier/labels.json"
        )
        
        # Variables de estado
        self.running = False
        self.current_sign = None
        self.sign_buffer = deque(maxlen=10)  # Buffer para estabilizar detección
        self.confidence_threshold = 0.7
        
        self.logger.info("Sistema de traducción inicializado")
    
    def process_frame(self, frame):
        """Procesa un frame individual y devuelve el resultado"""
        try:
            # 1. Procesamiento de imagen con OpenCV
            processed_frame = self.image_processor.preprocess(frame)
            
            # 2. Detección de landmarks con MediaPipe
            landmarks = self.hand_detector.detect(processed_frame)
            
            if landmarks is not None:
                # 3. Dibujar landmarks en el frame
                processed_frame = self.hand_detector.draw_landmarks(processed_frame, landmarks)
                
                # 4. Clasificación con TensorFlow
                sign, confidence = self.sign_classifier.classify(landmarks)
                
                # 5. Aplicar buffer para estabilidad
                self.sign_buffer.append((sign, confidence))
                
                # 6. Determinar sign final basado en consenso
                if len(self.sign_buffer) >= 5:
                    final_sign = self._get_consensus_sign()
                    return processed_frame, final_sign
            
            return processed_frame, None
            
        except Exception as e:
            self.logger.error(f"Error procesando frame: {e}")
            return frame, None
    
    def _get_consensus_sign(self):
        """Determina el signo con mayor consenso en el buffer"""
        signs = [item[0] for item in self.sign_buffer if item[1] > self.confidence_threshold]
        if not signs:
            return None
        
        # Contar frecuencia y devolver el más común
        from collections import Counter
        most_common = Counter(signs).most_common(1)[0][0]
        return most_common
    
    def run(self):
        """Bucle principal del sistema"""
        self.logger.info("Iniciando sistema de traducción...")
        self.running = True
        
        # Inicializar cámara
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15)
        
        if not cap.isOpened():
            self.logger.error("No se pudo abrir la cámara")
            return
        
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    continue
                
                # Procesar frame
                processed_frame, detected_sign = self.process_frame(frame)
                
                # Mostrar resultados
                self._display_results(processed_frame, detected_sign)
                
                # Salir con 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        except KeyboardInterrupt:
            self.logger.info("Interrupción del usuario")
        
        finally:
            self.cleanup(cap)
    
    def _display_results(self, frame, sign):
        """Muestra los resultados en la ventana"""
        # Espejar imagen para mejor experiencia
        display_frame = cv2.flip(frame, 1)
        
        # Mostrar signo detectado
        if sign:
            cv2.putText(display_frame, f"Signo: {sign}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(display_frame, "Signo: None", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Mostrar FPS
        fps_text = f"FPS: {self._calculate_fps():.1f}"
        cv2.putText(display_frame, fps_text, (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Mostrar controles
        cv2.putText(display_frame, "Presiona 'q' para salir", (10, display_frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.imshow('Traductor de Lenguaje de Señas', display_frame)
    
    def _calculate_fps(self):
        """Calcula los FPS actuales"""
        if not hasattr(self, 'last_time'):
            self.last_time = time.time()
            self.frame_count = 0
            self.fps = 0
        
        self.frame_count += 1
        current_time = time.time()
        
        if current_time - self.last_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_time)
            self.last_time = current_time
            self.frame_count = 0
        
        return self.fps
    
    def cleanup(self, cap):
        """Limpia recursos al finalizar"""
        self.running = False
        cap.release()
        cv2.destroyAllWindows()
        self.logger.info("Sistema finalizado")

def main():
    """Función principal de entrada"""
    translator = SignLanguageTranslator()
    translator.run()

if __name__ == "__main__":
    main()
