#!/usr/bin/env python3
"""
Módulo centralizado de preprocesamiento de landmarks
Normalización de traducción y escala consistente en todo el sistema
"""

import numpy as np
from typing import Union, List, Tuple


def normalize_landmarks(landmarks: Union[np.ndarray, List[List[Tuple[float, float, float]]]]) -> np.ndarray:
    """
    Normalización de landmarks de manos (traducción + escala)
    
    Este método implementa el preprocesamiento estándar usado en todo el sistema:
    - Normalización de traducción (centrar en muñeca - landmark 0)
    - Normalización de escala (relativa a longitud del hueso índice)
    
    Args:
        landmarks: Array de landmarks shape (N, 21, 3) o lista de manos [[(x,y,z), ...], ...]
        
    Returns:
        Array normalizado shape (N, 21, 3) o (1, 21, 3) si es una sola mano
        
    Examples:
        >>> landmarks = np.random.rand(100, 21, 3)
        >>> normalized = normalize_landmarks(landmarks)
        >>> print(normalized.shape)
        (100, 21, 3)
        
        >>> single_hand = [[(0.5, 0.5, 0.0) for _ in range(21)]]
        >>> normalized = normalize_landmarks(single_hand)
        >>> print(normalized.shape)
        (1, 21, 3)
    """
    # Convertir a array numpy si es lista
    if isinstance(landmarks, list):
        if len(landmarks) == 0:
            return np.zeros((1, 21, 3), dtype=np.float32)
        
        # Si es lista de manos, tomar solo la primera
        hand = landmarks[0]
        if isinstance(hand, list) and len(hand) == 21:
            landmarks = np.array([hand], dtype=np.float32)
        else:
            landmarks = np.array(landmarks, dtype=np.float32)
    
    # Validar shape
    if len(landmarks.shape) == 2:
        landmarks = np.expand_dims(landmarks, axis=0)
    
    if landmarks.shape[1] != 21 or landmarks.shape[2] != 3:
        raise ValueError(f"Shape inválido: {landmarks.shape}, esperado (N, 21, 3)")
    
    X = landmarks.copy().astype(np.float32)
    
    # ====================
    # NORMALIZACIÓN DE TRADUCCIÓN
    # ====================
    # Centrar en la muñeca (landmark 0)
    X = X - X[:, 0:1, :]
    
    # ====================
    # NORMALIZACIÓN DE ESCALA
    # ====================
    # Usar longitud del hueso medio del dedo índice como referencia
    # landmarks[5] = MCP del índice, landmarks[6] = PIP del índice
    scale = np.linalg.norm(X[:, 9:10, :], axis=2, keepdims=True)
    
    # Evitar división por cero
    scale[scale < 1e-6] = 1.0
    
    # Normalizar por escala
    X = X / scale
    
    return X


def normalize_single_hand(landmarks: List[Tuple[float, float, float]]) -> np.ndarray:
    """
    Normalización para una sola mano (21 landmarks)
    
    Args:
        landmarks: Lista de 21 tuplas (x, y, z)
        
    Returns:
        Array normalizado shape (1, 21, 3)
    """
    return normalize_landmarks([landmarks])


def normalize_batch(landmarks: np.ndarray) -> np.ndarray:
    """
    Normalización para batch de manos (N manos)
    
    Args:
        landmarks: Array shape (N, 21, 3)
        
    Returns:
        Array normalizado shape (N, 21, 3)
    """
    return normalize_landmarks(landmarks)


def preprocess_for_inference(landmarks: List[List[Tuple[float, float, float]]]) -> np.ndarray:
    """
    Preprocesamiento específico para inferencia en tiempo real
    Retorna shape (1, 21, 3) para compatibilidad con TensorFlow
    
    Args:
        landmarks: Lista de manos detectadas [[(x,y,z), ...], ...]
        
    Returns:
        Array preprocesado shape (1, 21, 3)
    """
    if not landmarks or len(landmarks) == 0:
        return np.zeros((1, 21, 3), dtype=np.float32)
    
    # Tomar solo la primera mano
    hand = landmarks[0]
    
    if len(hand) != 21:
        return np.zeros((1, 21, 3), dtype=np.float32)
    
    # Normalizar
    normalized = normalize_landmarks([hand])
    
    return normalized


def preprocess_for_training(landmarks: np.ndarray) -> np.ndarray:
    """
    Preprocesamiento específico para entrenamiento
    Retorna shape (N, 21, 3) para batch de entrenamiento
    
    Args:
        landmarks: Array shape (N, 21, 3)
        
    Returns:
        Array preprocesado shape (N, 21, 3)
    """
    return normalize_landmarks(landmarks)


if __name__ == "__main__":
    # Prueba básica
    print("=== Prueba de Preprocesamiento ===")
    
    # Generar datos de prueba
    test_landmarks = np.random.rand(10, 21, 3)
    print(f"Input shape: {test_landmarks.shape}")
    
    # Normalizar
    normalized = normalize_landmarks(test_landmarks)
    print(f"Output shape: {normalized.shape}")
    print(f"Output dtype: {normalized.dtype}")
    print(f"Output range: [{normalized.min():.3f}, {normalized.max():.3f}]")
    
    # Prueba con lista
    single_hand = [[(0.5 + i*0.01, 0.5 + i*0.01, 0.0) for i in range(21)]]
    normalized_single = normalize_landmarks(single_hand)
    print(f"\nSingle hand input shape: (1, 21, 3)")
    print(f"Single hand output shape: {normalized_single.shape}")
    
    print("\n✅ Prueba completada exitosamente")
