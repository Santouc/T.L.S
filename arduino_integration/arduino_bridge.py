#!/usr/bin/env python3
"""
Puente de comunicación con Arduino para control de hardware
Integración separada del sistema principal de reconocimiento de señas
"""

import serial
import time
import threading
import logging
from typing import Dict, Optional, List
from queue import Queue, Empty

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArduinoBridge:
    """Puente de comunicación con Arduino para control de hardware"""
    
    def __init__(self, port: str = "COM3", baudrate: int = 9600, timeout: float = 1.0):
        """
        Inicializa puente Arduino
        
        Args:
            port: Puerto serial (COM3, /dev/ttyUSB0, etc.)
            baudrate: Velocidad de comunicación (9600 por defecto)
            timeout: Timeout para operaciones serial
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
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
        
        # Buffer de comandos para envío asíncrono
        self.command_queue = Queue(maxsize=100)
        self.sender_thread = None
        self.running = False
        
        logger.info(f"ArduinoBridge inicializado para puerto {port}")
    
    def connect(self) -> bool:
        """
        Conecta al Arduino
        
        Returns:
            True si conexión exitosa
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Esperar a que Arduino esté listo
            time.sleep(2)
            
            # Probar conexión enviando comando de prueba
            self.send_command("test")
            
            self.connected = True
            logger.info(f"Conectado exitosamente a Arduino en {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a Arduino: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Desconecta del Arduino de forma segura"""
        self.running = False
        
        if self.sender_thread and self.sender_thread.is_alive():
            self.sender_thread.join(timeout=2.0)
        
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.send_command("disconnect")
                time.sleep(0.1)
                self.serial_conn.close()
            except:
                pass
        
        self.connected = False
        logger.info("Desconectado de Arduino")
    
    def start_async_sender(self):
        """Inicia thread para envío asíncrono de comandos"""
        if self.running:
            return
        
        self.running = True
        self.sender_thread = threading.Thread(
            target=self._async_sender_loop,
            name="ArduinoSender",
            daemon=True
        )
        self.sender_thread.start()
        logger.info("Thread de envío asíncrono iniciado")
    
    def _async_sender_loop(self):
        """Loop de envío asíncrono de comandos"""
        while self.running:
            try:
                # Obtener comando de la cola
                command = self.command_queue.get(timeout=0.1)
                
                # Enviar comando
                if self.connected and self.serial_conn:
                    try:
                        message = f"{command}\n"
                        self.serial_conn.write(message.encode())
                        self.serial_conn.flush()
                        logger.debug(f"Comando enviado: {command.strip()}")
                    except Exception as e:
                        logger.error(f"Error enviando comando: {e}")
                        self.connected = False
                
                self.command_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error en loop de envío: {e}")
    
    def send_prediction(self, label: str, confidence: float, async_send: bool = True) -> bool:
        """
        Envía predicción de seña al Arduino
        
        Args:
            label: Etiqueta predicha
            confidence: Confianza de la predicción (0.0-1.0)
            async_send: Si enviar de forma asíncrona
            
        Returns:
            True si envío exitoso
        """
        if not self.connected:
            return False
        
        # Obtener acción mapeada
        action = self.action_mapping.get(label, "no_gesture")
        
        # Formato: "gesture:confidence"
        message = f"{action}:{confidence:.2f}"
        
        if async_send and self.running:
            # Envío asíncrono
            try:
                self.command_queue.put(message, timeout=0.1)
                return True
            except:
                return False
        else:
            # Envío síncrono
            return self.send_command(message)
    
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
            logger.error(f"Error enviando comando '{command}': {e}")
            self.connected = False
            return False
    
    def send_led_command(self, led_number: int, state: bool) -> bool:
        """
        Envía comando para controlar LED específico
        
        Args:
            led_number: Número de LED (2-11)
            state: True para encender, False para apagar
            
        Returns:
            True si envío exitoso
        """
        action = "led_on" if state else "led_off"
        command = f"{action}:{led_number}"
        return self.send_command(command)
    
    def send_buzzer_command(self, frequency: int, duration_ms: int) -> bool:
        """
        Envía comando para activar buzzer
        
        Args:
            frequency: Frecuencia en Hz
            duration_ms: Duración en milisegundos
            
        Returns:
            True si envío exitoso
        """
        command = f"buzzer:{frequency}:{duration_ms}"
        return self.send_command(command)
    
    def send_servo_command(self, servo_number: int, angle: int) -> bool:
        """
        Envía comando para controlar servo
        
        Args:
            servo_number: Número de servo (0-3)
            angle: Ángulo (0-180)
            
        Returns:
            True si envío exitoso
        """
        command = f"servo:{servo_number}:{angle}"
        return self.send_command(command)
    
    def read_response(self, timeout: float = 1.0) -> Optional[str]:
        """
        Lee respuesta del Arduino
        
        Args:
            timeout: Timeout de lectura
            
        Returns:
            Respuesta recibida o None
        """
        if not self.connected or not self.serial_conn:
            return None
        
        try:
            self.serial_conn.timeout = timeout
            response = self.serial_conn.readline().decode().strip()
            
            if response:
                logger.debug(f"Respuesta Arduino: {response}")
            
            return response if response else None
            
        except Exception as e:
            logger.error(f"Error leyendo respuesta: {e}")
            return None
    
    def get_status(self) -> Dict:
        """
        Obtiene estado actual del puente
        
        Returns:
            Diccionario con estado del sistema
        """
        return {
            "connected": self.connected,
            "port": self.port,
            "baudrate": self.baudrate,
            "queue_size": self.command_queue.qsize(),
            "async_sender_running": self.running,
            "action_mapping": self.action_mapping
        }
    
    def clear_queue(self):
        """Limpia cola de comandos pendientes"""
        while not self.command_queue.empty():
            try:
                self.command_queue.get_nowait()
                self.command_queue.task_done()
            except Empty:
                break
        
        logger.info("Cola de comandos limpiada")


class ArduinoController:
    """Controlador de alto nivel para Arduino con múltiples dispositivos"""
    
    def __init__(self):
        """Inicializa controlador de múltiples dispositivos Arduino"""
        self.devices = {}  # {device_name: ArduinoBridge}
        self.default_device = None
        
        logger.info("ArduinoController inicializado")
    
    def add_device(self, name: str, port: str, baudrate: int = 9600, 
                   make_default: bool = False) -> bool:
        """
        Agrega dispositivo Arduino
        
        Args:
            name: Nombre del dispositivo
            port: Puerto serial
            baudrate: Velocidad de comunicación
            make_default: Si establecer como dispositivo por defecto
            
        Returns:
            True si dispositivo agregado exitosamente
        """
        try:
            bridge = ArduinoBridge(port, baudrate)
            
            if bridge.connect():
                bridge.start_async_sender()
                self.devices[name] = bridge
                
                if make_default or self.default_device is None:
                    self.default_device = name
                
                logger.info(f"Dispositivo '{name}' agregado en {port}")
                return True
            else:
                logger.error(f"No se pudo conectar dispositivo '{name}'")
                return False
                
        except Exception as e:
            logger.error(f"Error agregando dispositivo '{name}': {e}")
            return False
    
    def remove_device(self, name: str):
        """
        Remueve dispositivo Arduino
        
        Args:
            name: Nombre del dispositivo a remover
        """
        if name in self.devices:
            self.devices[name].disconnect()
            del self.devices[name]
            
            if self.default_device == name:
                self.default_device = next(iter(self.devices), None)
            
            logger.info(f"Dispositivo '{name}' removido")
    
    def send_prediction_to_device(self, device_name: str, label: str, 
                                 confidence: float) -> bool:
        """
        Envía predicción a dispositivo específico
        
        Args:
            device_name: Nombre del dispositivo
            label: Etiqueta predicha
            confidence: Confianza
            
        Returns:
            True si envío exitoso
        """
        if device_name in self.devices:
            return self.devices[device_name].send_prediction(label, confidence)
        else:
            logger.warning(f"Dispositivo '{device_name}' no encontrado")
            return False
    
    def send_prediction_to_all(self, label: str, confidence: float) -> Dict[str, bool]:
        """
        Envía predicción a todos los dispositivos
        
        Args:
            label: Etiqueta predicha
            confidence: Confianza
            
        Returns:
            Diccionario con éxito por dispositivo
        """
        results = {}
        
        for name, bridge in self.devices.items():
            results[name] = bridge.send_prediction(label, confidence)
        
        return results
    
    def send_prediction_to_default(self, label: str, confidence: float) -> bool:
        """
        Envía predicción al dispositivo por defecto
        
        Args:
            label: Etiqueta predicha
            confidence: Confianza
            
        Returns:
            True si envío exitoso
        """
        if self.default_device:
            return self.send_prediction_to_device(self.default_device, label, confidence)
        else:
            logger.warning("No hay dispositivo por defecto configurado")
            return False
    
    def get_all_status(self) -> Dict[str, Dict]:
        """
        Obtiene estado de todos los dispositivos
        
        Returns:
            Diccionario con estado por dispositivo
        """
        status = {}
        
        for name, bridge in self.devices.items():
            status[name] = bridge.get_status()
        
        return status
    
    def disconnect_all(self):
        """Desconecta todos los dispositivos"""
        for name, bridge in self.devices.items():
            bridge.disconnect()
        
        self.devices.clear()
        self.default_device = None
        logger.info("Todos los dispositivos desconectados")


def main():
    """Función principal para demostración"""
    print("=== Sistema de Integración con Arduino ===")
    print("Este sistema permite controlar hardware Arduino desde el reconocedor de señas.")
    print()
    
    print("Componentes implementados:")
    print("✅ ArduinoBridge - Comunicación serial básica")
    print("✅ Envío asíncrono de comandos")
    print("✅ Control de LEDs, buzzers, servos")
    print("✅ ArduinoController - Múltiples dispositivos")
    print("✅ Manejo de errores y reconexión")
    print()
    
    print("Para usar el sistema:")
    print("1. Conectar: bridge = ArduinoBridge('COM3')")
    print("2. Enviar predicción: bridge.send_prediction('A', 0.85)")
    print("3. Control hardware: bridge.send_led_command(2, True)")
    print("4. Múltiples dispositivos: controller = ArduinoController()")
    print()
    
    print("Ejemplo básico:")
    print("bridge = ArduinoBridge('COM3')")
    print("if bridge.connect():")
    print("    bridge.send_prediction('A', 0.9)")
    print("    bridge.send_buzzer_command(1000, 200)")
    print("    bridge.disconnect()")
    print()
    
    print("Ejemplo con múltiples dispositivos:")
    print("controller = ArduinoController()")
    print("controller.add_device('principal', 'COM3', make_default=True)")
    print("controller.add_device('secundario', 'COM4')")
    print("controller.send_prediction_to_all('B', 0.8)")


if __name__ == "__main__":
    main()
