#!/usr/bin/env python3
"""Script para download do dataset do HuggingFace.

Este script baixa o dataset de arquitetura de software do HuggingFace
quando ele não está presente localmente.

Usage:
    python scripts/download_dataset.py
    python scripts/download_dataset.py --force  # Força re-download

Requirements:
    pip install huggingface_hub tqdm

Environment Variables:
    HF_TOKEN: HuggingFace API token (opcional, para datasets privados)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Diretório raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_ROOT / "dataset"

# Configuração do dataset no HuggingFace
# TODO: Atualizar com o nome correto do dataset no HuggingFace
HF_DATASET_NAME = "fiap-grupo27/architecture-diagrams-stride"  # Exemplo, ajustar conforme necessário
HF_SUBSET = None  # Subset específico, se houver


def check_dataset_exists() -> bool:
    """Verifica se o dataset já existe localmente.

    Returns:
        bool: True se as pastas de imagens existirem e tiverem conteúdo.
    """
    required_dirs = [
        DATASET_DIR / "train" / "images",
        DATASET_DIR / "val" / "images",
        DATASET_DIR / "test" / "images",
    ]

    for dir_path in required_dirs:
        if not dir_path.exists():
            return False
        # Verifica se tem pelo menos uma imagem
        if not any(dir_path.iterdir()):
            return False

    # Verifica se o data.yaml existe
    if not (DATASET_DIR / "data.yaml").exists():
        return False

    return True


def download_from_huggingface(force: bool = False) -> None:
    """Baixa o dataset do HuggingFace.

    Args:
        force: Se True, força o re-download mesmo se o dataset existir.
    """
    try:
        from huggingface_hub import snapshot_download
        from huggingface_hub.utils import RepositoryNotFoundError
    except ImportError:
        print("❌ Erro: huggingface_hub não está instalado.")
        print("   Instale com: pip install huggingface_hub tqdm")
        sys.exit(1)

    if not force and check_dataset_exists():
        print("✅ Dataset já existe localmente.")
        print("   Use --force para re-download.")
        return

    print(f"📥 Baixando dataset do HuggingFace: {HF_DATASET_NAME}")
    print(f"   Destino: {DATASET_DIR}")

    try:
        # Cria o diretório do dataset se não existir
        DATASET_DIR.mkdir(parents=True, exist_ok=True)

        # Download do dataset
        token = os.getenv("HF_TOKEN")
        downloaded_path = snapshot_download(
            repo_id=HF_DATASET_NAME,
            repo_type="dataset",
            local_dir=str(DATASET_DIR),
            token=token,
            resume_download=True,
        )

        print(f"✅ Download concluído: {downloaded_path}")

        # Verifica integridade
        if check_dataset_exists():
            print("✅ Dataset verificado com sucesso!")
        else:
            print("⚠️  Aviso: Dataset baixado mas estrutura inesperada.")
            print("   Verifique o diretório:", DATASET_DIR)

    except RepositoryNotFoundError:
        print(f"❌ Erro: Dataset '{HF_DATASET_NAME}' não encontrado no HuggingFace.")
        print("   Verifique se o nome está correto em HF_DATASET_NAME.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro durante o download: {e}")
        sys.exit(1)


def download_via_git() -> None:
    """Alternativa: Download via git clone do HuggingFace."""
    import subprocess

    git_url = f"https://huggingface.co/datasets/{HF_DATASET_NAME}"
    print(f"📥 Clonando dataset via Git: {git_url}")

    try:
        # Remove diretório existente se houver
        if DATASET_DIR.exists():
            import shutil

            shutil.rmtree(DATASET_DIR)

        # Clone do repo
        result = subprocess.run(
            ["git", "clone", "--depth", "1", git_url, str(DATASET_DIR)],
            capture_output=True,
            text=True,
            check=True,
        )

        print(f"✅ Clone concluído: {DATASET_DIR}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao clonar: {e}")
        print(f"   stderr: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Erro: comando 'git' não encontrado.")
        sys.exit(1)


def main() -> int:
    """Entry point do script."""
    parser = argparse.ArgumentParser(
        description="Download do dataset de arquitetura de software.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Força o re-download mesmo se o dataset existir.",
    )
    parser.add_argument(
        "--git",
        action="store_true",
        help="Usa git clone em vez do huggingface_hub.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Apenas verifica se o dataset existe, sem download.",
    )

    args = parser.parse_args()

    if args.check:
        if check_dataset_exists():
            print("✅ Dataset existe localmente.")
            return 0
        else:
            print("❌ Dataset não encontrado localmente.")
            return 1

    if args.git:
        download_via_git()
    else:
        download_from_huggingface(force=args.force)

    return 0


if __name__ == "__main__":
    sys.exit(main())
