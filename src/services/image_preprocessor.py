"""Image preprocessing for YOLO detection.

Redimensiona, normaliza e prepara imagens para inferência.
"""

import logging
from pathlib import Path
from typing import Union

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Pré-processa imagens para detecção de componentes YOLO.

    Executa as seguintes transformações:
    1. Carrega imagem do arquivo
    2. Converte para RGB
    3. Redimensiona para tamanho alvo (múltiplo de 32)
    4. Normaliza pixels (0-255 -> 0-1)
    5. Binarização opcional (threshold adaptativo)

    Usage:
        >>> preprocessor = ImagePreprocessor(target_size=640)
        >>> processed = preprocessor.preprocess("diagram.png")
        >>> # processed is numpy array ready for YOLO
    """

    def __init__(
        self,
        target_size: int = 640,
        normalize: bool = True,
        apply_threshold: bool = False,
    ):
        """Inicializa o pré-processador.

        Args:
            target_size: Tamanho alvo da imagem (múltiplo de 32 recomendado).
            normalize: Se deve normalizar pixels para faixa 0-1.
            apply_threshold: Se deve aplicar thresholding adaptativo.
        """
        self.target_size = target_size
        self.normalize = normalize
        self.apply_threshold = apply_threshold

    def preprocess(self, image_path: Union[str, Path]) -> np.ndarray:
        """Pré-processa arquivo de imagem para inferência YOLO.

        Args:
            image_path: Caminho para o arquivo de imagem (PNG, JPG, JPEG).

        Returns:
            np.ndarray: Array de imagem pré-processada (HWC, RGB, float32).

        Raises:
            FileNotFoundError: Se arquivo de imagem não existir.
            ValueError: Se imagem não puder ser carregada.
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Cannot load image: {image_path}")

        logger.debug(f"Loaded image: {image_path}, shape: {img.shape}")

        # Convert BGR (OpenCV default) to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Resize to target size
        img = self._resize(img)

        # Apply adaptive thresholding if enabled
        if self.apply_threshold:
            img = self._apply_threshold(img)

        # Normalize pixel values
        if self.normalize:
            img = img.astype(np.float32) / 255.0

        logger.debug(f"Preprocessed image shape: {img.shape}")
        return img

    def _resize(self, img: np.ndarray) -> np.ndarray:
        """Redimensiona imagem para tamanho alvo mantendo aspect ratio.

        Usa técnica letterbox para preencher se necessário.

        Args:
            img: Imagem de entrada (HWC).

        Returns:
            Imagem redimensionada.
        """
        h, w = img.shape[:2]

        # Calculate scale to fit within target_size
        scale = min(self.target_size / h, self.target_size / w)

        # Compute new dimensions
        new_h = int(h * scale)
        new_w = int(w * scale)

        # Resize
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Create letterbox (pad with gray)
        top = (self.target_size - new_h) // 2
        bottom = self.target_size - new_h - top
        left = (self.target_size - new_w) // 2
        right = self.target_size - new_w - left

        # Pad
        padded = cv2.copyMakeBorder(
            resized,
            top,
            bottom,
            left,
            right,
            cv2.BORDER_CONSTANT,
            value=(114, 114, 114),  # Gray padding
        )

        return padded

    def _apply_threshold(self, img: np.ndarray) -> np.ndarray:
        """Aplica thresholding adaptativo para melhoria de diagramas.

        Útil para diagramas com fundos variados.

        Args:
            img: Imagem de entrada (HWC, RGB).

        Returns:
            Imagem com threshold aplicado.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )

        # Convert back to RGB
        result = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)
        return result

    def get_original_size(self, image_path: Union[str, Path]) -> tuple:
        """Obtém dimensões originais da imagem sem carregar imagem completa.

        Args:
            image_path: Caminho para o arquivo de imagem.

        Returns:
            Tupla de (altura, largura).
        """
        image_path = Path(image_path)
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Cannot load image: {image_path}")
        return img.shape[:2]
