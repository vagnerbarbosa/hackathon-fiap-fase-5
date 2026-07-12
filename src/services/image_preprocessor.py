"""Pré-processamento de imagens para detecção YOLO.

Redimensiona, normaliza e prepara imagens para inferência.
Inclui validações rigorosas de segurança contra DoS.
"""

import logging
import mimetypes
from pathlib import Path
from typing import Union, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Constantes de segurança
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_IMAGE_DIMENSION = 10000  # Max 10k pixels
MIN_IMAGE_DIMENSION = 10     # Min 10 pixels
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/jpg'}


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

        image_path = Path(image_path)

        # Validações de segurança (prevenção contra DoS)
        self._validate_file_exists(image_path)
        self._validate_file_size(image_path)
        self._validate_mime_type(image_path)

        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Cannot load image (may be corrupted): {image_path}")

        # Valida dimensões após carregar
        self._validate_image_dimensions(img)

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

    def _validate_file_exists(self, image_path: Path) -> None:
        """Valida se arquivo existe.

        Args:
            image_path: Caminho para o arquivo.

        Raises:
            FileNotFoundError: Se arquivo não existe.
        """
        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            raise FileNotFoundError(f"Image not found: {image_path}")

    def _validate_file_size(self, image_path: Path) -> None:
        """Valida tamanho do arquivo (proteção contra DoS).

        Args:
            image_path: Caminho para o arquivo.

        Raises:
            ValueError: Se arquivo excede tamanho máximo.
        """
        size = image_path.stat().st_size
        if size > MAX_FILE_SIZE_BYTES:
            logger.error(
                f"File too large: {image_path} ({size} bytes). "
                f"Max: {MAX_FILE_SIZE_BYTES} bytes"
            )
            raise ValueError(
                f"File size exceeds maximum allowed ({MAX_FILE_SIZE_MB}MB). "
                f"Current: {size / 1024 / 1024:.2f}MB"
            )

    def _validate_mime_type(self, image_path: Path) -> None:
        """Valida MIME type do arquivo.

        Args:
            image_path: Caminho para o arquivo.

        Raises:
            ValueError: Se MIME type não é permitido.
        """
        mime_type, _ = mimetypes.guess_type(str(image_path))
        if mime_type not in ALLOWED_MIME_TYPES:
            logger.error(f"Invalid MIME type: {mime_type} for {image_path}")
            raise ValueError(
                f"Invalid file type: {mime_type}. "
                f"Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
            )

    def _validate_image_dimensions(self, img: np.ndarray) -> None:
        """Valida dimensões da imagem carregada.

        Args:
            img: Array numpy da imagem.

        Raises:
            ValueError: Se dimensões são inválidas.
        """
        if len(img.shape) < 2:
            raise ValueError("Invalid image: less than 2 dimensions")

        h, w = img.shape[:2]

        # Validações de dimensão
        if h < MIN_IMAGE_DIMENSION or w < MIN_IMAGE_DIMENSION:
            raise ValueError(
                f"Image too small: {w}x{h}. "
                f"Minimum: {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}"
            )

        if h > MAX_IMAGE_DIMENSION or w > MAX_IMAGE_DIMENSION:
            raise ValueError(
                f"Image too large: {w}x{h}. "
                f"Maximum: {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}"
            )

        # Valida número de canais (3 para RGB)
        if len(img.shape) == 3 and img.shape[2] not in [3, 4]:
            raise ValueError(
                f"Invalid number of channels: {img.shape[2]}. "
                f"Expected: 3 (RGB) or 4 (RGBA)"
            )

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
