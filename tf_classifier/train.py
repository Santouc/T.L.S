#!/usr/bin/env python3
"""
Script de entrenamiento para modelo de reconocimiento de señas
Genera model.h5 y labels.json para el sistema de inferencia
"""

import json
import numpy as np
import tensorflow as tf
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_dataset(dataset_path: str = "dataset_final.json"):
    """
    Carga dataset desde archivo JSON
    
    Args:
        dataset_path: Ruta del dataset
        
    Returns:
        Tuple (X, y, labels)
    """
    try:
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        
        X = np.array(data["X"], dtype=np.float32)
        # Asegurar shape correcto: (N, 21, 3)
        if len(X.shape) == 4 and X.shape[1] == 1:
            X = X.squeeze(axis=1)  # Remover dimensión extra
        print(f"Shape después de cargar: {X.shape}")
        y = np.array(data["y"], dtype=np.int32)
        labels = data["labels"]
        
        logger.info(f"Dataset cargado: {X.shape[0]} muestras, {len(labels)} clases")
        return X, y, labels
        
    except Exception as e:
        logger.error(f"Error cargando dataset: {e}")
        raise

def preprocess_data(X: np.ndarray) -> np.ndarray:
    """
    Preprocesamiento consistente con inferencia
    
    Args:
        X: Array (N, 21, 3) de landmarks
        
    Returns:
        Array preprocesado
    """
    # Normalización de traducción (centrar en muñeca)
    X = X - X[:, 0:1, :]
    
    # Normalización de escala (relativo a hueso índice)
    scale = np.linalg.norm(X[:, 9:10, :], axis=2, keepdims=True)
    scale[scale < 1e-6] = 1.0
    X = X / scale
    
    return X

def create_model(num_classes: int) -> tf.keras.Model:
    """
    Crea modelo para entrenamiento
    
    Args:
        num_classes: Número de clases de salida
        
    Returns:
        Modelo TensorFlow
    """
    inputs = tf.keras.Input(shape=(21, 3))
    
    # Capas densas
    x = tf.keras.layers.Dense(64, activation='relu')(inputs)
    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dense(128, activation='relu')(x)
    
    # Capa de salida
    outputs = tf.keras.layers.Dense(num_classes, activation='softmax')(x)
    
    model = tf.keras.Model(inputs, outputs)
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

def train_model(X: np.ndarray, y: np.ndarray, labels: list):
    """
    Entrena el modelo y guarda artefactos
    
    Args:
        X: Datos de entrenamiento
        y: Etiquetas de entrenamiento
        labels: Lista de nombres de clases
    """
    logger.info("Iniciando entrenamiento del modelo...")
    
    # Crear modelo
    num_classes = len(labels)
    model = create_model(num_classes)
    
    # Entrenar
    history = model.fit(
        X, y,
        epochs=20,
        batch_size=32,
        validation_split=0.2,
        verbose=1
    )
    
    # Guardar modelo
    model_path = "tf_classifier/model.h5"
    model.save(model_path)
    logger.info(f"Modelo guardado en {model_path}")
    
    # Guardar etiquetas
    labels_path = "tf_classifier/labels.json"
    with open(labels_path, 'w') as f:
        json.dump(labels, f, indent=2)
    logger.info(f"Etiquetas guardadas en {labels_path}")
    
    # Mostrar resultados
    final_accuracy = history.history['accuracy'][-1]
    final_val_accuracy = history.history['val_accuracy'][-1]
    
    logger.info(f"Entrenamiento completado:")
    logger.info(f"  Accuracy final: {final_accuracy:.4f}")
    logger.info(f"  Val accuracy final: {final_val_accuracy:.4f}")
    
    return model, history

def main():
    """Función principal de entrenamiento"""
    try:
        # Cargar dataset
        X, y, labels = load_dataset()
        
        # Preprocesar datos
        X_processed = preprocess_data(X)
        print(f"Shape después de preprocesar: {X_processed.shape}")
        
        # Entrenar modelo
        model, history = train_model(X_processed, y, labels)
        
        print("✅ Model trained and saved successfully!")
        print(f"   Model: tf_classifier/model.h5")
        print(f"   Labels: tf_classifier/labels.json")
        print(f"   Classes: {labels}")
        
    except Exception as e:
        logger.error(f"Error en entrenamiento: {e}")
        print(f"Training failed: {e}")

if __name__ == "__main__":
    main()
